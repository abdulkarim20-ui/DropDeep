from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QScrollArea, QWidget, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
import os
from src.frontend.components.flow_layout import FlowLayout
from src.config import resource_path

class PatternChip(QFrame):
    def __init__(self, text, parent=None, callback=None):
        super().__init__(parent)
        self.text = text
        self.callback = callback
        self.setFixedHeight(34)  # Slightly taller for better proportion
        
        # Determine category color based on extension/pattern
        self.bg_color = "#F3F4F6"
        self.text_color = "#374151"
        
        if any(ext in text for ext in ['.zip', '.rar', '.7z', '.tar']):
            self.bg_color = "#FEF2F2"; self.text_color = "#991B1B"
        elif any(ext in text for ext in ['.png', '.jpg', '.mp4', '.gif']):
            self.bg_color = "#EFF6FF"; self.text_color = "#1E40AF"
        elif text.startswith('.') or text in ['node_modules', '__pycache__']:
            self.bg_color = "#F0FDF4"; self.text_color = "#166534"
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.bg_color};
                border: none;
                border-radius: 17px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(8)  # Add spacing between label and button
        
        # Label
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {self.text_color}; font-weight: 700; font-size: 12px; background: transparent; font-family: 'Segoe UI', sans-serif;")
        layout.addWidget(lbl)
        
        # Close Button
        self.btn_close = QPushButton("✕") 
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.text_color};
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(0,0,0,0.1);
            }}
        """)
        self.btn_close.clicked.connect(self.on_remove)
        layout.addWidget(self.btn_close, 0, Qt.AlignVCenter)
        
    def on_remove(self):
        if self.callback:
            self.callback(self.text)

class IgnorePatternsDialog(QDialog):
    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Edit Ignore Patterns")
        self.setFixedSize(540, 500)
        
        self.current_patterns = set(self.manager.get_all_patterns()) if self.manager else set()
        self.original_patterns = self.current_patterns.copy()
        self.search_query = ""
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)
        self.setStyleSheet("background-color: #FFFFFF;")

        # 1. Header with Reset
        header_layout = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title_label = QLabel("Ignore Patterns")
        title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #111827;")
        subtitle_label = QLabel("Files matching these patterns won't be scanned.")
        subtitle_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        title_vbox.addWidget(title_label)
        title_vbox.addWidget(subtitle_label)
        
        self.btn_reset = QPushButton(" Restore Defaults")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        
        # Add reset icon
        reset_icon_path = resource_path("assets/reset.png")
        if os.path.exists(reset_icon_path):
            self.btn_reset.setIcon(QIcon(reset_icon_path))
            self.btn_reset.setIconSize(QSize(14, 14))
        
        self.btn_reset.setStyleSheet("color: #007AFF; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_reset)
        self.layout.addLayout(header_layout)

        # 2. Search & Add Bar
        search_box = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search patterns...")
        self.txt_search.setFixedHeight(38)
        self.txt_search.textChanged.connect(self.on_search_changed)
        
        # Add search icon
        search_icon_path = resource_path("assets/search.png")
        if os.path.exists(search_icon_path):
            search_action = self.txt_search.addAction(QIcon(search_icon_path), QLineEdit.LeadingPosition)
            search_action.triggered.connect(lambda: None)  # Icon only, no action
        
        self.txt_add = QLineEdit()
        self.txt_add.setPlaceholderText("Add new (e.g. *.tmp)")
        self.txt_add.setFixedHeight(38)
        self.txt_add.returnPressed.connect(self.add_pattern)
        
        # Example Label
        lbl_examples = QLabel("Support glob patterns (e.g. *.log, dist/, node_modules)")
        lbl_examples.setStyleSheet("color: #9CA3AF; font-size: 11px; margin-left: 4px;")
        
        input_layout_v = QVBoxLayout()
        input_layout_v.setSpacing(2)
        input_layout_v.addWidget(self.txt_add)
        input_layout_v.addWidget(lbl_examples)
        
        self.btn_add = QPushButton("Add")
        self.btn_add.setFixedSize(60, 38)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self.add_pattern)
        
        input_style = """
            QLineEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding-left: 8px;
                padding-right: 12px;
                background-color: #F9FAFB;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
                background-color: #FFFFFF;
            }
        """
        
        input_style_normal = """
            QLineEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 0 12px;
                background-color: #F9FAFB;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
                background-color: #FFFFFF;
            }
        """
        self.txt_search.setStyleSheet(input_style)  # Has icon padding
        self.txt_add.setStyleSheet(input_style_normal)  # Normal padding
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border-radius: 8px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #0069D9; }
        """)
        
        search_box.addWidget(self.txt_search, 1)
        search_box.addSpacing(8)
        search_box.addLayout(input_layout_v, 1)
        search_box.addWidget(self.btn_add)
        self.layout.addLayout(search_box)

        # 3. Content Area (Categorized)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background-color: #FFFFFF;")
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(20)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        # 4. Footer
        footer = QHBoxLayout()
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setFixedSize(140, 40)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_changes)
        
        self.btn_close = QPushButton("Cancel")
        self.btn_close.setFixedSize(100, 40)
        self.btn_close.clicked.connect(self.reject)
        
        footer.addStretch()
        footer.addWidget(self.btn_close)
        footer.addWidget(self.btn_save)
        self.layout.addLayout(footer)

        self.apply_button_styles()
        self.refresh_ui()

    def apply_button_styles(self):
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border-radius: 10px;
                font-weight: 700;
            }
            QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
        """)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                font-weight: 600;
                color: #374151;
            }
            QPushButton:hover { background-color: #F9FAFB; }
        """)

    def on_search_changed(self, text):
        self.search_query = text.lower()
        self.refresh_ui()

    def get_categorized_patterns(self):
        categories = {
            "System & Config": [],
            "Media & Assets": [],
            "Archives & Binaries": [],
            "Other Patterns": []
        }
        
        for p in sorted(list(self.current_patterns)):
            if self.search_query and self.search_query not in p.lower():
                continue
                
            if any(ext in p for ext in ['.zip', '.rar', '.7z', '.exe', '.dll', '.so']):
                categories["Archives & Binaries"].append(p)
            elif any(ext in p for ext in ['.png', '.jpg', '.mp4', '.gif', '.svg', '.ico']):
                categories["Media & Assets"].append(p)
            elif p.startswith('.') or p in ['node_modules', '__pycache__', 'venv', 'env']:
                categories["System & Config"].append(p)
            else:
                categories["Other Patterns"].append(p)
        return categories

    def refresh_ui(self):
        # Clear container
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        categories = self.get_categorized_patterns()
        
        any_visible = False
        for title, items in categories.items():
            if not items: continue
            any_visible = True
            
            section = QWidget()
            sec_layout = QVBoxLayout(section)
            sec_layout.setContentsMargins(0, 0, 0, 0)
            sec_layout.setSpacing(8)
            
            lbl = QLabel(title)
            lbl.setStyleSheet("font-weight: 700; color: #374151; font-size: 11px; text-transform: uppercase;")
            sec_layout.addWidget(lbl)
            
            flow_container = QWidget()
            flow = FlowLayout(flow_container, spacing=8)
            for p in items:
                flow.addWidget(PatternChip(p, callback=self.remove_pattern))
            
            sec_layout.addWidget(flow_container)
            self.container_layout.addWidget(section)

        if not any_visible:
            empty = QLabel("No patterns found matching your search.")
            empty.setStyleSheet("color: #9CA3AF; font-style: italic; font-size: 13px;")
            empty.setAlignment(Qt.AlignCenter)
            self.container_layout.addWidget(empty)

        self.btn_save.setEnabled(self.current_patterns != self.original_patterns)

    def add_pattern(self):
        txt = self.txt_add.text().strip()
        if txt and txt not in self.current_patterns:
            self.current_patterns.add(txt)
            self.txt_add.clear()
            self.refresh_ui()

    def remove_pattern(self, pattern):
        if pattern in self.current_patterns:
            self.current_patterns.remove(pattern)
            self.refresh_ui()

    def reset_to_defaults(self):
        # Implementation of reset logic
        from src.backend.managers.ignore_manager import DEFAULT_PATTERNS
        self.current_patterns = set(DEFAULT_PATTERNS)
        self.refresh_ui()

    def save_changes(self):
        orig = self.original_patterns
        curr = self.current_patterns
        added = curr - orig
        removed = orig - curr
        
        for p in added: self.manager.add_pattern(p)
        for p in removed: self.manager.remove_pattern(p)
            
        self.original_patterns = self.current_patterns.copy()
        self.btn_save.setEnabled(False)
        self.accept()
