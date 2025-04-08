import os
import git
from git import Repo
from typing import List, Dict, Tuple
import logging
from datetime import datetime

def setup_logging(log_file: str = 'git_chunks.log') -> None:
    """Setup logging configuration with both file and console output"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w'),
            logging.StreamHandler()
        ]
    )

def get_project_directory() -> str:
    """Prompt user for project directory path with validation"""
    while True:
        path = input("Enter the project directory path: ").strip()
        if os.path.isdir(path):
            if os.path.isdir(os.path.join(path, '.git')):
                return os.path.abspath(path)
            print("The directory doesn't appear to be a git repository.")
        else:
            print("Invalid directory path. Please try again.")

def get_untracked_files(repo: Repo) -> List[str]:
    """Get list of untracked files with relative paths"""
    return [os.path.normpath(item) for item in repo.untracked_files]

def safe_get_file_size(file_path: str) -> Tuple[int, bool]:
    """
    Safely get file size with multiple fallback methods
    
    Returns:
        Tuple of (size in bytes, success status)
    """
    try:
        # First try standard method
        return os.path.getsize(file_path), True
    except (OSError, PermissionError):
        try:
            # Fallback method for Windows
            if os.name == 'nt':
                import win32file
                handle = win32file.CreateFile(
                    file_path,
                    win32file.GENERIC_READ,
                    win32file.FILE_SHARE_READ,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None
                )
                size = win32file.GetFileSize(handle)
                win32file.CloseHandle(handle)
                return size, True
        except:
            pass
        
        # Final fallback - try to read the file
        try:
            with open(file_path, 'rb') as f:
                size = len(f.read())
                return size, True
        except:
            return 0, False

def calculate_chunks(untracked_files: List[str], repo_path: str, max_chunk_size: int = 25 * 1024 * 1024) -> Tuple[List[List[str]], Dict[str, int]]:
    """
    Calculate chunks with improved error handling and progress reporting
    
    Args:
        untracked_files: List of relative file paths
        repo_path: Absolute path to repository root
        max_chunk_size: Maximum chunk size in bytes
    
    Returns:
        Tuple of (list of file chunks, statistics dictionary)
    """
    chunks = []
    current_chunk = []
    current_chunk_size = 0
    stats = {
        'total_files': len(untracked_files),
        'processed_files': 0,
        'successful_files': 0,
        'failed_files': 0,
        'large_files': 0,
        'total_chunks': 0,
        'total_size': 0,
        'failed_files_list': []
    }

    for rel_path in untracked_files:
        abs_path = os.path.join(repo_path, rel_path)
        stats['processed_files'] += 1
        
        # Skip directories (git reports them in untracked_files)
        if os.path.isdir(abs_path):
            continue
            
        file_size, success = safe_get_file_size(abs_path)
        
        if not success:
            stats['failed_files'] += 1
            stats['failed_files_list'].append(rel_path)
            logging.debug(f"Size check failed for: {rel_path}")
            continue
            
        stats['successful_files'] += 1
        stats['total_size'] += file_size
        
        if file_size > max_chunk_size:
            stats['large_files'] += 1
            logging.info(f"Skipping large file: {rel_path} ({file_size/1024/1024:.2f}MB)")
            continue
            
        if current_chunk_size + file_size > max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = [rel_path]
            current_chunk_size = file_size
            stats['total_chunks'] += 1
        else:
            current_chunk.append(rel_path)
            current_chunk_size += file_size
    
    if current_chunk:
        chunks.append(current_chunk)
        stats['total_chunks'] += 1
    
    return chunks, stats

def generate_report(chunks: List[List[str]], stats: Dict[str, int], repo_path: str) -> None:
    """Generate comprehensive report with statistics and chunk details"""
    report = [
        "=" * 80,
        f"Git Repository Chunking Report",
        f"Repository: {repo_path}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "-" * 80,
        "Summary Statistics:",
        f"  Total files processed: {stats['total_files']}",
        f"  Successfully processed files: {stats['successful_files']}",
        f"  Files that couldn't be measured: {stats['failed_files']}",
        f"  Files too large (>25MB): {stats['large_files']}",
        f"  Total size of processable files: {stats['total_size']/(1024*1024):.2f}MB",
        f"  Total chunks created: {stats['total_chunks']}",
        "-" * 80
    ]
    
    # Add chunk details
    report.append("\nChunk Details:")
    for i, chunk in enumerate(chunks, 1):
        chunk_size = sum(safe_get_file_size(os.path.join(repo_path, f))[0] for f in chunk)
        report.append(f"\nChunk #{i} ({len(chunk)} files, {chunk_size/(1024*1024):.2f}MB):")
        for file_path in chunk:
            file_size = safe_get_file_size(os.path.join(repo_path, file_path))[0]
            report.append(f"  - {file_path} ({file_size/(1024*1024):.2f}MB)")
    
    # Add list of problematic files if any
    if stats['failed_files'] > 0:
        report.extend([
            "-" * 80,
            "\nFiles that couldn't be processed:",
            *[f"  - {f}" for f in stats['failed_files_list']]
        ])
    
    report.append("=" * 80)
    
    # Write to log
    logging.info("\n".join(report))

def main():
    setup_logging()
    logging.info("Starting Git Repository Chunking Tool")
    
    try:
        # Get project directory
        repo_path = get_project_directory()
        logging.info(f"\nProcessing repository at: {repo_path}")
        
        # Initialize repository
        repo = git.Repo(repo_path)
        
        # Get untracked files
        untracked_files = get_untracked_files(repo)
        
        if not untracked_files:
            logging.info("No untracked files found in the repository.")
            return
        
        logging.info(f"Found {len(untracked_files)} untracked items (files and folders).")
        
        # Calculate chunks
        chunks, stats = calculate_chunks(untracked_files, repo_path)
        
        if not chunks:
            logging.info("\nNo valid chunks could be created. Possible reasons:")
            if stats['large_files']:
                logging.info(f"- {stats['large_files']} files were too large (>25MB)")
            if stats['failed_files']:
                logging.info(f"- Couldn't get size for {stats['failed_files']} files")
            return
        
        # Generate report
        generate_report(chunks, stats, repo_path)
        
        logging.info("\nOperation completed successfully. Full report saved to git_chunks.log")
    
    except Exception as e:
        logging.error(f"\nFatal error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()