from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from src.frontend.components.dialogs.ignore_dialog import IgnorePatternsDialog

class AdvancedIgnoreWidget(QWidget):
    patterns_changed = pyqtSignal()
    
    def __init__(self, ignore_manager=None):
        super().__init__()
        self.ignore_manager = ignore_manager
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)
        
        # READ-ONLY Display (Mimicking a text field as requested, or just a nice label box)
        # "in text fked user can see the some ignire pattern by default"
        # Since the list is huge, we can't show all. We'll show a summary or "Standard Patterns + X Custom".
        # Or maybe just a disabled line edit with "Standard Patterns Active..."
        
        self.lbl_display = QLabel()
        self.lbl_display.setFixedHeight(32)
        self.lbl_display.setStyleSheet("""
            QLabel {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 0 12px;
                color: #6B7280;
                font-size: 13px;
            }
        """)
        
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        self.btn_edit.setFixedSize(60, 32)
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-weight: 600;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #9CA3AF;
            }
        """)
        self.btn_edit.clicked.connect(self.open_dialog)
        
        layout.addWidget(self.lbl_display, 1)
        layout.addWidget(self.btn_edit)
        
        self.update_status()

    def set_manager(self, manager):
        self.ignore_manager = manager
        self.update_status()

    def update_status(self):
        if self.ignore_manager:
            count = len(self.ignore_manager.get_all_patterns())
            self.lbl_display.setText(f"{count} Active Patterns (Standard + Custom)")
        else:
            self.lbl_display.setText("Not Loaded")

    def open_dialog(self):
        if not self.ignore_manager:
            return
            
        dialog = IgnorePatternsDialog(self, self.ignore_manager)
        dialog.exec_()
        self.update_status()
        self.patterns_changed.emit()
