from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication
from PyQt5.QtCore import Qt, QDateTime, QLocale, QSettings, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from src.config import resource_path
from src.frontend.components.tree_context_menu.menu import TreeContextMenu
import os

class FileTreeWidget(QTreeWidget):
    filePreviewRequested = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("StructurePro", "DropDeep")
        
        # Load custom folder icon once
        folder_icon_path = resource_path("assets/folder1.png")
        self.folder_icon = QIcon(folder_icon_path) if os.path.exists(folder_icon_path) else QIcon()
        
        # Load Chevron Icons for Tree
        chevron_right = resource_path("assets/chevron_right.png").replace("\\", "/")
        chevron_down = resource_path("assets/chevron_down.png").replace("\\", "/")

        # New VS Code properties
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setRootIsDecorated(True)
        self.setAnimated(True)

        # Restore column widths
        for i in range(self.columnCount()):
            width = self.settings.value(f"tree/column_width_{i}")
            if width:
                self.setColumnWidth(i, int(width))
                
        # Save upon resize
        self.header().sectionResized.connect(self.save_column_widths)
        
        # VS Code Stylesheet
        # VS Code Stylesheet
        self.setStyleSheet(f"""
        QTreeWidget {{
            background-color: transparent;
            border: none;
            padding: 4px;
            outline: 0;
        }}

        /* Row */
        QTreeWidget::item {{
            height: 26px;
            padding-left: 6px;
            color: #111827;
            border: none;
        }}

        /* Hover (NOT WHITE) */
        QTreeWidget::item:hover {{
            background-color: #E5E7EB;
            border-radius: 4px;
        }}

        /* Selected */
        QTreeWidget::item:selected {{
            background-color: #DCEAFE;
            color: #1D4ED8;
            border-radius: 4px;
        }}

        /* Selected but not focused (important VS Code behavior) */
        QTreeWidget::item:selected:!active {{
            background-color: #E5E7EB;
            color: #111827;
        }}

        /* Branch Icons (VS Code Style) */
        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {{
            image: url({chevron_right});
        }}

        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {{
            image: url({chevron_down});
        }}

        QTreeWidget::branch {{
            background: transparent;
        }}
        
        /* Refined Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: #D1D5DB;
            min-height: 20px;
            border-radius: 5px;
            border: 2px solid transparent; /* padding effect */
            background-clip: content-box;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #9CA3AF;
            border: 2px solid transparent; 
            background-clip: content-box;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: #D1D5DB;
            min-width: 20px;
            border-radius: 5px;
            border: 2px solid transparent;
            background-clip: content-box;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: #9CA3AF;
            border: 2px solid transparent; 
            background-clip: content-box;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
        """)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)
        
        # Connect item click for preview
        self.itemClicked.connect(self._on_item_clicked)
    
    def _on_item_clicked(self, item, column):
        """Handle item click to show preview in canvas."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        
        # Only preview files, not folders
        if data.get('type') == 'file':
            self.filePreviewRequested.emit(data)

    def _open_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        # Ensure we have access to ignore_manager, via window()
        ignore_mgr = self.window().ignore_manager if hasattr(self.window(), 'ignore_manager') else None
        
        TreeContextMenu(
            parent=self,
            tree=self,
            ignore_manager=ignore_mgr
        ).open(self.viewport().mapToGlobal(pos), data)

    def copy_tree_snippet(self, folder_data):
        from src.backend.exporter import generate_tree_text
        snippet = generate_tree_text(folder_data)
        QApplication.clipboard().setText(snippet)

    # --- Proxies for Menu Actions ---
    
    def rescan_folder(self, abs_path):
        """Legacy rescan - triggers full reload. Use only when necessary."""
        if hasattr(self.window(), 'reload_scan'):
             self.window().reload_scan() 
        else:
             print("Rescan function not found on main window")

    def fast_remove_item(self, item_name: str):
        """
        FAST client-side removal without re-scanning.
        Removes matching items from tree UI AND from current_data in memory.
        """
        main_window = self.window()
        
        # 1. Remove from in-memory data (so export is correct)
        if hasattr(main_window, 'current_data') and main_window.current_data:
            self._filter_out_name(main_window.current_data, item_name)
        
        # 2. Remove from tree UI (instant visual feedback)
        self._remove_items_by_name(self.invisibleRootItem(), item_name)
        
        # 3. Update token estimator (reflects the reduced content)
        if hasattr(main_window, 'token_btn'):
            main_window.token_btn.update_estimate()
    
    def _filter_out_name(self, node: dict, name_to_remove: str):
        """Recursively remove children matching name from data dict."""
        if 'children' not in node:
            return
        
        # Filter out matching children
        node['children'] = [
            child for child in node['children']
            if child.get('name') != name_to_remove
        ]
        
        # Recurse into remaining children
        for child in node['children']:
            if child.get('type') == 'folder':
                self._filter_out_name(child, name_to_remove)
    
    def _remove_items_by_name(self, parent_item, name_to_remove: str):
        """Recursively remove QTreeWidgetItems matching name."""
        items_to_remove = []
        
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            data = child.data(0, Qt.UserRole)
            
            if data and data.get('name') == name_to_remove:
                items_to_remove.append((parent_item, i))
            else:
                # Recurse into child
                self._remove_items_by_name(child, name_to_remove)
        
        # Remove in reverse order to avoid index shifting issues
        for parent, index in reversed(items_to_remove):
            parent.takeChild(index)

    def export_subfolder(self, abs_path, tree_only=False):
        if hasattr(self.window(), 'export_folder'):
            self.window().export_folder(abs_path, tree_only)
        else:
            print("Export function not found on main window")

    def open_file_external(self, path):
         if hasattr(self.window(), 'open_file_external'):
             self.window().open_file_external(path)
         else:
             print("External open function not found on main window")

    # preview_file_internal proxy removed

    def reveal_in_explorer(self, path):
        if hasattr(self.window(), 'reveal_in_explorer'):
            self.window().reveal_in_explorer(path)
        else:
            print("Reveal function not found on main window")

    def save_column_widths(self, *args):
        for i in range(self.columnCount()):
            self.settings.setValue(
                f"tree/column_width_{i}",
                self.columnWidth(i)
            )

    def get_icon_for_item(self, item_type, is_folder):
        if is_folder:
            return QIcon.fromTheme("folder")

        if "Python" in item_type:
            return QIcon.fromTheme("text-x-python")
        if "Image" in item_type:
            return QIcon.fromTheme("image-x-generic")
        if "PDF" in item_type:
            return QIcon.fromTheme("application-pdf")
        if "Document" in item_type:
            return QIcon.fromTheme("x-office-document")

        return QIcon.fromTheme("text-x-generic")

    def populate(self, data):
        """
        Populate the tree with dictionary data from scanner.
        """
        self.clear()
        if not data:
            return

        def add_items(parent, node_data):
            children = node_data.get('children', [])

            if not children:
                empty_item = QTreeWidgetItem(["(empty)"])
                empty_item.setDisabled(True)
                empty_item.setForeground(0, Qt.gray)
                parent.addChild(empty_item)
                return

            # Sort: Folders first, then files
            children = sorted(children, 
                            key=lambda x: (x['type'] != 'folder', x['name'].lower()))
            
            for child in children:
                name = child['name']
                item_type = child.get('display_type', "File")
                if child['type'] == 'folder' and item_type == "File":
                     item_type = "Folder" # Fallback safety

                # New order: Name only
                item = QTreeWidgetItem([name])
                
                # Attach data for context menu
                # Copy child to ensure we have 'children', 'path', etc. for exporter
                node_data = child.copy() 
                node_data["abs_path"] = child["path"] if os.path.isabs(child["path"]) else os.path.abspath(child["path"])
                node_data["rel_path"] = child.get("rel_path", child["path"])

                item.setData(0, Qt.UserRole, node_data)
                
                if child['type'] == 'folder':
                    font = QFont()
                    font.setWeight(QFont.DemiBold)  # Semi-bold
                    item.setFont(0, font)  # Name column only
                


                # Restricted file check
                # Restricted file check - visual indication logic moved or removed since columns are gone
                # if child['type'] == 'file' and child.get('content') is None and size == "":
                #      item.setText(2, "Restricted")

                # Icons
                if child['type'] == 'folder':
                    item.setIcon(0, self.folder_icon)
                else:
                    item.setIcon(0, self.get_icon_for_item(item_type, False))
                
                parent.addChild(item)
                
                if child['type'] == 'folder':
                    add_items(item, child)

        root_item = QTreeWidgetItem([data['name']])
        
        # Attach root data for context menu
        root_data = data.copy()
        root_data["abs_path"] = data["path"] if os.path.isabs(data["path"]) else os.path.abspath(data["path"])
        root_data["rel_path"] = data.get("rel_path", ".") # Root relative path is usually dot or empty
        root_item.setData(0, Qt.UserRole, root_data)

        root_font = QFont()
        root_font.setWeight(QFont.Bold)
        root_item.setFont(0, root_font)
        
        self.addTopLevelItem(root_item)
        add_items(root_item, data)
        root_item.setExpanded(True)
        # self.resizeColumnToContents(0) # Logic removed primarily to respect Stretch mode and user preference
        
        # Max width cap for Type column - Removed
        # max_type_width = 260
        # if self.columnWidth(2) > max_type_width:
        #    self.setColumnWidth(2, max_type_width)

    def filter_items(self, text):
        """
        Filter tree items based on text.
        """
        text = text.lower()
        
        def check_item(item):
            # Check current item
            match = text in item.text(0).lower() 
            
            # Check children
            child_match = False
            for i in range(item.childCount()):
                if check_item(item.child(i)):
                    child_match = True
            
            # Logic: Show if match OR child matches
            should_show = match or child_match
            item.setHidden(not should_show)
            
            # Expand if child matches to reveal it
            if child_match:
                item.setExpanded(True)
                
            return should_show

        # Iterate top level items (root is usually one, but loop to be safe)
        for i in range(self.topLevelItemCount()):
            check_item(self.topLevelItem(i))
