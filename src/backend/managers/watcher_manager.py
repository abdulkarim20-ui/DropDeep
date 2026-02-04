from PyQt5.QtCore import QObject, pyqtSignal, QFileSystemWatcher, QTimer
import os

class WatcherManager(QObject):
    file_changed = pyqtSignal(str)
    directory_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self._on_file_changed)
        self.watcher.directoryChanged.connect(self._on_directory_changed)
        self.watched_dirs = set()
        self.watched_files = set()
        
        # Debounce timer to avoid spamming updates (e.g. git operations)
        self._debouncer = QTimer()
        self._debouncer.setSingleShot(True)
        self._debouncer.setInterval(500) # 500ms debounce
        self._debouncer.timeout.connect(self._emit_buffered_changes)
        
        self._pending_file_changes = set()
        self._pending_dir_changes = set()

        # Flag to prevent self-loop if we implement saving later
        self._is_internal_change = False

    def start_watching_project(self, root_path):
        """Recursively watch all directories in the project."""
        self.stop_watching_project()
        if not os.path.exists(root_path):
            return

        self._add_dir_recursive(root_path)

    def stop_watching_project(self):
        """Stop watching all directories."""
        if self.watched_dirs:
            # removePaths expects a list of strings
            self.watcher.removePaths(list(self.watched_dirs))
        self.watched_dirs.clear()

    def watch_file(self, path):
        """Watch a specific file for content changes."""
        if not path or not os.path.exists(path):
            return
        if path not in self.watched_files:
            self.watcher.addPath(path)
            self.watched_files.add(path)

    def unwatch_file(self, path):
        """Stop watching a specific file."""
        if path in self.watched_files:
            # QFileSystemWatcher might throw if path doesn't exist anymore
            try:
                self.watcher.removePath(path)
            except:
                pass
            self.watched_files.discard(path)
            
    def _add_dir_recursive(self, path):
         if path in self.watched_dirs:
             return
             
         try:
             self.watcher.addPath(path)
             self.watched_dirs.add(path)
             
             for item in os.listdir(path):
                 full_path = os.path.join(path, item)
                 if os.path.isdir(full_path):
                     # Skip hidden/system directories if needed, but for now include all
                     self._add_dir_recursive(full_path)
         except Exception:
             pass

    def _on_file_changed(self, path):
        if self._is_internal_change:
            return
        self._pending_file_changes.add(path)
        self._debouncer.start()

    def _on_directory_changed(self, path):
        if self._is_internal_change:
            return
            
        self._pending_dir_changes.add(path)
        # Check for new subdirectories to watch immediately
        try:
             if os.path.isdir(path):
                 self._refresh_dir_watches(path)
        except:
             pass
        self._debouncer.start()
        
    def _refresh_dir_watches(self, path):
        # Scan immediate children to see if new dirs appeared
        try:
             for item in os.listdir(path):
                 full_path = os.path.join(path, item)
                 if os.path.isdir(full_path) and full_path not in self.watched_dirs:
                     self._add_dir_recursive(full_path)
        except Exception:
            pass

    def _emit_buffered_changes(self):
        # Process files
        for f in self._pending_file_changes:
            # Check if file still exists (it might have been deleted)
            if os.path.exists(f):
                 self.file_changed.emit(f)
        self._pending_file_changes.clear()
        
        # Process dirs
        if self._pending_dir_changes:
             # Just emit one "structure changed" signal or multiple.
             # Emitting specific paths allows partial refresh if implemented.
             for d in self._pending_dir_changes:
                self.directory_changed.emit(d)
        self._pending_dir_changes.clear()
