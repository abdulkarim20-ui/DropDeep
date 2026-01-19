from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QWidget, QStackedLayout, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QThread, QDateTime, QPropertyAnimation, QRect
from PyQt5.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QColor
import os
import shutil

from src.config import resource_path
from src.backend.analyzers.stats_analyzer import calculate_folder_stats
from src.backend.analyzers.project_identifier import identify_project_type

# --- Helper Thread for Stats ---
class StatsThread(QThread):
    stats_ready = pyqtSignal(dict) # stats dict
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        
    def run(self):
        stats = calculate_folder_stats(self.path)
        self.stats_ready.emit(stats)

# --- Component: Empty State (Drag & Drop) ---
class EmptyDropWidget(QFrame):
    button_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("EmptyDrop")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(12)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # 1. Icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")
        
        # Blue Folder Icon for Upload State (as per image)
        icon_path = resource_path("assets/drag_icon.png")
        if not os.path.exists(icon_path):
             icon_path = resource_path("assets/folder1.png") # Fallback
             
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
            
        # 2. Text
        self.text_label = QLabel("Drop a repository or project folder\nhere to get started.")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: #374151; font-weight: 700; font-size: 14px; background: transparent;")
        
        # 3. Separator
        sep_layout = QHBoxLayout()
        sep_layout.setSpacing(16)
        sep_layout.setContentsMargins(0, 0, 0, 0)
        
        frame1 = QFrame()
        frame1.setFrameShape(QFrame.HLine)
        frame1.setStyleSheet("background-color: #E5E7EB; border: none; min-height: 1px; max-height: 1px;")
        
        or_label = QLabel("OR")
        or_label.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600; background: transparent;")
        
        frame2 = QFrame()
        frame2.setFrameShape(QFrame.HLine)
        frame2.setStyleSheet("background-color: #E5E7EB; border: none; min-height: 1px; max-height: 1px;")
        
        sep_layout.addWidget(frame1, 1, Qt.AlignVCenter)
        sep_layout.addWidget(or_label, 0, Qt.AlignVCenter)
        sep_layout.addWidget(frame2, 1, Qt.AlignVCenter)
        
        # 4. Button
        self.select_btn = QPushButton("Select folder")
        self.select_btn.setCursor(Qt.PointingHandCursor)
        self.select_btn.setFixedSize(140, 38)
        self.select_btn.clicked.connect(self.button_clicked.emit)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            QPushButton:pressed {
                background-color: #0056B3;
            }
        """)

        # Assemble
        self.layout.addStretch()
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label)
        self.layout.addSpacing(4)
        self.layout.addLayout(sep_layout)
        self.layout.addSpacing(4)
        self.layout.addWidget(self.select_btn, 0, Qt.AlignCenter)
        self.layout.addStretch()
        
        self.update_style(hover=False)

    def set_hover(self, hover):
        self.update_style(hover)

    def update_style(self, hover):
        if hover:
            self.setStyleSheet("""
                #EmptyDrop {
                    background-color: #F0F9FF;
                    border: 2px dashed #007AFF;
                    border-radius: 16px;
                }
            """)
        else:
            self.setStyleSheet("""
                #EmptyDrop {
                    background-color: #FFFFFF;
                    border: 2px dashed #E5E7EB;
                    border-radius: 16px;
                }
            """)

# --- Component: Loaded State (Card) ---
class LoadedCardWidget(QFrame):
    close_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName("LoadedWidget")
        
        # Apply the same "Dashed Box" style as the Empty state
        self.setStyleSheet("""
            #LoadedWidget {
                background-color: #F9FAFB;
                border: 2px dashed #D1D5DB;
                border-radius: 16px;
            }
        """)
        
        # Center the card in the available space
        self.container_layout = QVBoxLayout(self)
        self.container_layout.setContentsMargins(16, 16, 16, 16)
        self.container_layout.setAlignment(Qt.AlignCenter)
        
        # --- The Card Box ---
        self.card = QFrame()
        self.card.setObjectName("CardBox")
        self.card.setFixedWidth(300) # Fixed width for consistent look
        
        # Card Style matches the image: White/Light Gray bg, Border, Shadow
        self.card.setStyleSheet("""
            #CardBox {
                background-color: #F8FAFC; 
                border: 1px solid #CBD5E1;
                border-radius: 12px;
            }
        """)
        
        # Layout for the Card
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(12, 8, 12, 12) # Tighter margins inside card
        self.card_layout.setSpacing(0)
        
        # 1. Top Row: Close Button (Right Aligned)
        top_row = QHBoxLayout()
        top_row.addStretch()
        
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        self.close_btn.setText("✕") # Using text as per probable reference, or fallback to icon
        
        # Check for icon, but text 'x' often looks cleaner if font matches
        # Let's try to use the icon if it exists for consistency, but style it simple
        close_icon = resource_path("assets/close.png")
        if os.path.exists(close_icon):
            self.close_btn.setIcon(QIcon(close_icon))
            self.close_btn.setIconSize(QSize(10, 10))
            self.close_btn.setText("")
            
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #64748B;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: #EF4444;
                background-color: #fee2e2;
            }
        """)
        
        top_row.addWidget(self.close_btn)
        self.card_layout.addLayout(top_row)
        
        # 2. Content Row (Icon + Text)
        content_row = QHBoxLayout()
        content_row.setSpacing(16)
        content_row.setContentsMargins(4, 0, 4, 4) # Padding around content
        
        # Icon Container
        self.icon_container = QLabel()
        self.icon_container.setFixedSize(64, 64)
        self.icon_container.setStyleSheet("""
            background-color: #DBEAFE;
            border-radius: 12px;
            border: 1px solid #BFDBFE;
        """)
        self.icon_container.setAlignment(Qt.AlignCenter)
        
        # Folder Icon
        icon_path = resource_path("assets/drag_icon_load.png")
        if not os.path.exists(icon_path):
            icon_path = resource_path("assets/folder1.png")
            
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_container.setPixmap(pix)
        else:
            self.icon_container.setText("📁")
            
        content_row.addWidget(self.icon_container)
        
        # Text Column
        self.text_col = QVBoxLayout()
        self.text_col.setSpacing(4)
        self.text_col.setAlignment(Qt.AlignVCenter)
        
        # Row 1: Name + Badge
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        
        self.name_label = QLabel("Project")
        self.name_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A; background: transparent;")
        
        self.badge = QLabel("Python")
        self.badge.setStyleSheet("""
            background-color: #2563EB; 
            color: white; 
            font-size: 10px; 
            font-weight: 600; 
            padding: 2px 6px; 
            border-radius: 4px;
        """)
        self.badge.setFixedHeight(18)
        
        name_row.addWidget(self.name_label)
        name_row.addWidget(self.badge)
        name_row.addStretch()
        
        self.text_col.addLayout(name_row)
        
        # Row 2: Stats
        self.stats_label = QLabel("...")
        self.stats_label.setStyleSheet("color: #64748B; font-size: 12px; background: transparent;")
        self.text_col.addWidget(self.stats_label)
        
        # Row 3: Status
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #10B981; font-size: 10px; background: transparent;")
        
        self.status_text = QLabel("Ready to Scan")
        self.status_text.setStyleSheet("color: #10B981; font-weight: 600; font-size: 12px; background: transparent;")
        
        self.time_label = QLabel("• Ready")
        self.time_label.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent;")
        
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_text)
        status_row.addWidget(self.time_label)
        status_row.addStretch()
        
        self.text_col.addLayout(status_row)
        
        content_row.addLayout(self.text_col)
        content_row.addStretch() 
        
        self.card_layout.addLayout(content_row)
        
        # Add Card to Main Container
        self.container_layout.addWidget(self.card)

        # --- Modern Slim Loader (Inside Card) ---
        self.scan_loader = QFrame()
        self.scan_loader.setFixedHeight(4) # Slightly thinner inside card? Or same 6. Let's stick to 6 but maybe 4 looks better inside. User liked 6.
        self.scan_loader.setVisible(False)
        self.scan_loader.setStyleSheet("""
        QFrame {
            background-color: #E5E7EB;
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        }
        """)
        # Note: If I put it inside card layout, it might mess up padding. 
        # The card has padding.
        # If I want it to be at the very bottom edge of the card, I might need to adjust layout.
        # Let's place it inside card_layout first.
        
        self.scan_loader = QFrame()
        self.scan_loader.setFixedHeight(6)
        self.scan_loader.setVisible(False)
        self.scan_loader.setStyleSheet("""
        QFrame {
            background-color: #E5E7EB;
            border-radius: 3px;
        }
        """)
        
        self.scan_loader_bar = QFrame(self.scan_loader)
        self.scan_loader_bar.setGeometry(0, 0, 0, 6)
        self.scan_loader_bar.setStyleSheet("""
        QFrame {
            background-color: #007AFF;
            border-radius: 3px;
        }
        """)
        
        self.card_layout.addSpacing(10)
        self.card_layout.addWidget(self.scan_loader)

    def start_loader(self):
        self.scan_loader.setVisible(True)
        self.scan_loader_bar.setGeometry(0, 0, 0, 6) # Reset to 0

    def set_progress(self, current, total):
        # Initial calculation state
        if total == 0 and current == 0:
             self.scan_loader.setVisible(True)
             self.status_text.setText("Calculating files...")
             self.scan_loader_bar.setGeometry(0,0,0,6)
             return
             
        if total <= 0:
            return
            
        self.scan_loader.setVisible(True)
        
        # Calculate width
        w = self.scan_loader.width()
        progress = current / total
        bar_w = int(w * progress)
        
        # Smooth update? Direct for now to correspond to real progress
        self.scan_loader_bar.setGeometry(0, 0, bar_w, 6)
        
        # Update text with details
        percent = int(progress * 100)
        self.status_text.setText(f"Scanning... {percent}%")

    def stop_loader(self):
        if hasattr(self, "loader_anim") and self.loader_anim:
            self.loader_anim.stop()
        self.scan_loader.setVisible(False)
        self.status_text.setText("Ready to Scan") # Reset text

    def set_data(self, path):
        # Validate path first
        if not path:
            return
            
        # Ensure we have an absolute path
        if not os.path.isabs(path):
            # If it's a relative path, we can't reliably analyze it
            self.name_label.setText(path)
            self.badge.setText("Invalid Path")
            self.badge.setStyleSheet("""
                background-color: #EF4444; 
                color: white; 
                font-size: 10px; 
                font-weight: 600; 
                padding: 2px 6px; 
                border-radius: 4px;
            """)
            self.stats_label.setText("Path is not absolute")
            return
            
        # Check if path exists
        if not os.path.exists(path):
            self.name_label.setText(os.path.basename(path))
            self.badge.setText("Not Found")
            self.badge.setStyleSheet("""
                background-color: #EF4444; 
                color: white; 
                font-size: 10px; 
                font-weight: 600; 
                padding: 2px 6px; 
                border-radius: 4px;
            """)
            self.stats_label.setText("Path does not exist")
            return
        
        # Valid path - proceed with normal logic
        name = os.path.basename(path)
        self.name_label.setText(name)
        
        # Identify Project Type using new module
        project_info = identify_project_type(path)
        p_name = project_info.get('name', 'Folder')
        p_color = project_info.get('color', '#6B7280')
        
        self.badge.setText(p_name)
        self.badge.setStyleSheet(f"""
            background-color: {p_color}; 
            color: white; 
            font-size: 10px; 
            font-weight: 600; 
            padding: 2px 6px; 
            border-radius: 4px;
        """)
        
        # Thread for stats
        self.stats_label.setText("Analyzing...")
        self.thread = StatsThread(path)
        self.thread.stats_ready.connect(self.update_stats)
        self.thread.start()
        
        # Update time (mock or real)
        pass # Keep existing logic or simplify
            
    def update_stats(self, stats):
        files = stats.get('files', 0)
        folders = stats.get('folders', 0)
        size_str = stats.get('size_str', '0 B')
        self.stats_label.setText(f"{files} files • {folders} folders • {size_str}")


# --- Main DropZone Class ---
class DropZone(QFrame):
    folderDropped = pyqtSignal(str)
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(332, 260) # Or dynamic? Keeping fixed as per design
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Stacked Layout
        self.stack = QStackedLayout(self)
        self.stack.setStackingMode(QStackedLayout.StackOne)
        
        # 0: Empty
        self.empty_view = EmptyDropWidget()
        self.empty_view.button_clicked.connect(self.clicked.emit) # Forward button click
        self.stack.addWidget(self.empty_view)
        
        # 1: Loaded
        self.loaded_view = LoadedCardWidget()
        self.loaded_view.close_clicked.connect(self.clear_loaded)
        self.stack.addWidget(self.loaded_view)
        
        self.is_loaded = False

    def set_loaded(self, path):
        self.is_loaded = True
        self.stack.setCurrentIndex(1)
        self.loaded_view.set_data(path)
        # We disable drops when loaded usually, or allow replacement
        self.setAcceptDrops(False)
        self.setCursor(Qt.ArrowCursor) # Don't show hand everywhere on card
        
    def clear_loaded(self):
        self.is_loaded = False
        self.stack.setCurrentIndex(0)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Signal parent if needed? 
        # Parent usually monitors start scan availability.
        # We might need to propagate 'cleared' signal if parent buttons rely on it.
        # But parent likely relies on 'folderDropped' to set state.
        # Ideally we emit a 'cleared' signal.
        # For now, if user clicks close, we just reset visual.
        # Parent logic for 'start scan' button enabled/disabled might need update.
        self.folderDropped.emit("") # Emit empty string to signal clear?

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self.is_loaded: 
            event.ignore()
            return
            
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and os.path.isdir(urls[0].toLocalFile()):
                event.accept()
                self.empty_view.set_hover(True)
            else:
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.empty_view.set_hover(False)
        event.accept()

    def dropEvent(self, event: QDropEvent):
        if self.is_loaded:
            return
            
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.folderDropped.emit(path)
                self.set_loaded(path)
        
        self.empty_view.set_hover(False)
        event.accept()

    def mouseReleaseEvent(self, event):
        if not self.is_loaded:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def start_scan_loader(self):
        self.loaded_view.start_loader()
        
    def set_scan_progress(self, current, total):
        self.loaded_view.set_progress(current, total)

    def stop_scan_loader(self):
        self.loaded_view.stop_loader()

    def set_status_text(self, text):
        self.loaded_view.status_text.setText(text)
