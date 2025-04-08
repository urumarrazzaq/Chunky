# Git Repository Chunking Tool

## Description
The Git Repository Chunking Tool is a Python utility designed to manage and organize large sets of untracked files in a Git repository by dividing them into smaller, more manageable chunks. It does this by analyzing untracked files, determining their sizes, and grouping them into chunks that fit within a specified size limit (default 25MB). This tool is useful for developers and teams managing large repositories, especially when working with untracked files that may be too large to handle in a single commit or need to be managed in a more efficient manner.

## Features:
Automatic Directory Detection: The tool asks for the directory path of the Git repository and validates it to ensure it’s a valid Git repository.

Untracked Files Handling: Identifies all untracked files in the repository and skips directories.

Size Calculation: Efficiently checks the size of each untracked file using multiple fallback methods, ensuring compatibility across platforms.

Chunking Files: Groups files into chunks based on a user-defined size limit (default 25MB).

Reporting: Generates a detailed report of the chunking process, including statistics like the total number of files processed, files that couldn’t be processed, chunk details, and large files that were skipped.

Logging: Comprehensive logging of operations, including errors, progress, and details of the chunking process.

## Key Statistics Tracked:
Total number of untracked files processed.

Number of files successfully processed.

Number of files that couldn’t be measured.

Number of files skipped due to being too large (greater than 25MB).

Total size of processable files.

Total number of chunks created.

## Report Generation:
Summary of the chunking operation.

Detailed breakdown of each chunk created, including file names and sizes.

List of files that could not be processed, including reasons.

