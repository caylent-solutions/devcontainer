#!/usr/bin/env python3
"""
Convert Windows line endings (CRLF) to Unix line endings (LF) for all text files.
Excludes binary files and processes files in parallel for performance.
"""

import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Thread-safe counters
stats_lock = Lock()
converted_count = 0
skipped_count = 0
error_count = 0

def convert_file(file_path):
    """Convert a single file from CRLF to LF if it's a text file."""
    global converted_count, skipped_count, error_count
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            
        if not content:
            with stats_lock:
                skipped_count += 1
            return False
            
        # Skip binary files (contain null bytes)
        if b'\x00' in content:
            with stats_lock:
                skipped_count += 1
            return False
            
        # Skip if no CRLF to convert
        if b'\r\n' not in content:
            with stats_lock:
                skipped_count += 1
            return False
            
        # Convert CRLF to LF
        converted_content = content.replace(b'\r\n', b'\n')
        
        with open(file_path, 'wb') as f:
            f.write(converted_content)
            
        with stats_lock:
            converted_count += 1
        return True
        
    except (OSError, IOError) as e:
        with stats_lock:
            error_count += 1
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False

def main():
    """Main function to process all files in the workspace."""
    global converted_count, skipped_count, error_count
    workspace_path = Path(os.getcwd())
    
    if not workspace_path.exists():
        print(f"Error: Workspace path {workspace_path} does not exist", file=sys.stderr)
        sys.exit(1)
    
    print(f"Converting line endings in: {workspace_path}")
    
    # Find all files
    files_to_process = []
    for root, dirs, files in os.walk(workspace_path):
        # Skip .git directory for performance
        if '.git' in dirs:
            dirs.remove('.git')
            
        for file in files:
            file_path = Path(root) / file
            files_to_process.append(file_path)
    
    if not files_to_process:
        print("No files found to process")
        return
    
    print(f"Processing {len(files_to_process)} files...")
    
    # Process files in parallel
    max_workers = os.cpu_count() or 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(convert_file, file_path): file_path 
                  for file_path in files_to_process}
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                file_path = futures[future]
                print(f"Unexpected error processing {file_path}: {e}", file=sys.stderr)
                with stats_lock:
                    error_count += 1
    
    # Print summary
    print(f"Line ending conversion complete:")
    print(f"  Converted: {converted_count} files")
    print(f"  Skipped: {skipped_count} files")
    if error_count > 0:
        print(f"  Errors: {error_count} files")
        sys.exit(1)

if __name__ == "__main__":
    main()