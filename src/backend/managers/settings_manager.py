import json
import os
from src.config import get_config_dir

class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._config_path = os.path.join(get_config_dir(), "config.json")
            cls._instance._config = {}
            cls._instance._load()
        return cls._instance

    def _load(self):
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self._config = {}
        else:
            self._config = {}

    def _save(self):
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value
        self._save()

    # --- Smart Destination Logic ---

    def get_smart_toggle(self) -> bool:
        """Returns True if Smart Destination feature is enabled globally."""
        return self.get("smart_destination_enabled", True)

    def set_smart_toggle(self, enabled: bool):
        self.set("smart_destination_enabled", enabled)

    def get_default_export_path(self, source_folder: str) -> str:
        """Returns the saved default export path for a given source folder, if any."""
        if not source_folder: return None
        return self.get("folder_preferences", {}).get(source_folder, {}).get("default_export_path")

    def set_default_export_path(self, source_folder: str, target_path: str):
        """Saves a default export path for a source folder and clears manual history."""
        if not source_folder or not target_path: return
        
        prefs = self.get("folder_preferences", {})
        if source_folder not in prefs:
            prefs[source_folder] = {}
        
        prefs[source_folder]["default_export_path"] = target_path
        # Reset manual history since we now have an explicit preference
        prefs[source_folder]["history"] = {"count": 0, "last_path": target_path}
        
        self.set("folder_preferences", prefs)

    def get_folder_history(self, source_folder: str) -> dict:
        """Returns the manual history for a folder."""
        if not source_folder: return {"count": 0, "last_path": None}
        return self.get("folder_preferences", {}).get(source_folder, {}).get("history", {"count": 0, "last_path": None})

    def update_export_history(self, source_folder: str, target_path: str) -> int:
        """
        Updates history. Returns the NEW consecutive count.
        """
        if not source_folder or not target_path: return 0

        prefs = self.get("folder_preferences", {})
        if source_folder not in prefs:
            prefs[source_folder] = {}
        
        history = prefs[source_folder].get("history", {"count": 0, "last_path": None})
        
        last_path = history.get("last_path")
        count = history.get("count", 0)

        # Normalize paths for comparison
        clean_target = os.path.normpath(target_path).lower()
        clean_last = os.path.normpath(last_path).lower() if last_path else None

        if clean_target == clean_last:
            count += 1
        else:
            count = 1 # Reset to 1 (current export)
            
        history["count"] = count
        history["last_path"] = target_path
        
        prefs[source_folder]["history"] = history
        self.set("folder_preferences", prefs)
        
        return count
    def get_default_export_formats(self) -> list:
        """Returns the list of default export format IDs."""
        return self.get("default_export_formats", ["txt_full"])

    def set_default_export_formats(self, formats: list):
        """Saves the default export formats."""
        self.set("default_export_formats", formats)
        # Reset history
        self.set("format_history", {"count": 0, "last_formats": formats})

    def update_format_history(self, current_formats: list) -> int:
        """Tracks consecutive usage of a format combination. Returns count."""
        history = self.get("format_history", {"count": 0, "last_formats": []})
        last_formats = sorted(history.get("last_formats", []))
        current_sorted = sorted(current_formats)
        
        count = history.get("count", 0)
        
        if current_sorted == last_formats:
            count += 1
        else:
            count = 1
            
        history["count"] = count
        history["last_formats"] = current_formats
        self.set("format_history", history)
        return count

    def get_window_geometry(self) -> bytes:
        from PyQt5.QtCore import QByteArray
        hex_data = self.get("window_geometry")
        return QByteArray.fromHex(hex_data.encode()) if hex_data else None

    def set_window_geometry(self, geometry: bytes):
        self.set("window_geometry", bytes(geometry).hex())

    def get_splitter_sizes(self) -> list:
        return self.get("splitter_sizes", [240, 600])

    def set_splitter_sizes(self, sizes: list):
        self.set("splitter_sizes", sizes)
