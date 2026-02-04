
# src/frontend/styles/theme.py

# ===== VS Code Inspired Palette =====
BG_APP = "#F3F4F6"          # App background (light gray)
BG_PANEL = "#FFFFFF"       # Panels
BG_SIDEBAR = "#F9FAFB"     # Tree sidebar
BG_HOVER = "#E5E7EB"       # Hover (important: not white)
BG_SELECTED = "#DCEAFE"    # Selection blue (soft)
BG_ACTIVE_LINE = "#EEF2FF"

BORDER_LIGHT = "#E5E7EB"
BORDER_FOCUS = "#3B82F6"

TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6B7280"

ACCENT = "#007AFF"         # VS Code / Windows blue
COLOR_PRIMARY = ACCENT     # Backward compatibility

# ===== Global Stylesheet =====
STYLESHEET = f"""
/* ================= APP ================= */
QMainWindow {{
    background-color: {BG_APP};
}}

QWidget {{
    font-family: "Segoe UI";
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

/* ================= PANELS ================= */
QFrame {{
    background-color: {BG_PANEL};
}}

/* Clear section boundaries */
.section {{
    border: 1px solid {BORDER_LIGHT};
    border-radius: 0px;
    background-color: {BG_PANEL};
}}

/* ================= SPLITTER ================= */
QSplitter::handle {{
    background-color: {BORDER_LIGHT};
}}
QSplitter::handle:hover {{
    background-color: {ACCENT};
}}

/* ================= SCROLLBAR ================= */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: #D1D5DB;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: #9CA3AF;
}}

/* ================= INPUT ================= */
QLineEdit {{
    background-color: #FFFFFF;
    border: 1px solid {BORDER_LIGHT};
    border-radius: 6px;
    padding: 6px 10px;
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}

/* ================= BUTTON ================= */
QPushButton {{
    background-color: #FFFFFF;
    border: 1px solid {BORDER_LIGHT};
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton:hover {{
    background-color: {BG_HOVER};
}}
QPushButton:pressed {{
    background-color: #D1D5DB;
}}
"""
