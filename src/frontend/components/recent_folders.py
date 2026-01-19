from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal, Qt
from src.frontend.styles.theme import COLOR_PRIMARY
import os

class RecentFoldersWidget(QWidget):
    folderClicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(6)

        label = QLabel("Recent:")
        label.setStyleSheet(
            "font-weight: 600; font-size: 12px; color: #333;"
        )
        layout.addWidget(label)

        self.btn_container = QWidget()
        self.btn_layout = QHBoxLayout(self.btn_container)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_layout.setSpacing(6)

        layout.addWidget(self.btn_container)
        layout.addStretch()

    def set_folders(self, folders):
        # Clear
        while self.btn_layout.count():
            w = self.btn_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        if not folders:
            lbl = QLabel("None")
            lbl.setStyleSheet("font-size: 12px; color: #999;")
            self.btn_layout.addWidget(lbl)
            return

        for i, folder in enumerate(folders):
            name = os.path.basename(folder) or folder

            # Use QLabel as hyperlink with exact same blue as Browse button
            link = QLabel(f"<a href='#' style='text-decoration: none;'>{name}</a>")
            link.setToolTip(folder)
            link.setTextInteractionFlags(Qt.TextBrowserInteraction)
            link.setOpenExternalLinks(False)
            link.setCursor(Qt.PointingHandCursor)
            link.setStyleSheet(f"""
                QLabel {{
                    color: {COLOR_PRIMARY};
                    font-size: 12px;
                    background: transparent;
                }}
                QLabel a {{
                    color: {COLOR_PRIMARY};
                }}
                QLabel a:hover {{
                    text-decoration: underline;
                }}
            """)
            link.linkActivated.connect(lambda _, p=folder: self.folderClicked.emit(p))
            self.btn_layout.addWidget(link)

            if i < len(folders) - 1:
                sep = QLabel("|")
                sep.setStyleSheet("color: #999;")
                self.btn_layout.addWidget(sep)
