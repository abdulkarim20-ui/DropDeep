import os
import logging

# Setup basic logging for debugging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def format_size(size):
    """Convert bytes to human-readable format"""
    if size == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def calculate_folder_stats(path):
    """
    Calculates total files, folders, and size of a directory recursively.
    Handles permission errors gracefully and ensures robust scanning.
    
    Args:
        path: Absolute path to the directory to analyze
        
    Returns:
        dict: Contains 'files', 'folders', 'size', 'size_str'
    """
    total_files = 0
    total_folders = 0
    total_size = 0
    
    # Common heavy folders to skip for performance
    SKIP_DIRS = {'node_modules', '.git', 'venv', '__pycache__', 'dist', 'build', '.idea', '.vscode'}
    
    if not os.path.exists(path):
        logger.warning(f"Path does not exist: {path}")
        return {
            'files': 0,
            'folders': 0,
            'size': 0,
            'size_str': '0 B'
        }
    
    if not os.path.isdir(path):
        logger.warning(f"Path is not a directory: {path}")
        # If it's a file, count it as 1 file
        try:
            file_size = os.path.getsize(path)
            return {
                'files': 1,
                'folders': 0,
                'size': file_size,
                'size_str': format_size(file_size)
            }
        except OSError as e:
            logger.error(f"Error getting file size: {e}")
            return {
                'files': 0,
                'folders': 0,
                'size': 0,
                'size_str': '0 B'
            }
    
    # Scan the directory
    try:
        for root, dirs, files in os.walk(path):
            # Filter out directories to skip (modify in-place)
            original_dirs = dirs[:]
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            # Count folders (excluding skipped ones)
            total_folders += len(dirs)
            
            # Count files
            total_files += len(files)
            
            # Calculate size for each file
            for filename in files:
                try:
                    filepath = os.path.join(root, filename)
                    # Use lstat to avoid following symlinks
                    file_stat = os.lstat(filepath)
                    total_size += file_stat.st_size
                except (OSError, PermissionError) as e:
                    # Log but continue - don't let one file error stop everything
                    logger.debug(f"Could not access file {filename}: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Unexpected error accessing {filename}: {e}")
                    continue
                    
    except PermissionError as e:
        logger.warning(f"Permission denied accessing directory: {path}")
        # Return what we have so far
    except Exception as e:
        logger.error(f"Error walking directory {path}: {e}")
        # Return what we have so far
    
    return {
        'files': total_files,
        'folders': total_folders,
        'size': total_size,
        'size_str': format_size(total_size)
    }
