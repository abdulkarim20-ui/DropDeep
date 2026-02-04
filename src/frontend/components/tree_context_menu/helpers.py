import os
import platform
import subprocess
from PyQt5.QtWidgets import QApplication


def copy_text(text: str):
    QApplication.clipboard().setText(text)


def reveal_in_explorer(path: str):
    if not os.path.exists(path):
        return

    if platform.system() == "Windows":
        path = os.path.normpath(path)
        if os.path.isfile(path):
            os.startfile(os.path.dirname(path))
        else:
            os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", "-R", path], check=False)
    else:
        subprocess.run(["xdg-open", os.path.dirname(path)], check=False)


def menu_style():
    return """
    QMenu {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 4px;
        font-size: 13px;
    }
    QMenu::item {
        padding: 6px 30px 6px 12px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #F3F4F6;
    }
    QMenu::separator {
        height: 1px;
        background: #E5E7EB;
        margin: 4px 0;
    }
    """
