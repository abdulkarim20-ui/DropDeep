import sys
import os

# Ensure src can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from src.frontend.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set Metadata
    app.setApplicationName("Crawlsee")
    app.setApplicationVersion("1.0.0")

    # Windows Taskbar Icon Fix
    if sys.platform.startswith("win"):
        try:
            import ctypes
            myappid = 'structurepro.crawlsee.1.0.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # Set App Icon
    from PyQt5.QtGui import QIcon
    from src.config import resource_path
    icon_path = resource_path("assets/app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Launch
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
