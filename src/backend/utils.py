import os
from src.config import FILE_TYPE_MAP

def get_file_heading(file_path):
    """
    Determines the appropriate emoji and file type for a given file path.
    """
    filename = os.path.basename(file_path)
    # Check exact filename first
    if filename in FILE_TYPE_MAP:
        emoji, file_type = FILE_TYPE_MAP[filename]
        return f"--- {emoji} {file_type}: {file_path} ---"

    # Check extension
    extension = os.path.splitext(filename)[1].lower()
    if extension in FILE_TYPE_MAP:
        emoji, file_type = FILE_TYPE_MAP[extension]
    else:
        emoji, file_type = FILE_TYPE_MAP['default']
        
    return f"--- {emoji} {file_type}: {file_path} ---"

import re

SENSITIVE_KEYS = ['api_key', 'token', 'secret', 'password']

def sanitize_content(text):
    if not text:
        return text

    for key in SENSITIVE_KEYS:
        text = re.sub(
            rf'({key}\s*[:=]\s*)(.+)',
            r'\1***REDACTED***',
            text,
            flags=re.IGNORECASE
        )
    return text
