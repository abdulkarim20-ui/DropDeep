import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from src.config import resource_path

class SmartDestinationDialog(QDialog):
    def __init__(self, target_path: str, parent=None):
        super().__init__(parent)
        self.target_path = target_path
        self.remember = False # Result

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 220)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Main Card
        card = QFrame()
        card.setObjectName("SmartCard")
        card.setStyleSheet("""
            QFrame#SmartCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Icon + Title
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_path = resource_path("assets/explore.png") # Reusing explore icon as "location" icon
        if os.path.exists(icon_path):
             icon_lbl.setPixmap(QIcon(icon_path).pixmap(24, 24))
        
        title = QLabel("Smart Destination")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        
        header.addWidget(icon_lbl)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        layout.addSpacing(12)
        
        # Content
        msg = QLabel(
            f"You've exported to this location 5 times in a row.<br><br>"
            f"<span style='color: #6B7280;'>{self.target_path}</span><br><br>"
            "Set this as your <b>default export location</b> for this folder?"
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.4;")
        layout.addWidget(msg)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_no = QPushButton("No, keep asking")
        btn_no.setCursor(Qt.PointingHandCursor)
        btn_no.setFixedHeight(36)
        btn_no.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #4B5563;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-weight: 500;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #F9FAFB; }
        """)
        btn_no.clicked.connect(self.reject)
        
        btn_yes = QPushButton("Yes, save as default")
        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_yes.setFixedHeight(36)
        btn_yes.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #0069D9; }
        """)
        btn_yes.clicked.connect(self.on_yes)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_no)
        btn_layout.addWidget(btn_yes)
        
        layout.addLayout(btn_layout)
        
        root.addWidget(card)

    def on_yes(self):
        self.remember = True
        self.accept()
