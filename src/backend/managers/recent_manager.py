import json, os
from src.config import get_config_dir

RECENT_FILE = os.path.join(get_config_dir(), "crawlsee_recent.json")

def load_recent():
    if not os.path.exists(RECENT_FILE):
        return []
    try:
        with open(RECENT_FILE, "r") as f:
            data = json.load(f)
            # Filter non-existent folders
            return [p for p in data if os.path.isdir(p)]
    except:
        return []

def add_recent(path):
    recent = load_recent()
    # Normalize path
    path = os.path.abspath(path)
    
    if path in recent:
        recent.remove(path)
    recent.insert(0, path)
    recent = recent[:3] # Keep top 3

    try:
        with open(RECENT_FILE, "w") as f:
            json.dump(recent, f)
    except:
        pass

    return recent
