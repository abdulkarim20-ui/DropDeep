import os
import fnmatch
import logging
from datetime import datetime
from src.backend.analyzers.file_types import get_file_type


logger = logging.getLogger(__name__)

# Extensions that are safe to read as text/code
ALLOWED_CODE_EXTENSIONS = {
    '.py', '.pyw', '.js', '.jsx', '.ts', '.tsx', '.html', '.htm',
    '.css', '.scss', '.sass', '.less', '.json', '.xml', '.yaml', '.yml',
    '.md', '.txt', '.sql', '.c', '.cpp', '.h', '.hpp', '.java', '.cs',
    '.sh', '.bat', '.ps1', '.dockerfile', '.conf', '.ini', '.toml',
    '.gitignore', '.env', '.vb', '.rb', '.php', '.go', '.rs', '.swift',
    '.kt', '.kts', '.lua', '.pl', '.r', '.m', '.vue', '.svelte'
}

SPECIAL_TEXT_FILES = {'dockerfile', 'makefile', 'license', 'readme', 'changelog', 'cmakelists.txt'}

# Performance limits
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
MAX_FOLDER_DEPTH = 50  # Prevent infinite recursion on symlink loops


def scan_directory_structure(startpath, ignore_manager=None, progress_callback=None, pause_event=None, stop_event=None):
    """
    Recursively scans the directory and builds a structured dictionary.
    Supports pausing via threading.Event and safe stopping.
    
    Optimized for large folders with:
    - Depth limiting to prevent infinite loops
    - Fast folder stats (removed expensive recursive size/mtime)
    - File size limits for content reading
    - Efficient memory usage
    """
    
    if not startpath or not os.path.isdir(startpath):
        logger.warning(f"Invalid start path: {startpath}")
        return {
            'name': 'Invalid',
            'path': startpath or '',
            'type': 'folder',
            'display_type': 'Folder',
            'children': []
        }
    
    root_name = os.path.basename(startpath) or startpath
    root_node = {
        'name': root_name,
        'path': '.',  # Root marker - consistent relative path model
        'abs_path': os.path.abspath(startpath),  # Store absolute for reference
        'type': 'folder',
        'display_type': 'Folder',
        'children': []
    }
    
    # Stack: (abs_path, parent_node, depth)
    stack = [(startpath, root_node, 0)]
    processed_count = 0
    visited_paths = set()  # Prevent symlink loops
    
    while stack:
        # Check Stop
        if stop_event and stop_event.is_set():
            return root_node

        # Check Pause
        if pause_event:
            pause_event.wait()  # Blocks if cleared (paused)

        current_path, current_node, depth = stack.pop()
        
        # Depth check
        if depth > MAX_FOLDER_DEPTH:
            logger.warning(f"Max depth reached at {current_path}")
            continue
        
        # Symlink loop detection
        try:
            real_path = os.path.realpath(current_path)
            if real_path in visited_paths:
                logger.debug(f"Skipping symlink loop: {current_path}")
                continue
            visited_paths.add(real_path)
        except OSError:
            continue
        
        try:
            # Use scandir for better performance
            items = list(os.scandir(current_path))
            items.sort(key=lambda x: x.name.lower())
        except (OSError, PermissionError) as e:
            logger.debug(f"Cannot access {current_path}: {e}")
            continue
        
        for entry in items:
            item = entry.name
            full_path = entry.path
            
            # Check if the item should be ignored
            if ignore_manager and ignore_manager.should_ignore(item):
                continue
            # Removed deprecated IGNORED_PATTERNS fallback
            
            # Skip hidden files
            if item.startswith('.'):
                continue
            
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
            except OSError:
                continue
            
            if is_dir:
                # Optimized: No expensive folder stats
                new_folder_node = {
                    'name': item,
                    'path': os.path.relpath(full_path, startpath),
                    'type': 'folder',
                    'display_type': 'Folder',
                    'size_bytes': None,        # lazy / optional
                    'last_modified': None,
                    'children': []
                }
                current_node['children'].append(new_folder_node)
                stack.append((full_path, new_folder_node, depth + 1))
                
            elif is_file:
                # File processing
                processed_count += 1
                if progress_callback:
                    progress_callback(processed_count)
                
                try:
                    stat_info = entry.stat(follow_symlinks=False)
                    file_size = stat_info.st_size
                    file_mtime = stat_info.st_mtime
                except (OSError, PermissionError):
                    file_size = 0
                    file_mtime = 0
                    
                file_node = {
                    'name': item,
                    'path': os.path.relpath(full_path, startpath),
                    'type': 'file',
                    'display_type': get_file_type(item),
                    'content': None,
                    'size_bytes': file_size,
                    'last_modified': datetime.fromtimestamp(file_mtime).isoformat() if file_mtime else ""
                }
                
                # Check if we should read content
                _, ext = os.path.splitext(item)
                is_text_code = (ext.lower() in ALLOWED_CODE_EXTENSIONS) or (item.lower() in SPECIAL_TEXT_FILES)
                
                if is_text_code:
                    try:
                        # Use MAX_FILE_SIZE limit
                        if file_size <= MAX_FILE_SIZE:
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                file_node['content'] = f.read()
                        else:
                            file_node['content'] = None
                            file_node['too_large'] = True
                    except Exception:
                        file_node['content'] = None
                
                current_node['children'].append(file_node)
                
    # Populate stats centrally
    try:
        from src.backend.analyzers.stats_analyzer import calculate_folder_stats
        root_node['stats'] = calculate_folder_stats(startpath)
    except Exception as e:
        logger.error(f"Failed to calculate stats: {e}")
        # Basic fallback stats from scan
        root_node['stats'] = {'files': processed_count}

    return root_node

