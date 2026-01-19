import os
import sys

# Define a list of file extensions and folders to ignore.
# Define a list of file extensions and folders to ignore COMPLETELY (never shown in tree).
IGNORED_PATTERNS = [
    'node_modules',
    '__pycache__',
    'dist',
    'build',
    '.git',
    'venv',
    '.env',
    '.vscode',
    '.idea'
]

# Define file extensions that should be visible in the tree but NOT read/exported.
NON_TEXT_EXTENSIONS = [
    # Images
    '*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.svg', '*.ico', '*.webp', '*.tiff',
    # Documents
    '*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt', '*.pptx',
    # Audio/Video
    '*.mp3', '*.wav', '*.mp4', '*.avi', '*.mov', '*.mkv',
    # Archives
    '*.zip', '*.tar', '*.gz', '*.rar', '*.7z',
    # Executables/Binaries
    '*.exe', '*.dll', '*.so', '*.dylib', '*.bin', '*.iso'
]

# Define a mapping of file extensions to their corresponding emojis and file types
FILE_TYPE_MAP = {
    '.py': ('🐍', 'SCRIPT'),
    '.js': ('📜', 'SCRIPT'),
    '.jsx': ('⚛️', 'COMPONENT'),
    '.ts': ('💎', 'SCRIPT'),
    '.tsx': ('⚛️', 'COMPONENT'),
    '.html': ('🌐', 'PAGE'),
    '.htm': ('🌐', 'PAGE'),
    '.css': ('🎨', 'STYLE'),
    '.scss': ('🎨', 'STYLE'),
    '.json': ('🔧', 'CONFIG'),
    '.java': ('☕', 'CLASS'),
    '.c': ('⚙️', 'CODE'),
    '.cpp': ('⚙️', 'CODE'),
    '.h': ('⚙️', 'CODE'),
    '.cs': ('⚙️', 'CODE'),
    '.sql': ('🗄️', 'QUERY'),
    '.yaml': ('🔧', 'CONFIG'),
    '.yml': ('🔧', 'CONFIG'),
    '.env': ('🔒', 'SECRET'),
    '.gitignore': ('👻', 'CONFIG'),
    'Dockerfile': ('🐳', 'CONFIG'),
    'Makefile': ('🛠️', 'BUILD'),
    'README.md': ('📘', 'DOCS'),
    'default': ('📄', 'CODE'),
}

def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Resolve to project root (parent of 'src' folder where this config.py resides)
        # Path: DropDeep/src/config.py -> root is DropDeep/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)
