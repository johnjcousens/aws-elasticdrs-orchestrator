#!/usr/bin/env python3
"""
Script to remove the expensive transform functions from api-handler
"""

def remove_transform_functions():
    """Remove transform functions from lines 8102-8465"""
    file_path = "lambda/api-handler/index.py"
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Remove lines 8102-8465 (transform functions)
    # Python uses 0-based indexing, so line 8102 is index 8101
    start_line = 8101  # Line 8102 (0-based)
    end_line = 8465    # Line 8466 (0-based, exclusive)
    
    print(f"Removing lines {start_line + 1} to {end_line} from {file_path}")
    print(f"Original file has {len(lines)} lines")
    
    # Keep lines before and after the transform functions
    new_lines = lines[:start_line] + lines[end_line:]
    
    print(f"New file will have {len(new_lines)} lines")
    print(f"Removed {len(lines) - len(new_lines)} lines")
    
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Successfully removed transform functions from {file_path}")

if __name__ == "__main__":
    remove_transform_functions()