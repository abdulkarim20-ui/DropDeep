import os
import platform
import subprocess

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QIcon

from src.config import resource_path


class ExportResultDialog(QDialog):
    def __init__(self, export_path: str, parent=None):
        super().__init__(parent)
        self.export_path = export_path

        # Window flags (Explorer-style)
        self.setWindowFlags(
            Qt.Dialog |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedSize(360, 200)

        self._build_ui()
        # self._apply_shadow() # Disabled for stability based on previous context, but user requested it. 
        # Actually user explicitly provided code WITH shadow. 
        # I will uncomment it but keep in mind to remove if it crashes.
        self._apply_shadow()

    # ---------------- UI ---------------- #

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")
        # WinUI 3 Style: Clean white with subtle border, no shadow (stability)
        card.setStyleSheet("""
            QFrame#Card {
                background-color: #F3F3F3; /* Windows 11 Mica-like background */
                border-radius: 8px; /* Standard Windows 11 Window Radius */
                border: 1px solid #E5E5E5; 
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Custom Title Bar ---
        title_bar = QFrame()
        title_bar.setFixedHeight(32) # Standard Windows Title Bar Height
        title_bar.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(10)

        # Branding
        brand_icon_label = QLabel()
        brand_path = resource_path("assets/app_icon.png")
        if os.path.exists(brand_path):
            brand_icon_label.setPixmap(QIcon(brand_path).pixmap(16, 16))
        
        brand_title = QLabel("Export Successful")
        brand_title.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            color: #1F1F1F;
        """)

        # Close Button (X)
        btn_x = QPushButton()
        btn_x.setFixedSize(46, 32) # Standard Windows Close Button Size
        btn_x.setCursor(Qt.ArrowCursor) # Standard Windows Close behavior
        close_icon_path = resource_path("assets/close.png")
        if os.path.exists(close_icon_path):
            btn_x.setIcon(QIcon(close_icon_path))
            btn_x.setIconSize(QSize(10, 10))
        
        btn_x.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-top-right-radius: 8px;
            }
            QPushButton:hover {
                background-color: #C42B1C; /* Windows Red */
                icon: none; /* Just color, or keep icon inverted? */
                /* Usually icon turns white. For now simple red hover */
            }
            QPushButton:pressed {
                background-color: #B3271C;
            }
        """)
        btn_x.clicked.connect(self.accept)

        title_layout.addWidget(brand_icon_label)
        title_layout.addWidget(brand_title)
        title_layout.addStretch()
        title_layout.addWidget(btn_x)

        layout.addWidget(title_bar)

        # --- Content Area ---
        content = QFrame()
        content.setStyleSheet("background-color: #FFFFFF; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 24)
        content_layout.setSpacing(24)

        # Message
        msg = QLabel(
            "Your project structure has been exported successfully.\n\n"
            f"<a href='{self.export_path}' style='text-decoration:none; color:#0067C0;'>{self.export_path}</a>"
        )
        msg.setWordWrap(True)
        msg.setTextFormat(Qt.RichText) # Force HTML rendering
        msg.setOpenExternalLinks(True) # Allow clicking local file links
        msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        msg.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #1F1F1F;
                line-height: 1.5;
                border: none;
            }
        """)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_open = QPushButton("Open Folder")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setFixedHeight(32)

        # Remove icon for purer Windows dialog look, or keep it subtle?
        # Windows dialogs usually just text buttons. Keeping clean.
        
        btn_open.setStyleSheet(self._primary_button())
        btn_open.clicked.connect(self._open_folder)

        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFixedHeight(32)
        btn_close.setStyleSheet(self._secondary_button())
        btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(btn_open)
        btn_layout.addSpacing(8)
        btn_layout.addWidget(btn_close)

        content_layout.addWidget(msg)
        content_layout.addStretch()
        content_layout.addLayout(btn_layout)

        layout.addWidget(content)
        root.addWidget(card)

    def _apply_shadow(self):
        # Shadow removed to fix UpdateLayeredWindowIndirect failed crash
        pass

    # ---------------- Actions ---------------- #

    def _open_folder(self):
        if not os.path.exists(self.export_path):
            return
        
        path = os.path.normpath(self.export_path)

        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)

        self.accept()

    # ---------------- Styles ---------------- #

    def _primary_button(self):
        return """
        QPushButton {
            background-color: #0067C0; /* Windows Accent Blue */
            color: white;
            border-radius: 4px; /* Windows Standard */
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            padding: 0 24px;
            border: 1px solid #0067C0;
        }
        QPushButton:hover { background-color: #005A9E; border-color: #005A9E; }
        QPushButton:pressed { background-color: #004C98; border-color: #004C98; }
        """

    def _secondary_button(self):
        return """
        QPushButton {
            background-color: #FFFFFF;
            color: #1F1F1F;
            border-radius: 4px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            padding: 0 24px;
            border: 1px solid #D1D1D1;
        }
        QPushButton:hover { background-color: #FBFBFB; border-color: #C0C0C0; }
        QPushButton:pressed { background-color: #F0F0F0; border-color: #B0B0B0; }
        """

    # ---------------- Dragging ---------------- #

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
