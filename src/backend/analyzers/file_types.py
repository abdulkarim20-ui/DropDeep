import os

def get_file_type(filename):
    """
    Returns a human-readable file type based on extension.
    Mimics Windows Explorer "Type" column.
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    # Common Development Files
    if ext == '.py': return 'Python File'
    if ext == '.pyw': return 'Python GUI File'
    if ext == '.js': return 'JavaScript File'
    if ext == '.jsx': return 'React Component'
    if ext == '.ts': return 'TypeScript File'
    if ext == '.tsx': return 'TypeScript Component'
    if ext == '.html': return 'HTML Document'
    if ext == '.htm': return 'HTML Document'
    if ext == '.css': return 'Cascading Style Sheet'
    if ext == '.scss': return 'SASS File'
    if ext == '.json': return 'JSON File'
    if ext == '.xml': return 'XML Document'
    if ext == '.yaml': return 'YAML File'
    if ext == '.yml': return 'YAML File'
    if ext == '.md': return 'Markdown File'
    if ext == '.txt': return 'Text Document'
    if ext == '.sql': return 'SQL Source File'
    if ext == '.c': return 'C Source File'
    if ext == '.cpp': return 'C++ Source File'
    if ext == '.h': return 'C/C++ Header File'
    if ext == '.java': return 'Java Source File'
    if ext == '.class': return 'Java Class File'
    if ext == '.jar': return 'Executable Jar File'
    if ext == '.sh': return 'Shell Script'
    if ext == '.bat': return 'Windows Batch File'
    if ext == '.ps1': return 'PowerShell Script'
    if ext == '.dockerfile': return 'Docker File'
    if filename.lower() == 'dockerfile': return 'Docker File'
    if filename.lower() == 'makefile': return 'Make File'
    if ext == '.gitignore': return 'Git Ignore File'
    if ext == '.env': return 'Environment File'

    # Images
    if ext in ['.png', '.apng']: return 'PNG Image'
    if ext in ['.jpg', '.jpeg', '.jfif']: return 'JPEG Image'
    if ext == '.gif': return 'GIF Image'
    if ext == '.bmp': return 'Bitmap Image'
    if ext == '.svg': return 'SVG Document'
    if ext == '.webp': return 'WebP Image'
    if ext == '.ico': return 'Icon File'
    if ext == '.tiff': return 'TIFF Image'
    if ext == '.psd': return 'Adobe Photoshop Image'
    if ext == '.ai': return 'Adobe Illustrator File'

    # Documents
    if ext == '.pdf': return 'PDF Document'
    if ext in ['.doc', '.docx']: return 'Microsoft Word Document'
    if ext in ['.xls', '.xlsx']: return 'Microsoft Excel Worksheet'
    if ext in ['.ppt', '.pptx']: return 'Microsoft PowerPoint Presentation'
    if ext == '.csv': return 'Comma Separated Values'

    # Audio/Video
    if ext == '.mp3': return 'MP3 Audio File'
    if ext == '.wav': return 'WAVE Audio File'
    if ext == '.mp4': return 'MP4 Video File'
    if ext == '.avi': return 'AVI Video File'
    if ext == '.mov': return 'QuickTime Video File'
    if ext == '.mkv': return 'MKV Video File'

    # Archives
    if ext == '.zip': return 'Compressed (zipped) Folder'
    if ext == '.rar': return 'WinRAR Archive'
    if ext == '.7z': return '7-Zip Archive'
    if ext == '.tar': return 'TAR Archive'
    if ext == '.gz': return 'GZIP Archive'

    # System/Executables
    if ext == '.exe': return 'Application'
    if ext == '.dll': return 'Application Extension'
    if ext == '.iso': return 'Disc Image File'
    if ext == '.ini': return 'Configuration Settings'
    if ext == '.log': return 'Log File'

    # Fallback
    if len(ext) > 1:
        return f"{ext[1:].upper()} File"
    
    return "File"
