from .menu_base import ExplorerStyleMenu
from .actions import FileActions, FolderActions


class TreeContextMenu:
    def __init__(self, parent, tree, ignore_manager):
        self.parent = parent
        self.tree = tree
        self.ignore_manager = ignore_manager

    def open(self, global_pos, item_data):
        """
        item_data:
        {
            type: 'file' | 'folder',
            name: str,
            abs_path: str,
            rel_path: str,
            ...
        }
        """
        menu = ExplorerStyleMenu(self.parent)

        if item_data["type"] == "file":
            FileActions(menu, self.tree, self.ignore_manager, item_data).build()
        else:
            FolderActions(menu, self.tree, self.ignore_manager, item_data).build()

        menu.exec_(global_pos)
