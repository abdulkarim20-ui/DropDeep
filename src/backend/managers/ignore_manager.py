import fnmatch
import os
import json
from src.config import resource_path

# Robust default patterns for ignoring files/folders
# These include system files, build artifacts, and sensitive data not suitable for LLMs
DEFAULT_PATTERNS = [
    # System & IDE
    '.git', '.svn', '.hg', '.DS_Store', 'Thumbs.db', '.vscode', '.idea',
    # JavaScript / Node
    'node_modules', 'bower_components', 'jspm_packages', '.npm', '.yarn', 'yarn.lock', 'package-lock.json',
    # Python
    '__pycache__', '*.pyc', '*.pyo', '*.pyd', '.Python', 'env', 'venv', '.env', '.venv', 'pip-log.txt',
    # Build / Dist
    'dist', 'build', 'out', 'target', 'bin', 'obj',
    # Logs
    'logs', '*.log', 'npm-debug.log*', 'yarn-debug.log*', 'yarn-error.log*',
    # Sensitive / Secrets (Critical for LLM safety)
    '.env', '.env.local', '.env.*', 'config.js', 'config.json', 'secrets.json',
    '*.pem', '*.key', 'id_rsa', 'id_dsa', 'id_ed25519', 'known_hosts',
    # Large/Binary/Media (Often useless for text analysis)
    '*.exe', '*.dll', '*.so', '*.dylib', '*.iso', '*.bin', '*.dmg',
    '*.zip', '*.tar', '*.gz', '*.rar', '*.7z',
    '*.jpg', '*.jpeg', '*.png', '*.gif', '*.ico', '*.svg', '*.mp4', '*.mp3', '*.pdf'
]

class IgnoreManager:
    def __init__(self, use_persistence=True):
        # .../src/backend/managers/ignore_manager.py -> .../src/backend/managers -> .../src/backend -> .../src -> root
        self.persistence_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'ignore_patterns.json')
        self.default_patterns = set(DEFAULT_PATTERNS)
        self.user_patterns = set()
        self.session_patterns = set()  # Temporary patterns for this run only
        self.removed_patterns = set()
        self.use_persistence = use_persistence
        
        if self.use_persistence:
            self.load_patterns()
        
    def get_all_patterns(self):
        """Returns list of all active patterns (defaults + user + session - removed)."""
        # Start with defaults
        active = self.default_patterns.copy()
        # Add user patterns
        active.update(self.user_patterns)
        # Add session patterns
        active.update(self.session_patterns)
        # Remove excluded patterns
        active.difference_update(self.removed_patterns)
        
        return sorted(list(active))

    def load_patterns(self):
        """Load patterns from the local JSON file."""
        if not os.path.exists(self.persistence_file):
            return
            
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'user_patterns' in data:
                    self.user_patterns = set(data['user_patterns'])
                if 'removed_patterns' in data:
                    self.removed_patterns = set(data['removed_patterns'])
        except Exception as e:
            print(f"Error loading ignore patterns: {e}")

    def save_patterns(self):
        """Save current user patterns to JSON."""
        if not self.use_persistence:
            return
            
        data = {
            'user_patterns': list(self.user_patterns),
            'removed_patterns': list(self.removed_patterns)
        }
        try:
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving ignore patterns: {e}")

    def add_pattern(self, pattern):
        """Add a new pattern to the persistent ignore list."""
        if not pattern:
            return
            
        # If it was previously removed, un-remove it
        if pattern in self.removed_patterns:
            self.removed_patterns.remove(pattern)
            
        # Add to user patterns
        self.user_patterns.add(pattern)
        self.save_patterns()

    def add_session_pattern(self, pattern):
        """Add a pattern ONLY for this session (not saved)."""
        if not pattern:
            return

        # If it was previously removed, un-remove it temporarily
        if pattern in self.removed_patterns:
            self.removed_patterns.remove(pattern)
            
        self.session_patterns.add(pattern)
        # Do NOT save_patterns()

    def remove_pattern(self, pattern):
        """Remove a pattern.
        If it's in user_patterns, remove it.
        If it's in default_patterns, add to removed_patterns.
        """
        changed = False
        
        if pattern in self.user_patterns:
            self.user_patterns.remove(pattern)
            changed = True
            
        if pattern in self.session_patterns:
            self.session_patterns.remove(pattern)
            # No save needed for session list, but flow logic remains same
            
        if pattern in self.default_patterns:
            self.removed_patterns.add(pattern)
            changed = True
            
        if changed:
            self.save_patterns()



    def reset_to_defaults(self):
        """Clear user patterns and removed patterns."""
        self.user_patterns = set()
        self.removed_patterns = set()
        self.save_patterns()
        
    def set_custom_patterns(self, patterns):
        """Mass setter (legacy support or bulk import)."""
        self.user_patterns = set(patterns)
        self.save_patterns()

    def should_ignore(self, name):
        """Check if a file/folder name matches any ignore pattern."""
        active_patterns = self.get_all_patterns()
        return any(fnmatch.fnmatch(name, p) for p in active_patterns)
