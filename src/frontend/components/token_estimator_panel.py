# src/frontend/components/token_estimator_panel.py

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt
import os

from src.config import resource_path
from src.backend.analyzers.token_logic import (
    estimate_tokens_from_text,
    analyze_models,
    overall_token_status
)

# --- Helpers ---

def get_provider_icon(provider: str):
    """Resolve icon pixmap for provider."""
    icon_map = {
        "Google Gemini": "gemini.png",
        "Anthropic Claude": "claude.png",
        "OpenAI": "openai.png"
    }
    filename = icon_map.get(provider)
    if not filename:
        return None

    path = resource_path(f"assets/{filename}")
    if os.path.exists(path):
        return QPixmap(path).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return None


class ModelRow(QWidget):
    """
    Minimal row: [Icon] [Name] ...... [Remaining + Status]
    """
    def __init__(self, icon_pixmap, name, remaining, status):
        super().__init__()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4) 
        layout.setSpacing(10)
        
        # Icon
        if icon_pixmap:
            lbl_icon = QLabel()
            lbl_icon.setPixmap(icon_pixmap)
            lbl_icon.setFixedSize(16, 16)
            lbl_icon.setStyleSheet("border: none; background: transparent;") 
            layout.addWidget(lbl_icon)
        else:
            layout.addSpacing(16)

        # Model Name
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-size: 13px; color: #374151; border: none;")
        layout.addWidget(lbl_name, 1)

        # Status Logic
        if status == "safe":
            color = "#16A34A" # Green
            symbol = "✔"
            rem_str = self._format_short(remaining)
            tooltip = "Remaining Context Window (Safe)"
        elif status == "tight":
            color = "#D97706" # Amber
            symbol = "⚠"
            rem_str = self._format_short(remaining)
            tooltip = "Remaining Context Window (Tight)"
        else: # overflow
            color = "#DC2626" # Red
            symbol = "✖"
            rem_str = "OVER LIMIT"
            tooltip = "Context Window Exceeded"

        lbl_status = QLabel(f"{rem_str} {symbol}")
        lbl_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_status.setToolTip(tooltip)
        lbl_status.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500; border: none;")
        layout.addWidget(lbl_status)

    def _format_short(self, num):
        if num >= 1_000_000:
            return f"+{num/1_000_000:.2f}M tokens" # Added 'tokens' suffix for clarity? No, might clatter.
            # User said: "proper at the label so user understand what is this"
            # Maybe just "1.2M left"
        if num >= 1_000:
            return f"+{num/1_000:.0f}K"
        return f"+{num}"


class ProviderGroup(QFrame):
    """
    A bordered box containing the provider header and its model rows.
    """
    def __init__(self, provider_name, models):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background-color: #FAFAFA;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10) # Increased margins slightly for cleaner corners
        layout.setSpacing(2) # Little spacing
        
        # Header Row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)
        
        lbl_header = QLabel(provider_name)
        lbl_header.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            color: #9CA3AF;
            text-transform: uppercase;
        """)
        header_layout.addWidget(lbl_header)
        header_layout.addStretch()
        
        # Legend/Label for clarity (Only once per group or handled elsewhere?)
        # User wants "label so user understand what is this"
        # Let's add "Remaining" small label in header?
        lbl_legend = QLabel("REMAINING")
        lbl_legend.setStyleSheet("""
            font-size: 10px;
            font-weight: 600;
            color: #D1D5DB;
        """)
        header_layout.addWidget(lbl_legend)
        
        layout.addLayout(header_layout)
        layout.addSpacing(4)
        
        # Rows
        for m in models:
            icon = get_provider_icon(provider_name)
            row = ModelRow(icon, m["name"], m["remaining"], m["status"])
            layout.addWidget(row)


class TokenEstimatorPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("TokenEstimatorPanel")
        self.setStyleSheet("""
            QFrame#TokenEstimatorPanel {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            QLabel {
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12) # Spacing between provider boxes

        # --- Header ---
        # --- Header ---
        self.lbl_title = QLabel("AI Token Estimator")
        # Default Neutral Style
        self.lbl_title.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 6px;
            background-color: #F3F4F6;
            color: #374151;
        """)
        self.layout.addWidget(self.lbl_title)

        self.lbl_summary = QLabel("Export size: —")
        self.lbl_summary.setStyleSheet("font-size: 12px; font-weight: 500; color: #6B7280; border: none;")
        self.layout.addWidget(self.lbl_summary)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #F3F4F6; border: none; height: 1px;")
        self.layout.addWidget(line)

        # Container for dynamic content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10) # Space between group boxes
        self.layout.addWidget(self.content_widget)

    def update_from_text(self, export_text: str):
        # 1. Estimate
        raw_token_count = estimate_tokens_from_text(export_text)
        self.lbl_summary.setText(f"Export size: ~{raw_token_count:,} tokens")

        # 2. Analyze
        analysis = analyze_models(raw_token_count)
        global_status = overall_token_status(analysis)

        # 2.1 Update Global Header Color
        if global_status == "safe":
            self.lbl_title.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 4px 8px;
                border-radius: 6px;
                background-color: #ECFDF5;
                color: #065F46;
            """)
        else:
            self.lbl_title.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 4px 8px;
                border-radius: 6px;
                background-color: #FEF2F2;
                color: #7F1D1D;
            """)

        # 3. Clear old UI
        self._clear_content()

        # 4. Group by Provider
        grouped = {}
        for item in analysis:
            grouped.setdefault(item["provider"], []).append(item)

        provider_order = ["Google Gemini", "Anthropic Claude", "OpenAI"]

        # 5. Build UI Sections (Boxes)
        for provider in provider_order:
            if provider not in grouped: continue
            
            # Create a box for this provider
            group_box = ProviderGroup(provider, grouped[provider])
            self.content_layout.addWidget(group_box)

        self.adjustSize()

    def _clear_content(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
