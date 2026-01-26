from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, 
    QLabel, QPushButton, QFileDialog, QMessageBox, QProgressBar, QCheckBox, QSizePolicy,
    QLineEdit, QAction, QMenu, QApplication, QFrame, QSplitter
)
from src.frontend.components.toggle_switch import ToggleSwitch
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap

from src.frontend.styles.theme import STYLESHEET, COLOR_PRIMARY
from src.frontend.components.drop_zone import DropZone
from src.frontend.components.tree_view import FileTreeWidget
from src.frontend.components.canvas_preview import CanvasPreview

from src.backend.scanner import scan_directory_structure
from src.backend.exporter import export_data
from src.config import IGNORED_PATTERNS
from src.backend.managers.ignore_manager import IgnoreManager
from src.frontend.components.advanced_ignore import AdvancedIgnoreWidget
from src.backend.managers.recent_manager import load_recent, add_recent
from src.frontend.components.recent_folders import RecentFoldersWidget
from src.backend.managers.watcher_manager import WatcherManager
from src.config import resource_path
import os
import subprocess
import platform

class AddressBar(QLineEdit):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._should_select_all = False
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Select all on tab focus
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        if not self.hasFocus():
            self._should_select_all = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._should_select_all:
            QTimer.singleShot(0, self.selectAll)
            self._should_select_all = False

    def contextMenuEvent(self, event):
        from src.frontend.components.tree_context_menu.menu_base import ExplorerStyleMenu
        menu = ExplorerStyleMenu(self)
        
        def add_action(name, shortcut, slot, icon_file=None):
            from PyQt5.QtGui import QIcon
            from src.config import resource_path
            import os

            icon = QIcon()
            if icon_file:
                p = resource_path(f"assets/{icon_file}")
                if os.path.exists(p):
                    icon = QIcon(p)
            
            action = menu.addAction(icon, name)
            action.setShortcut(shortcut)
            action.setShortcutVisibleInContextMenu(True)
            action.triggered.connect(slot)

        add_action("Cut", "Ctrl+X", self.cut, "cut.png")
        add_action("Copy", "Ctrl+C", self.copy, "copy.png")
        menu.addSeparator()
        add_action("Select All", "Ctrl+A", self.selectAll)

        menu.exec_(event.globalPos())

class ScanThread(QThread):
    scan_finished = pyqtSignal(dict)
    progress_update = pyqtSignal(int, int) # current, total
    
    def __init__(self, path, ignore_manager=None):
        super().__init__()
        self.path = path
        self.ignore_manager = ignore_manager
        
        # Pause Event (Set = Running, Clear = Paused)
        from threading import Event
        self.pause_event = Event()
        self.pause_event.set() # Start running
        
        self.stop_event = Event()
        self.stop_requested = False
        
    def run(self):
        # 1. Pre-scan to get total files (for progress bar)
        total_files = 0
        try:
           # Send initial status
           self.progress_update.emit(0, 0)
           
           for root, dirs, files in os.walk(self.path):
               if self.stop_event.is_set(): return
               total_files += len(files)
               # Optional: Emit "Calculating..." updates if really large
        except Exception:
            total_files = 100 
            
        if total_files == 0: total_files = 1
        
        # State for throttling
        self._last_emit_percent = -1
        self._last_emit_time = 0
        import time
        
        # Define callback
        def on_progress(count):
            if self.stop_event.is_set(): return
            
            # Calculate percent
            percent = int((count / total_files) * 100)
            
            # Throttle: Emit only if percent changes OR every 100ms
            now = time.time()
            if percent > self._last_emit_percent or (now - self._last_emit_time) > 0.1:
                self.progress_update.emit(count, total_files)
                self._last_emit_percent = percent
                self._last_emit_time = now

        # 2. Run Scan
        result = scan_directory_structure(
            self.path, 
            self.ignore_manager, 
            progress_callback=on_progress,
            pause_event=self.pause_event,
            stop_event=self.stop_event
        )
        self.scan_finished.emit(result)

    def is_paused(self):
        return not self.pause_event.is_set()

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DropDeep")
        
        # Window size presets (single source of truth)
        self.HOME_WIDTH = 380
        self.HOME_HEIGHT = 420
        self.HOME_HEIGHT_ADV = 480
        self.SIZE_RESULT = (940, 600) 

        # Start in HOME size (Advanced enabled by default now)
        self.setFixedSize(self.HOME_WIDTH, self.HOME_HEIGHT_ADV)
        
        # Pro-Desktop UI flags (Enable resize grips even if framed)
        self.setWindowFlag(Qt.Window, True)
        self.setMouseTracking(True)
        
        # Set App Icon
        icon_path = resource_path("assets/app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Apply Theme
        self.setStyleSheet(STYLESHEET)
        
        # State Tracking
        self.home_advanced_enabled = False
        self.resize_anim = None
        
        # Central Widget & Stack
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.stack = QStackedWidget()
        
        # layouts
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.stack)
        
        # Initialize Views
        # Initialize Views
        self.init_home_view()
        self.init_result_view()
        
        # Start Home
        self.stack.setCurrentWidget(self.home_page)
        
        # Center Window on Screen (Robust Fix)
        self.center_window()
        
        self.current_data = None
        self.scan_thread = None
        self.selected_folder_path = None # Track selected folder
        
        # Watcher
        self.watcher = WatcherManager()
        self.watcher.file_changed.connect(self.on_file_changed)
        self.watcher.directory_changed.connect(self.on_directory_changed)

    def center_window(self):
        """Centers the window on the primary screen and ensures it fits."""
        screen = QApplication.primaryScreen()
        if not screen:
            return
            
        screen_geo = screen.availableGeometry()
        window_geo = self.frameGeometry()
        
        # Center point
        center_point = screen_geo.center()
        window_geo.moveCenter(center_point)
        
        # Iterate to ensure Top-Left is visible (handling multi-monitor weirdness or huge scaling)
        # Move window top-left to calculated position, but clamp to 0,0 relative to screen
        new_x = window_geo.x()
        new_y = window_geo.y()
        
        # Basic Clamp: Ensure title bar isn't off-screen top
        if new_y < screen_geo.y():
            new_y = screen_geo.y()
            
        self.move(new_x, new_y)

    def lock_window(self, width, height):
        """Lock window size (no user resize)."""
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resize(width, height)

    def animate_home_height(self, target_height):
        # STOP any running animation
        if hasattr(self, "home_height_anim") and self.home_height_anim:
            if self.home_height_anim.state() == QPropertyAnimation.Running:
                self.home_height_anim.stop()

        fixed_width = self.width()  # 🔒 LOCK WIDTH

        self.home_height_anim = QPropertyAnimation(self, b"size")
        self.home_height_anim.setDuration(200)
        self.home_height_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.home_height_anim.setStartValue(self.size())
        self.home_height_anim.setEndValue(QSize(fixed_width, target_height))

        self.home_height_anim.finished.connect(
            lambda: self.setFixedSize(fixed_width, target_height)
        )

        self.home_height_anim.start()

    def animate_advanced_panel(self, expand: bool):
        start = self.ignore_widget.maximumHeight()
        end = 36 if expand else 0  # exact height of your widget

        self.panel_anim = QPropertyAnimation(
            self.ignore_widget, b"maximumHeight"
        )
        self.panel_anim.setDuration(180)
        self.panel_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.panel_anim.setStartValue(start)
        self.panel_anim.setEndValue(end)
        self.panel_anim.start()

    def animate_window(self, target_rect, on_finished=None):
        # Keep a strong reference and parent the animation to avoid GC
        if hasattr(self, '_geometry_anim') and self._geometry_anim:
            try:
                self._geometry_anim.stop()
            except Exception:
                pass

        self._geometry_anim = QPropertyAnimation(self, b"geometry", self)
        self._geometry_anim.setDuration(350)  # Smoother, more premium feel
        self._geometry_anim.setEasingCurve(QEasingCurve.OutCubic)  # Expands smoothly, decelerates at end
        self._geometry_anim.setStartValue(self.geometry())
        self._geometry_anim.setEndValue(target_rect)
        
        if on_finished is not None:
            def _finish_and_release():
                try:
                    on_finished()
                finally:
                    self._geometry_anim = None
            self._geometry_anim.finished.connect(_finish_and_release)
        else:
            def _release():
                self._geometry_anim = None
            self._geometry_anim.finished.connect(_release)
            
        self._geometry_anim.start()

    def _clear_size_constraints(self):
        try:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            # Ensure central widget doesn't block
            if self.centralWidget():
                self.centralWidget().setMinimumSize(0, 0)
        except Exception:
            pass
    
    # Deprecated old resize animations in favor of animate_window
    def animate_resize(self, width, height, lock_after=False, callback=None):
        # Calculate centered position for the new size
        screen = QApplication.primaryScreen()
        target_rect = QRect(self.x(), self.y(), width, height)
        
        if screen:
             avail = screen.availableGeometry()
             # Center X
             center_x = avail.center().x() - (width // 2)
             # Center Y
             center_y = avail.center().y() - (height // 2)
             
             # Clamp top safety
             if center_y < avail.y(): 
                 center_y = avail.y()
             
             target_rect = QRect(center_x, center_y, width, height)
        
        def _done():
            if lock_after:
                self.setFixedSize(width, height)
            if callback:
                callback()
                
        self._clear_size_constraints()
        self.animate_window(target_rect, on_finished=_done)

    def unlock_window(self, min_width=620, min_height=480):
        """
        Unlocks the window constraints so the user can resize.
        Also performs a safety check to ensure window fits on screen.
        """
        self.setMinimumSize(min_width, min_height)
        self.setMaximumSize(16777215, 16777215)
        
        screen = QApplication.primaryScreen()
        if screen:
            avail_geo = screen.availableGeometry()
            screen_h = avail_geo.height()
            screen_w = avail_geo.width()
            
            # If current height exceeds screen height, clamp it
            current_h = self.height()
            current_w = self.width()
            
            new_h = current_h
            new_w = current_w
            
            if current_h > screen_h:
                new_h = int(screen_h * 0.9) # 90% of screen height
            
            if current_w > screen_w:
                new_w = int(screen_w * 0.9)
                
            if new_h != current_h or new_w != current_w:
                self.resize(new_w, new_h)
                self.center_window() # Re-center after forceful resize
            elif self.y() < avail_geo.y():
                # Just reposition if off-top without resize needed
                self.move(self.x(), avail_geo.y())

    def init_home_view(self):
        self.home_page = QWidget()
        layout = QVBoxLayout(self.home_page)
        # Narrower margins for mobile-like width
        layout.setContentsMargins(24, 0, 24, 0) # Top/Bottom handled by stretch
        layout.setSpacing(0) # Spacing handled manually
        
        # Top Bar (More Menu)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 16, 0, 0) # Top margin for spacing
        top_bar.addStretch()
        
        self.btn_more = QPushButton()
        self.btn_more.setCursor(Qt.PointingHandCursor)
        self.btn_more.setFixedSize(32, 32)
        self.btn_more.setToolTip("More")
        
        # Try more.png first, fallback to settings.png
        more_icon_path = resource_path("assets/more.png")
        if os.path.exists(more_icon_path):
            self.btn_more.setIcon(QIcon(more_icon_path))
            self.btn_more.setIconSize(QSize(20, 20))
            
        self.btn_more.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
            QPushButton:pressed {
                background-color: #E5E7EB;
            }
            QPushButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)
        
        # Create More Menu
        self._build_more_menu()
        
        top_bar.addWidget(self.btn_more)
        layout.addLayout(top_bar)

        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.setFixedSize(332, 260) # Fixed Card Size (380 - 48 margins = 332 available width)
        self.drop_zone.folderDropped.connect(self.on_folder_ready)
        self.drop_zone.clicked.connect(self.browse_folder)
        
        layout.addStretch(1)
        layout.addWidget(self.drop_zone, 0, Qt.AlignCenter)
        
        layout.addSpacing(8)
        
        # Initialize Ignore Manager (Loads patterns + defaults)
        self.ignore_manager = IgnoreManager(use_persistence=True)

        # Advanced Ignore Toggle
        self.advanced_check = ToggleSwitch("Advanced ignore patterns")
        self.advanced_check.toggled.connect(self.toggle_advanced_ignore)
        layout.addWidget(self.advanced_check, 0, Qt.AlignLeft)
        
        # Default: ON (User wants clarity)
        # Note: SetChecked triggers toggled signal usually, so we need to handle state init first.
        self.home_advanced_enabled = True 
        self.advanced_check.setChecked(True)
        
        # Advanced Ignore Input (hidden by default)
        self.ignore_widget = AdvancedIgnoreWidget(self.ignore_manager)
        self.ignore_widget.patterns_changed.connect(self.reload_scan)
        # self.ignore_widget.setVisible(False) <--- REMOVED
        
        # ✅ Correct Layout Initialization
        # Since we default to ON, we need to set proper initial height
        self.ignore_widget.setMaximumHeight(36) # Default expanded height
        self.ignore_widget.setMinimumHeight(0)
        self.ignore_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        layout.addWidget(self.ignore_widget)
        
        # Recent Folders
        self.recent_widget = RecentFoldersWidget()
        self.recent_widget.set_folders(load_recent())
        self.recent_widget.folderClicked.connect(self.on_folder_ready)
        layout.addWidget(self.recent_widget)
        
        layout.addSpacing(8)
        
        # Start Scan Button (Bottom Right)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_start = QPushButton("Start Scan")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedWidth(120)
        self.btn_start.setFixedHeight(36)
        self.btn_start.setEnabled(False) # Disabled initially
        
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            QPushButton:pressed {
                background-color: #0056B3;
            }
            QPushButton:disabled {
                background-color: #E5E7EB;
                color: #9CA3AF;
            }
        """)
        self.btn_start.clicked.connect(self.start_scan_action)
        
        btn_layout.addWidget(self.btn_start)
        layout.addLayout(btn_layout)
        
        layout.addStretch(1)
        
        self.stack.addWidget(self.home_page)
        
        # State for pending scan
        self.pending_path = None

    def on_folder_ready(self, path):
        """Called when folder is dropped, selected, or loaded from recent."""
        
        # CRITICAL: Stop any running/paused scan first
        if hasattr(self, 'scan_thread') and self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop_requested = True
            self.scan_thread.stop_event.set()
            self.scan_thread.pause_event.set()  # unblock if paused 
            self.scan_thread.wait() # Ensure it's dead
            self.scan_thread = None
            
        # Reset UI Control States (Button text, etc.)
        self.btn_start.setText("Start Scan")
        self.drop_zone.stop_scan_loader() # Clear any frozen progress bar state
        
        self.pending_path = path
        
        if path:
            # Update recent folders immediately when folder is loaded
            recent = add_recent(path)
            self.recent_widget.set_folders(recent)
            
            # Enable scan button
            self.btn_start.setEnabled(True)
            
            # Show loaded state in drop zone
            self.drop_zone.set_loaded(path) # Ensure visual feedback with full path
        else:
            # Handle Removal / Clear
            self.btn_start.setEnabled(False)
            # Guard against recursion: Only clear if not already cleared
            if self.drop_zone.is_loaded:
                self.drop_zone.clear_loaded()
                
            self.current_data = None # Clear cached data on removal
            self.tree.clear()

    def start_scan_action(self):
        """Triggered by button click - Supports Pause/Resume"""
        # If currently scanning, handle Pause/Resume
        if hasattr(self, 'scan_thread') and self.scan_thread and self.scan_thread.isRunning():
            if self.scan_thread.is_paused():
                self.scan_thread.resume()
                self.btn_start.setText("Pause")
                self.drop_zone.set_status_text("Resuming...")
                self.drop_zone.setEnabled(False) # Lock UI
            else:
                self.scan_thread.pause()
                self.btn_start.setText("Resume")
                self.drop_zone.set_status_text("Paused - You can remove folder")
                self.drop_zone.setEnabled(True) # Unlock UI so user can click 'X'
            return

        # Normal Start
        if self.pending_path:
             # Check for Smart Cache (Persist Session)
            if self.current_data and self.current_data.get('path') == os.path.abspath(self.pending_path):
                 # Reuse existing data without rescan
                 self.stack.setCurrentWidget(self.result_page)
                 
                 # Logic to restore tree size/scroll if needed?
                 self.animate_resize(*self.SIZE_RESULT, callback=lambda: self.unlock_window(min_width=620, min_height=480))
                 return

            self.start_scan(self.pending_path)

    def init_result_view(self):
        self.result_page = QWidget()
        layout = QVBoxLayout(self.result_page)
        layout.setContentsMargins(12, 12, 12, 10)
        
        # Header
        # Header (Explorer Toolbar Style)
        from PyQt5.QtWidgets import QFrame
        header_container = QFrame()
        header_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px; /* Smooth container rounding */
            }
        """)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(6, 6, 6, 6)
        header_layout.setSpacing(8)
        
        # Back Button (Minimal)
        back_btn = QPushButton()
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedSize(32, 32)
        back_btn.setToolTip("Back to Home")
        
        back_icon_path = resource_path("assets/left-arrow.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16)) # Use 16-20px for toolbar icons
        else:
            back_btn.setText("←") # Fallback
            
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px; /* Subtle hover shape */
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
            QPushButton:pressed { background-color: #E5E7EB; }
        """)
        back_btn.clicked.connect(self.go_home)
        
        # Refresh Button
        self.btn_refresh = QPushButton()
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setFixedSize(32, 32)
        self.btn_refresh.setToolTip("Refresh Folder")
        
        refresh_icon_path = resource_path("assets/refresh.png")
        if os.path.exists(refresh_icon_path):
            self.btn_refresh.setIcon(QIcon(refresh_icon_path))
            self.btn_refresh.setIconSize(QSize(18, 18))
        else:
            self.btn_refresh.setText("⟳") # Fallback
            
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #F3F4F6; }
            QPushButton:pressed { background-color: #E5E7EB; }
        """)
        self.btn_refresh.clicked.connect(self.reload_scan)
        
        # Address Bar (Path)
        self.path_bar = AddressBar("/path/to/project")
        self.path_bar.setReadOnly(False) # Editable for user interaction
        self.path_bar.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 4px; /* Rectangular but soft, like Windows address bar */
                padding: 4px 10px;
                font-family: 'Segoe UI', monospace;
                font-size: 13px;
                color: #374151;
            }
            QLineEdit:hover { border-color: #D1D5DB; }
            QLineEdit:focus { 
                border: 1px solid #E5E7EB;
                border-bottom: 2px solid #007AFF; 
            }
            QLineEdit::selection {
                background-color: #0078D7; /* Windows Blue selection */
                color: #FFFFFF;
            }
        """)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setFixedWidth(240) 
        self.search_bar.setClearButtonEnabled(False) # Disable native, use custom
        
        # Actions Setup (Order matters for visual stacking)
        # We want: [ Text ... (Clear) (Search) ]
        # For TrailingPosition: First added is usually Rightmost? Or inner?
        # PyQt behaviour: Actions are stacked. Let's add Search (Permanent) first, then Clear (Conditional).
        
        # 1. Search Icon (Rightmost)
        search_icon_path = resource_path("assets/search.png")
        if os.path.exists(search_icon_path):
            self.search_bar.addAction(QIcon(search_icon_path), QLineEdit.TrailingPosition)
            
        # 2. Custom Clear Action (Left of search icon)
        clear_icon_path = resource_path("assets/clear.png")
        self.act_clear = QAction(self.search_bar)
        if os.path.exists(clear_icon_path):
            # Resize icon to standard toolbar size (16x16) for crisp look
            pix = QPixmap(clear_icon_path)
            scaled = pix.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.act_clear.setIcon(QIcon(scaled))
        else:
            self.act_clear.setText("✕")
        
        self.act_clear.triggered.connect(self.search_bar.clear)
        self.search_bar.addAction(self.act_clear, QLineEdit.TrailingPosition)
        self.act_clear.setVisible(False) # Ensure hidden initially THIS IS CRITICAL

        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E5E7EB;
                border-radius: 4px; 
                padding-top: 5px;
                padding-bottom: 5px;
                padding-left: 10px; 
                padding-right: 50px; /* Space for TWO icons */
                background-color: #FFFFFF;
                font-size: 13px;
                color: #111827;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #E5E7EB; 
                border-bottom: 2px solid #007AFF; 
                background-color: #FFFFFF;
            }
        """)
        
        def on_search_changed(text):
            self.tree.filter_items(text)
            self.act_clear.setVisible(bool(text))
            
        self.search_bar.textChanged.connect(on_search_changed)
        
        # Add to Layout
        header_layout.addWidget(back_btn)
        header_layout.addWidget(self.btn_refresh)
        header_layout.addWidget(self.path_bar, 1) # Expand address bar
        header_layout.addWidget(self.search_bar)
        
        layout.addWidget(header_container)
        
        # --- Content Area with Splitter (VS Code-like layout) ---
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.content_splitter.setHandleWidth(1)
        self.content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E5E7EB;
            }
            QSplitter::handle:hover {
                background-color: #007AFF;
            }
        """)
        
        # Left Panel: Tree View (Sidebar)
        tree_container = QFrame()
        tree_container.setProperty("class", "section")
        
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(0)
        
        # Content (Tree)
        self.tree = FileTreeWidget()
        self.tree.filePreviewRequested.connect(self.preview_in_canvas)
        tree_layout.addWidget(self.tree)
        
        # Right Panel: Canvas Preview (VS Code-like editor)
        preview_container = QFrame()
        preview_container.setProperty("class", "section")
        
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0) # Content sits flush inside the border
        preview_layout.setSpacing(0)
        
        self.canvas_preview = CanvasPreview()
        preview_layout.addWidget(self.canvas_preview)
        
        # Add panels to splitter
        self.content_splitter.addWidget(tree_container)
        self.content_splitter.addWidget(preview_container)
        
        # Set initial sizes (40% tree, 60% canvas)
        self.content_splitter.setSizes([140, 420])
        
        # Add splitter with stretch to fill available space
        layout.addWidget(self.content_splitter, 1)  # stretch=1 to fill height
        
        # Guide Label (Placed above the export bar border)
        lbl_guide = QLabel("Select export formats (Multiple selection allowed)")
        lbl_guide.setStyleSheet("font-size: 13px; font-weight: 500; color: #6B7280; margin-left: 12px; margin-bottom: 2px;")

        # --- Export Action Bar (Bottom) ---
        export_container = QFrame()
        export_container.setFixedHeight(72)
        export_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        
        # Main Layout for Bar
        bar_layout = QHBoxLayout(export_container)
        bar_layout.setContentsMargins(24, 12, 24, 12)
        bar_layout.setSpacing(12)
        
        # Label
        lbl_format = QLabel("Format:")
        lbl_format.setStyleSheet("font-size: 13px; font-weight: 600; color: #6B7280; border: none;")
        bar_layout.addWidget(lbl_format)
        
        # Toggle Chips Logic
        self.export_buttons = {}
        
        def create_chip(text, item_id):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F3F4F6;
                    border: 1px solid #E5E7EB;
                    border-radius: 16px;
                    padding: 0px 16px;
                    color: #374151;
                    font-weight: 500;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                    border-color: #D1D5DB;
                }
                QPushButton:checked {
                    background-color: #EFF6FF;
                    border: 1px solid #3B82F6;
                    color: #1D4ED8;
                    font-weight: 600;
                }
            """)
            self.export_buttons[item_id] = btn
            return btn

        # Create Options
        btn_full = create_chip("Full Structure", "txt_full")
        btn_tree = create_chip("Tree Only", "txt_tree")
        btn_json = create_chip("JSON", "json")
        btn_pdf = create_chip("PDF", "pdf")
        
        # Defaults
        btn_full.setChecked(True)
        
        bar_layout.addWidget(btn_full)
        bar_layout.addWidget(btn_tree)
        bar_layout.addWidget(btn_json)
        bar_layout.addWidget(btn_pdf)
        
        # Spacer
        bar_layout.addStretch()
        
        # "Token Estimate" dropdown button - Modularized
        from src.frontend.components.token_estimate_button import TokenEstimateButton
        self.token_btn = TokenEstimateButton(
            parent=export_container,
            data_getter=lambda: self.current_data,
            format_getter=self.get_selected_export_formats
        )
        bar_layout.addWidget(self.token_btn)
        
        # Connect Toggles to Live Update
        for btn in self.export_buttons.values():
            btn.toggled.connect(lambda: self.token_btn.update_estimate())
        
        # Spacer padding
        bar_layout.addSpacing(12)

        # Export Button (Right)
        export_btn = QPushButton("Export Files")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setFixedSize(140, 40)
        
        export_icon_path = resource_path("assets/export.png")
        if os.path.exists(export_icon_path):
            export_btn.setIcon(QIcon(export_icon_path))
            export_btn.setIconSize(QSize(18, 18))

        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                padding-left: 20px;
                padding-right: 20px;
                border: none;
            }
            QPushButton:hover { background-color: #0069D9; }
            QPushButton:pressed { background-color: #0056B3; }
        """)
        export_btn.clicked.connect(self.export_current_data)
        
        bar_layout.addWidget(export_btn)
        
        layout.addWidget(lbl_guide)
        layout.addWidget(export_container)
        

        
        self.stack.addWidget(self.result_page)

    def browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if path:
            self.on_folder_ready(path)

    def get_abs_path_from_node(self, node_or_path):
        """
        Convert any node/path input into a valid absolute filesystem path.
        This is the ONLY function allowed to touch OS paths.
        """

        if not node_or_path:
            return None

        # Case 1: full node dict
        if isinstance(node_or_path, dict):
            rel_path = node_or_path.get("path")
        else:
            rel_path = node_or_path

        if not rel_path:
            return None

        # Already absolute (safety)
        if os.path.isabs(rel_path):
            return os.path.normpath(rel_path)

        # Root folder itself
        if not self.selected_folder_path:
            return None

        abs_path = os.path.normpath(
            os.path.join(self.selected_folder_path, rel_path)
        )

        return abs_path

    def reveal_in_explorer(self, node_or_path):
        abs_path = self.get_abs_path_from_node(node_or_path)

        if not abs_path:
            QMessageBox.warning(self, "Not Found", "Invalid path.")
            return

        if not os.path.exists(abs_path):
            QMessageBox.warning(
                self,
                "Not Found",
                f"Path does not exist:\n{abs_path}"
            )
            return

        try:
            if platform.system() == "Windows":
                if os.path.isdir(abs_path):
                    subprocess.Popen(["explorer", abs_path])
                else:
                    subprocess.Popen(
                        ["explorer", "/select,", abs_path]
                    )

            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", abs_path])

            else:
                folder = abs_path if os.path.isdir(abs_path) else os.path.dirname(abs_path)
                subprocess.Popen(["xdg-open", folder])

        except Exception as e:
            QMessageBox.critical(self, "Reveal Failed", str(e))
            
    def open_file_external(self, node_or_path):
        abs_path = self.get_abs_path_from_node(node_or_path)

        if not abs_path or not os.path.exists(abs_path):
            QMessageBox.warning(self, "Not Found", "File does not exist.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(abs_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", abs_path])
            else:
                subprocess.Popen(["xdg-open", abs_path])
        except Exception as e:
            QMessageBox.critical(self, "Open Failed", str(e))

    # preview_file_internal removed as it is legacy code replaced by canvas_preview

    def preview_in_canvas(self, file_node):
        """
        Preview file content in the canvas panel (VS Code-like).
        This is called when a file is clicked in the tree.
        """
        if not file_node:
            self.canvas_preview.show_empty()
            return
        
        abs_path = self.get_abs_path_from_node(file_node)
        self.canvas_preview.preview_file(file_node, abs_path)
        
        # Start watching this file for content changes
        if abs_path:
            self.watcher.watch_file(abs_path)

    def start_scan_loader(self):
        self.drop_zone.start_scan_loader()

    def stop_scan_loader(self):
        self.drop_zone.stop_scan_loader()

    def start_scan(self, path):
        if not path:
            # Cleared state
            self.selected_folder_path = None
            return

        self.selected_folder_path = path

        self.drop_zone.setEnabled(False)
        self.start_scan_loader()
        
        self.path_bar.setText(path)
        self.path_bar.setCursorPosition(0) # Reset scroll code? No simply show start.
        
        # Prepare ignore manager (Ensure patterns are fresh if modified recently)
        # In this architecture, ignore_manager tracks its own state, so we just pass it.
        # Use simple pattern refresh if needed, but manager.user_patterns is live.
        self.ignore_manager.load_patterns() # Reload just in case external edit happened? Optional.
        
        # Threading
        self.scan_thread = ScanThread(path, self.ignore_manager)
        self.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.scan_thread.progress_update.connect(self.on_scan_progress)
        self.scan_thread.start()
        
        # Update Button to Pause Mode
        self.btn_start.setEnabled(True) # Keep enabled for Pause action
        self.btn_start.setText("Pause")

    def on_scan_progress(self, current, total):
        self.drop_zone.set_scan_progress(current, total)

    def on_scan_finished(self, data):
        self.current_data = data
        self.tree.populate(data)
        
        # Start watching the project root
        if self.selected_folder_path:
            self.watcher.start_watching_project(self.selected_folder_path)
        
        if 'name' in data:
             self.search_bar.setPlaceholderText(f"Search {data['name']}")
        
        # Reset Home State
        self.drop_zone.setEnabled(True)
        self.stop_scan_loader()
        self.btn_start.setText("Start Scan") # Reset button text
        
        # Switch View FIRST (before animation starts)
        self.stack.setCurrentWidget(self.result_page)
        
        # Smart resize for tree view + Unlock (animate AFTER view switch)
        self.animate_resize(*self.SIZE_RESULT, callback=lambda: self.unlock_window(min_width=620, min_height=480))

        # Trigger initial estimate
        self.token_btn.update_estimate()

    def go_home(self):
        self.stack.setCurrentWidget(self.home_page)
        # self.current_data = None  <-- REMOVED to persist session
        # self.tree.clear()         <-- REMOVED to persist session
        
        # Restore loaded state if folder is still selected
        if self.selected_folder_path:
            self.drop_zone.set_loaded(self.selected_folder_path)
        else:
            self.drop_zone.clear_loaded()

        # Respect current toggle state for height
        target_height = self.HOME_HEIGHT_ADV if self.home_advanced_enabled else self.HOME_HEIGHT
        self.animate_resize(self.HOME_WIDTH, target_height, lock_after=True)

    def toggle_advanced_ignore(self, checked):
        if checked == self.home_advanced_enabled:
            return

        self.home_advanced_enabled = checked
        
        # 1. Animate Widget Height (Smooth content reveal)
        self.animate_advanced_panel(checked) 
        
        # 2. Animate Window Height (Smooth container expansion)
        target_height = self.HOME_HEIGHT_ADV if checked else self.HOME_HEIGHT
        
        # We must maintain current position and width
        current_rect = self.geometry()
        target_rect = QRect(
            current_rect.x(), 
            current_rect.y(), 
            self.HOME_WIDTH, 
            target_height
        )
        
        
        # 🔒 LOCK WIDTH STRICTLY
        # Do NOT use _clear_size_constraints() here because it unlocks width.
        # We want to allow HEIGHT change, but FORBID WIDTH change.
        self.setFixedWidth(self.HOME_WIDTH)
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        
        self.animate_window(target_rect, on_finished=lambda: self.setFixedSize(self.HOME_WIDTH, target_height))

    def export_current_data(self):
        if not self.current_data:
            return
            
        formats = []
        if self.export_buttons["txt_full"].isChecked(): formats.append("txt_full")
        if self.export_buttons["txt_tree"].isChecked(): formats.append("txt_tree")
        if self.export_buttons["json"].isChecked(): formats.append("json")
        if self.export_buttons["pdf"].isChecked(): formats.append("pdf")
        
        if not formats:
            QMessageBox.warning(self, "No Format Selected", "Please select at least one export format.")
            return

        target_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if target_dir:
            # Check for large project
            # Check for large project
            # Stats are now centrally populated by scanner
            total_files = self.current_data.get('stats', {}).get('files', 0)

            if total_files > 3000:
                reply = QMessageBox.question(
                    self, 
                    "Large Export Warning", 
                    f"You are about to export {total_files:,} files.\nThis might take a while. Continue?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # Show progress feedback for large exports
            self.setCursor(Qt.WaitCursor)
            QApplication.processEvents()  # Ensure cursor updates
            
            try:
                files = export_data(self.current_data, target_dir, formats)
                
                self.unsetCursor()
                
                if files:
                    # Success Dialog
                    from src.frontend.components.dialogs.export_result_dialog import ExportResultDialog
                    dialog = ExportResultDialog(target_dir, self)
                    dialog.exec_()
                else:
                    QMessageBox.warning(self, "Export Warning", "No files were exported.")
                
            except Exception as e:
                self.unsetCursor()
                # Show detailed error for debugging
                error_msg = str(e)
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "..."
                QMessageBox.critical(
                    self, 
                    "Export Error", 
                    f"Export failed:\n\n{error_msg}\n\nTip: For very large projects, try exporting Tree/Text only."
                )

    def reload_scan(self):
        """Re-scan the currently selected folder without changing view"""
        if not self.selected_folder_path:
            return
            
        # UI Feedback
        self.tree.setDisabled(True)
        self.btn_refresh.setDisabled(True)
        self.setCursor(Qt.WaitCursor)
        
        # Create new scan thread
        self.scan_thread = ScanThread(self.selected_folder_path, self.ignore_manager)
        
        def on_reload_finished(data):
            self.current_data = data
            self.tree.populate(data)
            self.tree.setDisabled(False)
            self.btn_refresh.setDisabled(False)
            self.unsetCursor()
            
            # Re-apply filter if search text exists
            search_text = self.search_bar.text()
            if search_text:
                self.tree.filter_items(search_text)
            
            # Update estimate on reload
            self.token_btn.update_estimate()
                
        self.scan_thread.scan_finished.connect(on_reload_finished)
        self.scan_thread.start()

    def preview_file(self, path):
        """Open file in default system application"""
        if not os.path.exists(path):
            return
            
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as e:
            print(f"Error opening file: {e}")

    def export_folder(self, abs_path, tree_only=False):
        """Export a specific sub-folder"""
        if not os.path.exists(abs_path):
            return

        target_dir = QFileDialog.getExistingDirectory(self, f"Select Export Directory for '{os.path.basename(abs_path)}'")
        if not target_dir:
            return

        # We need to scan just this folder to get its structure
        self.setCursor(Qt.WaitCursor)
        
        # NOTE: We run this synchronously for simplicity since it's a sub-folder export, 
        # or we could use another thread. For now, sync is acceptable for a "Save As" type action 
        # unless folder is huge. Let's reuse scan logic but possibly sync or quick thread.
        # To match architecture, let's just do it directly if we trust scanner is fast enough,
        # or spin a thread if we want to be safe. 
        # Given "safe, fast, predictable" goal, let's use a quick local scanner call.
        
        try:
            # Re-import here to avoid circularity if any, though likely fine at top
            from src.backend.scanner import scan_directory_structure
            
            sub_data = scan_directory_structure(abs_path, self.ignore_manager)
            
            formats = ["txt_tree"] if tree_only else ["txt_full"]
            # If user wants customized "Tree + Code", maybe they want JSON/PDF too?
            # The prompt says: "Tree Only" vs "Tree + Code".
            # "Tree + Code" implies likely the standard full text dump.
            
            files = export_data(sub_data, target_dir, formats)
            self.unsetCursor()
            
            # New Custom Dialog
            from src.frontend.components.dialogs.export_result_dialog import ExportResultDialog
            dialog = ExportResultDialog(target_dir, self)
            dialog.exec_()
                
        except Exception as e:
            self.unsetCursor()
            QMessageBox.critical(self, "Export Error", str(e))

    def get_selected_export_formats(self):
        """Helper to get currently selected export formats for token estimation."""
        if not hasattr(self, 'export_buttons'): 
            return []
        
        formats = []
        # Check keys against the IDs defined in create_chip
        if self.export_buttons.get("txt_full") and self.export_buttons["txt_full"].isChecked(): 
            formats.append("txt_full")
        if self.export_buttons.get("txt_tree") and self.export_buttons["txt_tree"].isChecked(): 
            formats.append("txt_tree")
        if self.export_buttons.get("json") and self.export_buttons["json"].isChecked(): 
            formats.append("json")
        if self.export_buttons.get("pdf") and self.export_buttons["pdf"].isChecked(): 
            formats.append("pdf")
            
        return formats

    def _build_more_menu(self):
        """Build the 'More' dropdown menu with About option."""
        from PyQt5.QtWidgets import QMenu
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor
        
        more_menu = QMenu(self)
        more_menu.setFixedWidth(140)
        
        # Transparent background for rounded corners to work
        more_menu.setAttribute(Qt.WA_TranslucentBackground)
        more_menu.setWindowFlags(more_menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        
        more_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 4px 0;
                margin: 0px; /* Important for no shadow overlap */
            }
            QMenu::item {
                padding: 8px 12px; /* Reduced padding for better alignment */
                color: #374151;
                font-size: 13px;
                font-weight: 500;
                border-radius: 4px; /* Rounded highlight */
                margin: 2px 4px; /* Space for rounded highlight */
            }
            QMenu::item:selected {
                background-color: #F3F4F6;
                color: #111827;
            }
            QMenu::icon {
                padding-left: 4px;
            }
        """)
        
        # About Action
        about_action = more_menu.addAction("About")
        about_icon_path = resource_path("assets/information.png")
        if os.path.exists(about_icon_path):
            about_action.setIcon(QIcon(about_icon_path))
        about_action.triggered.connect(self._show_about_dialog)
        
        self.btn_more.setMenu(more_menu)

    def _show_about_dialog(self):
        """Show the About dialog with app information."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("About")
        dialog.setFixedWidth(340) # Slightly wider
        # Remove fixed height to allow content to fit
        
        # Proper window flags for clean dialog
        dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 32, 24, 24)
        layout.setSpacing(16)
        
        # Ensure dialog background is white
        dialog.setStyleSheet("QDialog { background-color: white; }")
        
        # App Icon
        icon_label = QLabel()
        icon_path = resource_path("assets/app_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_label)
        
        # Container for text to ensure proper spacing
        text_container = QVBoxLayout()
        text_container.setSpacing(4)
        
        # App Name
        name_label = QLabel("DropDeep")
        name_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #111827; background: transparent; border: none;")
        name_label.setAlignment(Qt.AlignCenter)
        text_container.addWidget(name_label)
        
        # Version
        version_label = QLabel("Version 1.0.0")
        version_label.setStyleSheet("font-size: 13px; color: #6B7280; background: transparent; border: none;")
        version_label.setAlignment(Qt.AlignCenter)
        text_container.addWidget(version_label)
        
        layout.addLayout(text_container)
        
        # Description
        desc_label = QLabel("A powerful tool to scan, visualize, and export\nproject directory structures for LLM context.")
        desc_label.setStyleSheet("font-size: 13px; color: #4B5563; line-height: 1.4; background: transparent; border: none;")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addSpacing(8)
        
        # Developer
        dev_label = QLabel("Developed by Abdulkarim")
        dev_label.setStyleSheet("font-size: 11px; color: #9CA3AF; font-weight: 600; background: transparent; border: none;")
        dev_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_label)
        
        layout.addStretch()
        
        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(90, 36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def on_file_changed(self, path):
        """Handle external file changes."""
        # Update Canvas Content if open
        # We need to detect if it's a file we can read text from or just reload image
        try:
             # Check if it's currently open in canvas before reading
            if path in self.canvas_preview.open_files:
                # If image, we don't need to read content
                if any(path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp']):
                    self.canvas_preview.reload_file_content(path)
                else:
                    # Text file
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.canvas_preview.reload_file_content(path, content)
                    except UnicodeDecodeError:
                        pass # Binary file?
        except Exception as e:
            print(f"Error reading changed file {path}: {e}")

    def on_directory_changed(self, path):
        """Handle external directory structure changes."""
        self.quiet_reload_scan()

    def quiet_reload_scan(self):
        """Re-scan without blocking UI (for auto-updates)."""
        if not self.selected_folder_path:
            return
            
        # Avoid overlapping scans or interrupting active user scan
        if self.scan_thread and self.scan_thread.isRunning():
            return
            
        # We use a new thread instance
        self.scan_thread = ScanThread(self.selected_folder_path, self.ignore_manager)
        
        def on_finished(data):
            self.current_data = data
            self.tree.populate(data)
            
            search_text = self.search_bar.text()
            if search_text:
                self.tree.filter_items(search_text)
            
            self.token_btn.update_estimate()
                
        self.scan_thread.scan_finished.connect(on_finished)
        self.scan_thread.start()
