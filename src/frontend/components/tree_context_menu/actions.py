from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from src.config import resource_path
from .helpers import copy_text


def icon(name):
    path = resource_path(f"assets/{name}")
    return QIcon(path)


class FileActions:
    def __init__(self, menu, tree, ignore_manager, data):
        self.menu = menu
        self.tree = tree
        self.ignore_manager = ignore_manager
        self.data = data

    def build(self):

        
        self.menu.addAction(
            "Open File",
            lambda: self.tree.open_file_external(self.data)
        )

        self.menu.addAction(
            icon("copy.png"),
            "Copy Relative Path",
            lambda: copy_text(self.data["rel_path"])
        )

        self.menu.addAction(
            icon("copy.png"),
            "Copy Full Path",
            lambda: copy_text(self.data["abs_path"])
        )

        self.menu.addSeparator()

        self.menu.addAction(
            icon("ignore.png"),
            "Ignore This File",
            lambda: self._ignore_and_refresh()
        )

        self.menu.addSeparator()

        self.menu.addAction(
            icon("explore.png"),
            "Reveal in Explorer",
            lambda: self.tree.reveal_in_explorer(self.data)
        )

    def _ignore_and_refresh(self):
        # Add to session pattern (for future scans)
        self.ignore_manager.add_session_pattern(self.data["name"])
        # FAST removal from current view (no re-scan!)
        self.tree.fast_remove_item(self.data["name"])


class FolderActions:
    def __init__(self, menu, tree, ignore_manager, data):
        self.menu = menu
        self.tree = tree
        self.ignore_manager = ignore_manager
        self.data = data

    def build(self):
        # Using tree.window() calls if needed, but tree usually has proxies
        # Since I am using tree instance, I assume tree has necessary methods or I should call helpers
        
        # NOTE: self.tree in actions is likely FileTreeWidget.
        # But previous code accessed self.window().reload_scan via callback.
        # The user provided code uses `self.tree.rescan_folder(self.data["abs_path"])`
        # I need to ensure FileTreeWidget has `rescan_folder`, `export_subfolder`.
        # I will stick to user provided code structure here, and fix tree_view.py to implement these proxies.
        
        self.menu.addAction(
            icon("rescan.png"),
            "Re-scan This Folder",
            lambda: self.tree.rescan_folder(self.data["abs_path"])
        )

        self.menu.addAction(
            icon("copy.png"),
            "Copy Folder Path",
            lambda: copy_text(self.data["abs_path"])
        )

        self.menu.addAction(
            icon("copy.png"),
            "Copy Tree Snippet",
            lambda: self.tree.copy_tree_snippet(self.data)
        )

        self.menu.addSeparator()

        from .menu_base import ExplorerStyleMenu
        export_menu = ExplorerStyleMenu(self.menu)
        export_menu.setTitle("Export This Folder")
        export_menu.setIcon(icon("export folder.png"))
        
        # Add the styled submenu to the main menu
        self.menu.addMenu(export_menu)
        
        export_menu.addAction(
            "Tree Only",
            lambda: self.tree.export_subfolder(self.data["abs_path"], tree_only=True)
        )
        export_menu.addAction(
            "Tree + Code",
            lambda: self.tree.export_subfolder(self.data["abs_path"], tree_only=False)
        )

        self.menu.addSeparator()

        self.menu.addAction(
            icon("ignore.png"),
            "Ignore This Folder",
            lambda: self._ignore_and_refresh()
        )

        self.menu.addSeparator()

        self.menu.addAction(
            icon("explore.png"),
            "Reveal in Explorer",
            lambda: self.tree.reveal_in_explorer(self.data)
        )

    def _ignore_and_refresh(self):
        # Add to session pattern (for future scans)
        self.ignore_manager.add_session_pattern(self.data["name"])
        # FAST removal from current view (no re-scan!)
        self.tree.fast_remove_item(self.data["name"])
