import os
import json
import io
import html
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Flowable, Preformatted, XPreformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import black
from src.backend.utils import get_file_heading, sanitize_content

logger = logging.getLogger(__name__)

# --- Constants for Large File Handling ---
MAX_FILE_SIZE_FOR_PDF = 100_000  # 100KB max per file in PDF (prevents memory issues)
MAX_FILES_IN_PDF = 500  # Maximum files to include in PDF
MAX_TOC_DEPTH = 10  # Maximum folder depth for TOC

# --- Text & JSON Export Helpers ---

def _build_tree_string(node, prefix='', depth=0, max_depth=50):
    """Build tree with depth limit to prevent stack overflow on deep structures."""
    if depth > max_depth:
        return f"{prefix}... (truncated - too deep)"
    
    output = []
    children = node.get('children', [])
    if not children:
        return ''
    
    sorted_children = sorted(children, key=lambda x: x.get('name', ''))
    for index, child in enumerate(sorted_children):
        is_last = index == len(sorted_children) - 1
        connector = '└── ' if is_last else '├── '
        new_prefix = prefix + ('    ' if is_last else '│   ')

        name = child.get('name', 'unknown')
        if child.get('type') == 'folder':
            output.append(f"{prefix}{connector}📁 {name}/")
            subtree = _build_tree_string(child, new_prefix, depth + 1, max_depth)
            if subtree:
                output.append(subtree)
        else:
            output.append(f"{prefix}{connector}📄 {name}")
    return '\n'.join(output)

def generate_tree_text(data):
    if not data:
        return ""
    output = []
    output.append(f"Project Directory Structure: {data.get('name', 'Unknown')}\n")
    output.append(f"📁 {data.get('path', '')}")
    output.append(_build_tree_string(data))
    return '\n'.join(output)

def generate_full_text(data):
    if not data:
        return ""
    output = []
    output.append(generate_tree_text(data))
    
    output.append("\n" + "=" * 50)
    output.append("Code File Contents")
    output.append("=" * 50 + "\n")
    
    # Iterative file collection (prevents stack overflow)
    all_files = _collect_all_files(data)
    
    for file_node in all_files:
        path = file_node.get('path', 'unknown')
        content = file_node.get('content')
        if content:
            output.append(get_file_heading(path))
            output.append(sanitize_content(content))
            output.append("\n" + "=" * 50 + "\n")
            
    return '\n'.join(output)

def _collect_all_files(data, max_files=10000):
    """Iteratively collect all files to avoid recursion limits."""
    all_files = []
    stack = [data]
    
    while stack and len(all_files) < max_files:
        node = stack.pop(0)
        for child in node.get('children', []):
            if child.get('type') == 'folder':
                stack.append(child)
            elif child.get('type') == 'file' and child.get('content') is not None:
                all_files.append(child)
                if len(all_files) >= max_files:
                    break
    
    return all_files


# --- PDF Export Helpers ---

def _sanitize_pdf_anchor(name):
    """
    Sanitize a path/name for use as PDF anchor (bookmark + link target).
    Must be consistent between NamedDestination and TOC links.
    Uses only alphanumeric characters and underscores for maximum compatibility.
    """
    if not name:
        return "file_unknown"
    
    # Convert to safe anchor: only alphanumeric and underscore
    safe_chars = []
    for char in name:
        if char.isalnum():
            safe_chars.append(char)
        else:
            safe_chars.append('_')
    
    safe_name = ''.join(safe_chars)
    
    # Ensure it starts with a letter (required for some PDF readers)
    if safe_name and not safe_name[0].isalpha():
        safe_name = 'f_' + safe_name
    
    # Limit length and ensure uniqueness with hash suffix for long paths
    if len(safe_name) > 80:
        import hashlib
        hash_suffix = hashlib.md5(name.encode()).hexdigest()[:8]
        safe_name = safe_name[:70] + '_' + hash_suffix
    
    return safe_name if safe_name else "file_unknown"


class NamedDestination(Flowable):
    """PDF bookmark destination."""
    def __init__(self, name):
        Flowable.__init__(self)
        # Use shared sanitization
        self.name = _sanitize_pdf_anchor(name)
        
    def draw(self):
        try:
            self.canv.bookmarkPage(self.name)
            self.canv.addOutlineEntry(self.name, self.name, 0, 0)
        except Exception as e:
            logger.warning(f"Could not create bookmark for {self.name}: {e}")


def _escape_xml(text):
    """Escape text for safe XML/PDF rendering."""
    if not text:
        return ""
    return html.escape(str(text))


def _truncate_content(content, max_chars=MAX_FILE_SIZE_FOR_PDF):
    """Truncate file content if too large for PDF."""
    if not content:
        return ""
    if len(content) > max_chars:
        return content[:max_chars] + f"\n\n... [TRUNCATED - File too large ({len(content):,} chars)]"
    return content


def _sanitize_content_for_pdf(content):
    """
    Sanitize content for ReportLab PDF rendering.
    Handles special characters, null bytes, and encoding issues.
    """
    if not content:
        return ""
    
    # Remove null bytes and other problematic characters
    content = content.replace('\x00', '')
    
    # Replace tabs with spaces for consistent rendering
    content = content.replace('\t', '    ')
    
    # Remove control characters except newlines
    sanitized = []
    for char in content:
        if char == '\n' or char == '\r' or (ord(char) >= 32 and ord(char) < 127) or ord(char) >= 160:
            sanitized.append(char)
        else:
            sanitized.append(' ')  # Replace control chars with space
    
    return ''.join(sanitized)


def generate_pdf(data, output_path):
    """
    Generate PDF with robust error handling for large projects.
    """
    if not data:
        raise ValueError("No data provided for PDF generation")
    
    buffer = io.BytesIO()
    
    try:
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=72, 
            leftMargin=72,
            topMargin=72, 
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        
        # Add custom styles (with error handling for duplicates)
        if 'FileHeadingStyle' not in [s.name for s in styles.byName.values()]:
            styles.add(ParagraphStyle(
                name='FileHeadingStyle', 
                fontName='Helvetica-Bold', 
                fontSize=14, 
                leading=16, 
                spaceAfter=12
            ))
        
        if 'CodePreformattedStyle' not in [s.name for s in styles.byName.values()]:
            styles.add(ParagraphStyle(
                name='CodePreformattedStyle', 
                fontName='Courier', 
                fontSize=8, 
                leading=10, 
                textColor=black, 
                spaceBefore=6, 
                spaceAfter=6
            ))
        
        story = []

        # Title Page
        title_style = ParagraphStyle(
            'TitleStyle', 
            fontSize=24, 
            fontName='Helvetica-Bold', 
            alignment=TA_CENTER, 
            spaceAfter=24
        )
        
        project_name = _escape_xml(data.get('name', 'Unknown Project'))
        project_path = _escape_xml(data.get('path', ''))
        
        story.append(Paragraph(f"Project Scan Report: {project_name}", title_style))
        story.append(Paragraph(f"Path: {project_path}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        # Table of Contents (with depth limit)
        story.append(Paragraph("Table of Contents", styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))
        
        toc_items = []
        _build_toc_items(data, toc_items, styles, level=0, max_items=500)
        story.extend(toc_items)
        
        story.append(PageBreak())

        # Code File Contents
        story.append(Paragraph("Code File Contents", styles['Heading1']))
        
        # Collect files with limits
        all_files = _collect_all_files(data, max_files=MAX_FILES_IN_PDF)
        
        if len(all_files) >= MAX_FILES_IN_PDF:
            story.append(Paragraph(
                f"<i>Note: Showing first {MAX_FILES_IN_PDF} files. "
                f"Total files may exceed this limit.</i>",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.1 * inch))

        for i, file_node in enumerate(all_files):
            try:
                if i > 0:
                    story.append(PageBreak())

                file_path = file_node.get('path', 'unknown')
                story.append(NamedDestination(file_path))
                
                heading_text = _escape_xml(get_file_heading(file_path))
                story.append(Paragraph(heading_text, styles['FileHeadingStyle']))

                # Get and sanitize content
                raw_content = file_node.get('content', '')
                content = _sanitize_content_for_pdf(raw_content)
                content = _truncate_content(content)
                
                if content:
                    # Use XPreformatted for better handling of special content
                    try:
                        story.append(Preformatted(content, styles['CodePreformattedStyle']))
                    except Exception as e:
                        # Fallback: escape and use paragraph
                        logger.warning(f"Preformatted failed for {file_path}: {e}")
                        escaped = _escape_xml(content[:5000])  # Limit fallback
                        story.append(Paragraph(f"<pre>{escaped}</pre>", styles['Normal']))
                else:
                    story.append(Paragraph("<i>(Empty or binary file)</i>", styles['Normal']))
                    
                story.append(Spacer(1, 0.2 * inch))
                
            except Exception as e:
                logger.error(f"Error processing file {file_node.get('path', '?')}: {e}")
                story.append(Paragraph(
                    f"<i>Error rendering file: {_escape_xml(str(e))}</i>",
                    styles['Normal']
                ))

        # Build PDF
        doc.build(story)
        
        # Write to file
        with open(output_path, "wb") as f:
            f.write(buffer.getvalue())
            
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise RuntimeError(f"PDF generation failed: {e}") from e
    finally:
        buffer.close()


def _build_toc_items(node, items_list, styles, level=0, max_items=500, current_count=None):
    """
    Build TOC items iteratively with limits.
    """
    if current_count is None:
        current_count = [0]  # Mutable counter
    
    if level > MAX_TOC_DEPTH or current_count[0] >= max_items:
        return
    
    children = node.get('children', [])
    if not children:
        return
        
    sorted_children = sorted(children, key=lambda x: (x.get('type') != 'folder', x.get('name', '')))
    indent_size = 12
    
    for child in sorted_children:
        if current_count[0] >= max_items:
            items_list.append(Paragraph(
                f"<i>... and more items (TOC truncated at {max_items})</i>",
                styles['Normal']
            ))
            return
            
        current_count[0] += 1
        child_name = _escape_xml(child.get('name', 'unknown'))
        
        if child.get('type') == 'folder':
            style = ParagraphStyle(
                f'TOCFolderLevel{level}_{current_count[0]}', 
                parent=styles['Normal'], 
                leftIndent=indent_size * level, 
                spaceAfter=2
            )
            items_list.append(Paragraph(f"📁 {child_name}/", style))
            _build_toc_items(child, items_list, styles, level + 1, max_items, current_count)
        else:
            style = ParagraphStyle(
                f'TOCFileLevel{level}_{current_count[0]}', 
                parent=styles['Normal'], 
                leftIndent=indent_size * level, 
                spaceAfter=2
            )
            file_path = child.get('path', '')
            has_content = child.get('content') is not None
            
            if has_content:
                # Only create clickable link if file has content (will have a bookmark destination)
                safe_path = _sanitize_pdf_anchor(file_path)
                items_list.append(Paragraph(
                    f"<a href='#{safe_path}'><font color='blue'>📄 {child_name}</font></a>", 
                    style
                ))
            else:
                # Non-linkable entry for binary/unsupported files
                items_list.append(Paragraph(f"📄 {child_name}", style))


# --- Main Export Function ---

def export_data(data, target_dir, formats):
    """
    Exports the data to the specified formats in the target directory.
    formats: list of strings ['json', 'txt_tree', 'txt_full', 'pdf']
    
    Returns list of created file paths.
    Raises exceptions with descriptive messages on failure.
    """
    if not data:
        raise ValueError("No data to export")
    
    if not target_dir or not os.path.isdir(target_dir):
        raise ValueError(f"Invalid target directory: {target_dir}")
    
    base_name = data.get('name', 'export')
    # Sanitize filename
    base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
    if not base_name:
        base_name = 'export'
    
    results = []
    errors = []
    
    if 'json' in formats:
        try:
            out = os.path.join(target_dir, f"{base_name}.json")
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False, default=str)
            results.append(out)
        except Exception as e:
            errors.append(f"JSON export failed: {e}")
            logger.error(f"JSON export failed: {e}")
        
    if 'txt_tree' in formats:
        try:
            out = os.path.join(target_dir, f"{base_name}.tree.txt")
            with open(out, 'w', encoding='utf-8') as f:
                f.write(generate_tree_text(data))
            results.append(out)
        except Exception as e:
            errors.append(f"Tree text export failed: {e}")
            logger.error(f"Tree text export failed: {e}")

    if 'txt_full' in formats:
        try:
            out = os.path.join(target_dir, f"{base_name}.full.txt")
            with open(out, 'w', encoding='utf-8') as f:
                f.write(generate_full_text(data))
            results.append(out)
        except Exception as e:
            errors.append(f"Full text export failed: {e}")
            logger.error(f"Full text export failed: {e}")
        
    if 'pdf' in formats:
        try:
            out = os.path.join(target_dir, f"{base_name}.pdf")
            generate_pdf(data, out)
            results.append(out)
        except Exception as e:
            errors.append(f"PDF export failed: {e}")
            logger.error(f"PDF export failed: {e}")
    
    # If all exports failed, raise an error
    if not results and errors:
        raise RuntimeError("All exports failed: " + "; ".join(errors))
    
    # If some succeeded but some failed, log warnings but return successes
    if errors:
        logger.warning(f"Some exports failed: {errors}")
        
    return results
