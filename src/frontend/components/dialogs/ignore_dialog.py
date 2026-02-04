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
        self.setFixedHeight(30) # Fixed height to prevent 'squeezing'
        
        # Determine category color
        self.bg_color = "#F3F4F6"
        self.text_color = "#4B5563"
        
        if any(ext in text for ext in ['.zip', '.rar', '.7z', '.exe', '.dll']):
            self.bg_color = "#FEE2E2"; self.text_color = "#991B1B"
        elif any(ext in text for ext in ['.png', '.jpg', '.mp4', '.gif', '.svg', '.ico']):
            self.bg_color = "#E0F2FE"; self.text_color = "#0369A1"
        elif text.startswith('.') or text in ['node_modules', '__pycache__', 'venv', 'env', '.git']:
            self.bg_color = "#EEF2FF"; self.text_color = "#4338CA"
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.bg_color};
                border: 1px solid transparent;
                border-radius: 6px;
            }}
            QFrame:hover {{
                border: 1px solid rgba(0,0,0,0.05);
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 4, 0)
        layout.setSpacing(6)
        
        # Label
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {self.text_color}; font-weight: 600; font-size: 13px; background: transparent;")
        layout.addWidget(lbl)
        
        # Close Button (Light Gray, Normal weight)
        self.btn_close = QPushButton("X")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #9CA3AF; /* Light Gray palette */
                border: none;
                font-size: 11px;
                font-weight: 500; /* Normal weight */
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(0,0,0,0.05);
                border-radius: 12px;
                color: #4B5563; /* Darker on hover */
            }}
        """)
        self.btn_close.clicked.connect(self.on_remove)
        layout.addWidget(self.btn_close)
        
    def on_remove(self):
        if self.callback:
            self.callback(self.text)

class IgnorePatternsDialog(QDialog):
    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Edit Ignore Patterns")
        self.setFixedSize(540, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
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
        title_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #1F2937;")
        subtitle_label = QLabel("Files matching these patterns won't be scanned.")
        subtitle_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        title_vbox.addWidget(title_label)
        title_vbox.addWidget(subtitle_label)
        
        self.btn_reset = QPushButton(" Restore Defaults")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setMinimumHeight(30)
        self.btn_reset.setFixedWidth(150) # Increased to prevent clipping
        
        reset_icon_path = resource_path("assets/reset.png")
        if os.path.exists(reset_icon_path):
            self.btn_reset.setIcon(QIcon(reset_icon_path))
            self.btn_reset.setIconSize(QSize(14, 14))
        
        self.btn_reset.setStyleSheet("""
            QPushButton {
                color: #007AFF; 
                font-size: 12px; 
                font-weight: 600; 
                border: 1px solid #DCEAFE; 
                background: #F0F7FF;
                border-radius: 15px;
                padding: 2px 10px;
            }
            QPushButton:hover {
                background: #DCEAFE;
                border-color: #007AFF;
            }
        """)
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_reset, 0, Qt.AlignVCenter)
        self.layout.addLayout(header_layout)

        # 2. Search & Add Bar
        search_add_master = QHBoxLayout()
        search_add_master.setSpacing(16)
        search_add_master.setContentsMargins(0, 0, 0, 0)
        
        # -- Left Column: Search --
        search_col = QVBoxLayout()
        search_col.setSpacing(4)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search...")
        self.txt_search.setFixedHeight(38)
        self.txt_search.setObjectName("searchBar")
        self.txt_search.textChanged.connect(self.on_search_changed)
        
        search_icon_path = resource_path("assets/search.png")
        if os.path.exists(search_icon_path):
            self.txt_search.addAction(QIcon(search_icon_path), QLineEdit.LeadingPosition)
        
        search_col.addWidget(self.txt_search)
        search_col.addStretch() # Aligns search bar to the top matching the add field
        
        # -- Right Column: Add --
        add_col = QVBoxLayout()
        add_col.setSpacing(4)
        
        add_input_row = QHBoxLayout()
        add_input_row.setSpacing(8)
        
        self.txt_add = QLineEdit()
        self.txt_add.setPlaceholderText("Add new (e.g. *.tmp)")
        self.txt_add.setFixedHeight(38)
        self.txt_add.returnPressed.connect(self.add_pattern)
        
        self.btn_add = QPushButton("Add")
        self.btn_add.setFixedSize(65, 38)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self.add_pattern)
        
        add_input_row.addWidget(self.txt_add, 1)
        add_input_row.addWidget(self.btn_add)
        
        lbl_examples = QLabel("Support glob patterns (e.g. *.log, dist/, node_modules)")
        lbl_examples.setStyleSheet("color: #9CA3AF; font-size: 11px; margin-left: 2px;")
        
        add_col.addLayout(add_input_row)
        add_col.addWidget(lbl_examples)
        
        # Unified Styling
        input_style = """
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 0 12px;
                background-color: #F8F9FA;
                font-size: 13px;
                color: #1F2937;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit#searchBar {
                padding-left: 32px;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
                background-color: #FFFFFF;
            }
            QPushButton#addBtn {
                background-color: #007AFF;
                color: white;
                border-radius: 6px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton#addBtn:hover { background-color: #0069D9; }
        """
        self.txt_search.setStyleSheet(input_style)
        self.txt_add.setStyleSheet(input_style)
        self.btn_add.setObjectName("addBtn")
        self.btn_add.setStyleSheet(input_style)
        
        search_add_master.addLayout(search_col, 2)
        search_add_master.addLayout(add_col, 3)
        self.layout.addLayout(search_add_master)

        # 3. Content Area (Categorized)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background-color: #FFFFFF;
                border: none;
            }
            /* VS Code Ultra-Slim Permanent Blue Scrollbar */
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #007AFF;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0069D9;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
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
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
            QPushButton:hover:enabled { background-color: #0069D9; }
        """)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-weight: 500;
                color: #4B5563;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #F9FAFB; border-color: #9CA3AF; }
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
            lbl.setStyleSheet("""
                font-weight: 600; 
                color: #6B7280; 
                font-size: 11px; 
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-top: 4px;
            """)
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
