import os
import json
from PyQt5.QtGui import QIcon
from src.config import resource_path

class IconManager:
    _instance = None
    _icon_cache = {}
    _mappings = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IconManager, cls).__new__(cls)
            cls._instance.base_path = resource_path("assets/Files Icon")
            cls._instance._load_mappings()
        return cls._instance

    def _load_mappings(self):
        """Load icon mappings from the JSON file."""
        if self._mappings is not None:
            return
            
        mapping_path = resource_path("assets/icon_mappings.json")
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                self._mappings = json.load(f)
        except Exception as e:
            print(f"Error loading icon mappings: {e}")
            self._mappings = {
                "fileNames": {},
                "fileExtensions": {},
                "folderNames": {},
                "folderNamesExpanded": {}
            }

    def _get_icon(self, icon_name: str) -> QIcon:
        """Helper to load and cache QIcon from svg name."""
        if not icon_name:
            return QIcon()
            
        if icon_name in self._icon_cache:
            return self._icon_cache[icon_name]
        
        # Some icons in the theme have .clone.svg suffix in definitions, 
        # but our moved files usually keep the base name. 
        # The mappings from the JSON give us the icon identity.
        path = os.path.join(self.base_path, f"{icon_name}.svg")
        
        # Fallback for clones or unusual names
        if not os.path.exists(path):
             # Try without potential suffix if mapping was "python.clone" or similar
             base_id = icon_name.split('.')[0]
             path = os.path.join(self.base_path, f"{base_id}.svg")
             
        if not os.path.exists(path):
            return QIcon()
            
        icon = QIcon(path)
        self._icon_cache[icon_name] = icon
        return icon

    def get_file_icon(self, filename: str) -> QIcon:
        """Get icon for a file based on name or extension (Material Theme logic)."""
        name_lower = filename.lower()
        
        # 1. Check exact filename matches (e.g. package.json, dockerfile)
        file_names = self._mappings.get("fileNames", {})
        if name_lower in file_names:
            icon = self._get_icon(file_names[name_lower])
            if not icon.isNull():
                return icon

        # 2. Check Extension Match (multi-part support like .test.js)
        exts = self._mappings.get("fileExtensions", {})
        parts = name_lower.split('.')
        
        # Iterate from longest extension to shortest (.test.js -> .js)
        # index 0 is usually name, so start from 1
        for i in range(1, len(parts)):
            candidate = ".".join(parts[i:])
            if candidate in exts:
                icon = self._get_icon(exts[candidate])
                if not icon.isNull():
                    return icon

        # 3. Fallback: try raw extension if not found in mappings
        # Some icons are named directly after the extension (e.g. dart.svg, zig.svg)
        ext = os.path.splitext(name_lower)[1]
        if ext and ext.startswith('.'):
            bare_ext = ext[1:]
            # Try mapping first
            if bare_ext in exts:
                icon = self._get_icon(exts[bare_ext])
                if not icon.isNull():
                    return icon
            
            # Try using the extension name directly as the icon ID
            icon = self._get_icon(bare_ext)
            if not icon.isNull():
                return icon

        # 4. Final Fallback: Generic File
        return self._get_icon("file")

    def get_folder_icon(self, foldername: str, is_open: bool = False) -> QIcon:
        """Get icon for a folder (Material Theme logic)."""
        name_lower = foldername.lower()
        
        folder_names = self._mappings.get("folderNames", {})
        folder_names_expanded = self._mappings.get("folderNamesExpanded", {})
        
        # 1. Try specific folder name match
        icons_to_check = folder_names_expanded if is_open else folder_names
        
        if name_lower in icons_to_check:
            icon = self._get_icon(icons_to_check[name_lower])
            if not icon.isNull():
                return icon
        
        # 2. Derive state from alternate state if only one exists
        alt_icons = folder_names if is_open else folder_names_expanded
        if name_lower in alt_icons:
            icon_id = alt_icons[name_lower]
            suffix = "-open" if is_open else ""
            # Strip potential existing state suffixes and apply target suffix
            base_id = icon_id.replace("-open", "").replace("_open", "")
            derived_id = f"{base_id}{suffix}"
            
            icon = self._get_icon(derived_id)
            if not icon.isNull():
                return icon
            # Use the alt ID as final specific fallback
            icon = self._get_icon(icon_id)
            if not icon.isNull():
                return icon

        # 3. Generic folder fallback
        generic_id = "folder-open" if is_open else "folder"
        icon = self._get_icon(generic_id)
        if not icon.isNull():
            return icon
            
        return QIcon()
