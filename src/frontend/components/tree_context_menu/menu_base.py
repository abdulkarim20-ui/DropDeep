from PyQt5.QtWidgets import QMenu, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class ExplorerStyleMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 🔑 Disable native frame
        self.setWindowFlags(
            Qt.Popup |
            Qt.FramelessWindowHint |
            Qt.NoDropShadowWindowHint
        )

        # 🔑 Allow rounded corners
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 🔑 Clean rounded style
        self.setStyleSheet(self._style())

    def _style(self):
        return """
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #D1D5DB; /* Slightly darker border for definition */
            border-radius: 8px; /* Slightly tighter radius */
            padding: 4px;
        }

        QMenu::item {
            padding: 6px 32px 6px 12px;
            border-radius: 4px;
            font-size: 13px;
            color: #1F2937;
        }

        QMenu::item:selected {
            background-color: #F3F4F6;
        }

        QMenu::separator {
            height: 1px;
            background: #E5E7EB;
            margin: 6px 6px;
        }
        """
