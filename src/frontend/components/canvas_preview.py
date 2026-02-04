"""
Canvas Preview Panel - VS Code-like file/image preview in the editor area.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QSizePolicy, QStackedWidget, QApplication,
    QTabWidget, QTabBar
)
from PyQt5.QtGui import QFont, QColor, QFontInfo, QPixmap
from PyQt5.QtCore import Qt
from src.config import resource_path
from src.frontend.components.zoomable_image_viewer import ZoomableImageViewer
import os

# QScintilla for code preview
from PyQt5.Qsci import (
    QsciScintilla,
    QsciLexerPython,
    QsciLexerJSON,
    QsciLexerCPP,
    QsciLexerHTML,
    QsciLexerCSS,
    QsciLexerJavaScript,
    QsciLexerMarkdown,
    QsciLexerSQL,
    QsciLexerXML,
    QsciLexerYAML,
    QsciLexerBash
)


def get_editor_font():
    # VS Code Default Font Stack preferences
    for name in ["Cascadia Code", "Cascadia Mono", "Consolas", "Menlo", "Monaco", "Courier New"]:
        font = QFont(name)
        font.setPointSizeF(10.5) # 10.5pt ≈ 14px (VS Code Standard) based on 96 DPI
        if QFontInfo(font).family() == name:
            return font
    
    font = QFont("Monospace")
    font.setPointSizeF(10.5)
    return font


class AutoScrollEditor(QsciScintilla):
    """QsciScintilla subclass with auto-hiding scrollbars."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.verticalScrollBar().setProperty("active", "true")
        self.horizontalScrollBar().setProperty("active", "true")
        self.verticalScrollBar().style().unpolish(self.verticalScrollBar())
        self.verticalScrollBar().style().polish(self.verticalScrollBar())
        self.horizontalScrollBar().style().unpolish(self.horizontalScrollBar())
        self.horizontalScrollBar().style().polish(self.horizontalScrollBar())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.verticalScrollBar().setProperty("active", "false")
        self.horizontalScrollBar().setProperty("active", "false")
        self.verticalScrollBar().style().unpolish(self.verticalScrollBar())
        self.verticalScrollBar().style().polish(self.verticalScrollBar())
        self.horizontalScrollBar().style().unpolish(self.horizontalScrollBar())
        self.horizontalScrollBar().style().polish(self.horizontalScrollBar())
        super().leaveEvent(event)


class CanvasPreview(QWidget):
    """
    A VS Code-like preview panel that supports multiple open tabs (Editors/Images).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.open_files = {} # Key: unique_path, Value: widget_instance

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget to switch between "Empty" and "Tabbed View"
        self.stack = QStackedWidget()
        
        # 1. Empty State (Welcome)
        self.empty_widget = self._build_empty_state()
        self.stack.addWidget(self.empty_widget)
        
        # 2. Tabbed Interface
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True) # Removes standard frame, looks cleaner
        self.tabs.setUsesScrollButtons(True) # Enable scrolling for tabs
        self.tabs.setElideMode(Qt.ElideRight) # Truncate long names
        
        close_icon = resource_path("assets/close.png").replace("\\", "/")
        
        # VS Code-like Tab Styling
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border-top: 1px solid #E5E7EB; /* Subtle separator */
                background: #FFFFFF;
                top: -1px; /* Overlap border */
            }}
            QTabBar {{
                background: #F3F4F6; /* Sidebar/Tabbar gray */
            }}
            QTabBar::tab {{
                background: #F3F4F6; 
                color: #6B7280;
                border-right: 1px solid #E5E7EB;
                border-bottom: 1px solid #E5E7EB;
                padding: 6px 10px;
                padding-right: 24px; /* Space for close button */
                min-width: 120px;
                max-width: 220px;
                height: 24px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                border-top: 1px solid transparent; 
            }}
            QTabBar::tab:selected {{
                background: #FFFFFF;
                color: #1F2937;
                border-top: 2px solid #007AFF; /* Active Blue Top Border */
                border-bottom: 1px solid #FFFFFF; /* Merge with content */
                font-weight: 500;
            }}
            QTabBar::tab:hover:!selected {{
                background: #FFFFFF;
                color: #1F2937;
            }}
            QTabBar::close-button {{
                subcontrol-position: right;
                margin-right: 6px;
                image: url({close_icon});
                width: 25px;
                height: 25px;
                border-radius: 4px;
            }}
            QTabBar::close-button:hover {{
                background-color: #E5E7EB; /* Subtle hover block */
            }}
            QTabBar::scroller {{
                width: 0px; 
                height: 0px;
            }}
        """)
        
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.stack.addWidget(self.tabs)
        
        layout.addWidget(self.stack)
        
        # Start with empty state
        self.show_empty()
    
    def _build_empty_state(self):
        """Build the welcome/empty state view."""
        widget = QWidget()
        widget.setStyleSheet("background-color: #FFFFFF;")
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Welcome message
        title = QLabel("No file selected")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: 500;
            color: #9CA3AF;
            font-family: 'Segoe UI', sans-serif;
        """)
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Click on a file in the Explorer to preview")
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: #D1D5DB;
            font-family: 'Segoe UI', sans-serif;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return widget

    def _create_code_editor(self, content, ext):
        """Factory: Create a new code editor instance."""
        editor = AutoScrollEditor()
        font = get_editor_font()
        editor.setFont(font)
        editor.setMarginsFont(font)
        
        # Light theme styling (VS Code Light)
        editor.setStyleSheet("""
            QsciScintilla {
                background-color: #FFFFFF;
                color: #1F2937;
                border: none;
            }
            
            /* VS Code Auto-Hide Slim Blue Scrollbars */
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: transparent;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar[active="true"]::handle:vertical {
                background: #007AFF;
            }
            QScrollBar::handle:vertical:hover {
                background: #0069D9;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: transparent;
                height: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: transparent;
                min-width: 20px;
                border-radius: 3px;
            }
            QScrollBar[active="true"]::handle:horizontal {
                background: #007AFF;
            }
            QScrollBar::handle:horizontal:hover {
                background: #0069D9;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # Editor Configuration
        editor.setMarginType(1, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(1, 12)
        editor.setMarginsBackgroundColor(QColor("#FFFFFF"))
        editor.setMarginSensitivity(1, False)
        
        editor.setMarginType(0, QsciScintilla.NumberMargin)
        editor.setMarginWidth(0, "00000")
        editor.setMarginLineNumbers(0, True)
        editor.setMarginsForegroundColor(QColor("#6E7681"))
        
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor("#F0F0F0"))
        editor.setCaretForegroundColor(QColor("#000000"))
        editor.setCaretWidth(2)
        
        editor.setSelectionBackgroundColor(QColor("#ADD6FF"))
        editor.setSelectionForegroundColor(QColor("#000000"))
        
        editor.setFolding(QsciScintilla.PlainFoldStyle)
        editor.setMarginType(2, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(2, 12)
        editor.setFoldMarginColors(QColor("#FFFFFF"), QColor("#FFFFFF"))
        
        editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        editor.setMatchedBraceBackgroundColor(QColor("#D7D7D7"))
        editor.setMatchedBraceForegroundColor(QColor("#000000"))

        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(4)
        editor.setAutoIndent(False)
        editor.setWrapMode(QsciScintilla.WrapNone)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded) # Smart: only show if needed
        editor.setReadOnly(True)
        
        editor.setPaper(QColor("#FFFFFF"))
        editor.setColor(QColor("#1F2937"))
        
        # Set Content & Lexer
        lexer = self._get_lexer(ext)
        if lexer:
             lexer.setDefaultFont(font)
             lexer.setDefaultPaper(QColor("#FFFFFF"))
             lexer.setDefaultColor(QColor("#24292E"))
             self._apply_vscode_theme(lexer)
             editor.setLexer(lexer)
        else:
             editor.setLexer(None)
             editor.setFont(font)
             
        editor.setText(content)
        return editor

    def _create_image_viewer(self, abs_path):
        """Factory: Create a new image viewer instance."""
        viewer = ZoomableImageViewer()
        viewer.setStyleSheet("background-color: #FFFFFF;")
        if abs_path and os.path.exists(abs_path):
            pixmap = QPixmap(abs_path)
            viewer.set_image(pixmap)
        return viewer

    def _get_lexer(self, ext):
        """Get the appropriate lexer for a file extension."""
        ext = ext.lower()
        if ext in ['.py', '.pyw']: return QsciLexerPython()
        if ext in ['.json']: return QsciLexerJSON()
        if ext in ['.html', '.htm', '.xml', '.svg']: return QsciLexerHTML()
        if ext in ['.css', '.scss', '.less']: return QsciLexerCSS()
        if ext in ['.js', '.jsx', '.ts', '.tsx', '.mjs']: return QsciLexerJavaScript()
        if ext in ['.c', '.cpp', '.h', '.hpp', '.cs', '.java', '.go']: return QsciLexerCPP()
        if ext in ['.sh', '.bash', '.zsh']: return QsciLexerBash()
        if ext in ['.yaml', '.yml']: return QsciLexerYAML()
        if ext in ['.sql']: return QsciLexerSQL()
        if ext in ['.md', '.markdown']: return QsciLexerMarkdown()
        return None
    
    def _apply_vscode_theme(self, lexer):
        """Apply VS Code Light syntax highlighting to the lexer."""
        if not lexer: return
        
        c_background = QColor("#FFFFFF")
        c_default = QColor("#24292E")
        c_keyword = QColor("#0000FF")
        c_string = QColor("#A31515")
        c_comment = QColor("#008000")
        c_number = QColor("#098658")
        c_class = QColor("#267F99")
        c_function = QColor("#795E26")
        c_operator = QColor("#24292E")
        c_identifier = QColor("#24292E")

        def set_style(style_id, color, paper=c_background, bold=False, italic=False):
            lexer.setColor(color, style_id)
            lexer.setPaper(paper, style_id)
            font = get_editor_font()
            if bold: font.setBold(True)
            if italic: font.setItalic(True)
            lexer.setFont(font, style_id)

        if isinstance(lexer, QsciLexerPython):
            set_style(QsciLexerPython.Default, c_default)
            set_style(QsciLexerPython.Comment, c_comment)
            set_style(QsciLexerPython.CommentBlock, c_comment)
            set_style(QsciLexerPython.Number, c_number)
            set_style(QsciLexerPython.DoubleQuotedString, c_string)
            set_style(QsciLexerPython.SingleQuotedString, c_string)
            set_style(QsciLexerPython.Keyword, c_keyword)
            set_style(QsciLexerPython.TripleSingleQuotedString, c_string)
            set_style(QsciLexerPython.TripleDoubleQuotedString, c_string)
            set_style(QsciLexerPython.ClassName, c_class)
            set_style(QsciLexerPython.FunctionMethodName, c_function)
            set_style(QsciLexerPython.Operator, c_operator)
            set_style(QsciLexerPython.Identifier, c_identifier)
            set_style(QsciLexerPython.Decorator, QColor("#AF00DB"))
            
        elif isinstance(lexer, QsciLexerJSON):
            set_style(QsciLexerJSON.Default, c_default)
            set_style(QsciLexerJSON.Number, c_number)
            set_style(QsciLexerJSON.String, c_string)
            set_style(QsciLexerJSON.Property, QColor("#0451A5"))
            set_style(QsciLexerJSON.Operator, c_operator)
            set_style(QsciLexerJSON.Keyword, c_keyword)
            
        elif isinstance(lexer, (QsciLexerHTML, QsciLexerXML)):
             set_style(QsciLexerHTML.Default, c_default)
             set_style(QsciLexerHTML.Tag, QColor("#800000")) 
             set_style(QsciLexerHTML.Attribute, QColor("#FF0000")) 
             set_style(QsciLexerHTML.Value, QColor("#0000FF"))
             set_style(QsciLexerHTML.HTMLComment, c_comment)
             
        elif isinstance(lexer, QsciLexerJavaScript):
             set_style(QsciLexerJavaScript.Default, c_default)
             set_style(QsciLexerJavaScript.Comment, c_comment)
             set_style(QsciLexerJavaScript.CommentLine, c_comment)
             set_style(QsciLexerJavaScript.Keyword, c_keyword)
             set_style(QsciLexerJavaScript.DoubleQuotedString, c_string)
             set_style(QsciLexerJavaScript.SingleQuotedString, c_string)
             set_style(QsciLexerJavaScript.Number, c_number)

    def show_empty(self):
        """Show the empty/welcome state."""
        self.stack.setCurrentWidget(self.empty_widget)

    def close_tab(self, index):
        """Close the tab at the given index."""
        widget = self.tabs.widget(index)
        
        # Remove from tracking dict
        # We need to find the key (path) for this widget
        path_to_remove = None
        for path, w in self.open_files.items():
            if w == widget:
                path_to_remove = path
                break
        
        if path_to_remove:
            del self.open_files[path_to_remove]
            
        self.tabs.removeTab(index)
        
        # If no tabs left, show empty state
        if self.tabs.count() == 0:
            self.show_empty()

    def preview_file(self, file_node, abs_path=None):
        """
        Open or switch to a file tab.
        """
        if not file_node:
            # If explicit None passed, do nothing or show empty? 
            # Usually we don't clear everything on just a missing node unless intended.
            return
        
        name = file_node.get("name", "Unknown")
        
        # Use abs_path as key if available, otherwise name (fallback)
        key = abs_path if abs_path else name
        
        # 1. Check if already open
        if key in self.open_files:
            self.stack.setCurrentWidget(self.tabs)
            self.tabs.setCurrentWidget(self.open_files[key])
            return

        # 2. Create New Tab
        _, ext = os.path.splitext(name)
        ext = ext.lower()
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico', '.webp', '.tif', '.tiff'}
        
        new_widget = None
        
        if ext in image_extensions:
            if abs_path:
                new_widget = self._create_image_viewer(abs_path)
            else:
                # Fallback for image without path? Just show empty placeholder or message
                new_widget = QLabel("Image preview unavailable")
                new_widget.setAlignment(Qt.AlignCenter)
        else:
            # Code/Text
            content = file_node.get("content")
            if content is None:
                content = "// Content not available\n"
            new_widget = self._create_code_editor(content, ext)

        if new_widget:
            # Add to Tabs
            index = self.tabs.addTab(new_widget, name)
            self.tabs.setCurrentIndex(index)
            self.tabs.setTabToolTip(index, key) # Show full path on hover
            
            # Track it
            self.open_files[key] = new_widget
            
            # Ensure visible
            self.stack.setCurrentWidget(self.tabs)

    def reload_file_content(self, path, content=None):
        """Update the content of an open file (e.g. from external change)."""
        widget = self.open_files.get(path)
        if not widget:
            return

        if isinstance(widget, QsciScintilla):
            if content is None:
                return
            
            # Save state
            line, index = widget.getCursorPosition()
            first_line = widget.firstVisibleLine()
            
            # Check if content actually changed to avoid flicker
            if widget.text() != content:
                widget.setText(content)
                
                # Restore state
                widget.setCursorPosition(line, index)
                # setFirstVisibleLine not always available or behaves differently in some versions
                # verticalScrollBar().setValue(...) is more robust if needed, but try method first
                widget.setFirstVisibleLine(first_line)
            
        elif isinstance(widget, ZoomableImageViewer):
            if path and os.path.exists(path):
                pixmap = QPixmap(path)
                widget.set_image(pixmap)
