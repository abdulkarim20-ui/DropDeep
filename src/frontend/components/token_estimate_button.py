from PyQt5.QtWidgets import QPushButton, QMenu, QWidgetAction, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import os

from src.config import resource_path
from src.frontend.components.token_estimator_panel import TokenEstimatorPanel
from src.backend.exporter import generate_full_text, generate_tree_text
from src.backend.analyzers.token_logic import (
    estimate_tokens_from_text,
    analyze_models,
    overall_token_status
)

class TokenEstimateButton(QPushButton):
    """
    A dropdown button that reveals the Token Estimator Panel.
    """
    
    def __init__(self, parent=None, data_getter=None, format_getter=None):
        """
        Args:
            parent: Parent widget
            data_getter: Callable that returns the current project data (dict).
            format_getter: Callable returning list of selected formats.
        """
        super().__init__("Token Estimate", parent)
        self.data_getter = data_getter
        self.format_getter = format_getter
        self.last_status = None # 'safe' or 'overflow'
        
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(140, 40)
        
        # Panel Instance
        self.panel = TokenEstimatorPanel(self)
        
        self._apply_styles()
        self._build_menu()
        
    def _apply_styles(self, state="closed"):
        # Resolve Icons
        if state == "open":
            raw_path = resource_path("assets/chevron_up.png")
            icon_path = raw_path.replace("\\", "/") if os.path.exists(raw_path) else ""
        else:
            raw_path = resource_path("assets/chevron_left.png")
            icon_path = raw_path.replace("\\", "/") if os.path.exists(raw_path) else ""
            
        # Default Neutral
        bg_col = "#F3F4F6"
        hover_col = "#E5E7EB"
        txt_col = "#374151"
        brd_col = "#E5E7EB"

        # Apply Status Colors if set
        if self.last_status == "safe":
            bg_col = "#ECFDF5"
            hover_col = "#D1FAE5"
            txt_col = "#065F46" 
            brd_col = "#10B981" 
        elif self.last_status == "overflow":
            bg_col = "#FEF2F2"
            hover_col = "#FEE2E2"
            txt_col = "#7F1D1D"
            brd_col = "#EF4444"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_col};
                color: {txt_col};
                border: 1px solid {brd_col};
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                padding-left: 10px;
                padding-right: 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {hover_col};
                border-color: #D1D5DB;
            }}
            QPushButton::menu-indicator {{ 
                subcontrol-origin: padding; 
                subcontrol-position: right center;
                margin-right: 10px;
                width: 12px;
                image: url({icon_path});
            }}
        """)

    def _build_menu(self):
        token_menu = QMenu(self)
        
        # Enable transparency to remove standard OS shadow/square corners
        token_menu.setWindowFlags(token_menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        token_menu.setAttribute(Qt.WA_TranslucentBackground)
        
        # Clean menu style - transparent so only the panel border shows
        token_menu.setStyleSheet("""
            QMenu {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px; 
            }
        """)

        # Container Action for the Panel
        container_action = QWidgetAction(token_menu)
        container_action.setDefaultWidget(self.panel)
        token_menu.addAction(container_action)
        
        # Signals
        token_menu.aboutToShow.connect(self._on_menu_show)
        token_menu.aboutToHide.connect(lambda: self._apply_styles("closed"))
        
        self.setMenu(token_menu)

    def _on_menu_show(self):
        # When opening, force 'open' state during update
        self.update_estimate(state_override="open")

    def update_estimate(self, state_override=None):
        """
        Recalculates estimate based on current data/formats and updates UI.
        Public method called by MainWindow.
        Args:
            state_override: If set, forces the button style to this state ('open'/'closed').
                            If None, detects state from menu visibility.
        """
        if not self.data_getter:
            return
            
        data = self.data_getter()
        if not data:
            self.panel.update_from_text("")
            self.last_status = None
            self._apply_styles("closed")
            return

        # Determine Text Source
        formats = self.format_getter() if self.format_getter else ["txt_full"]
        
        # Exact logic: Tree only -> Tree text. Default/Full -> Full text.
        if "txt_tree" in formats and "txt_full" not in formats:
            text = generate_tree_text(data)
        else:
            text = generate_full_text(data)
            
        # 1. Update Panel
        self.panel.update_from_text(text)
        
        # 2. Update Button Status (Sync)
        # Re-calc locally to determine button color
        count = estimate_tokens_from_text(text)
        analysis = analyze_models(count)
        self.last_status = overall_token_status(analysis)
        
        # Refresh style
        if state_override:
            state = state_override
        else:
            state = "open" if self.menu() and self.menu().isVisible() else "closed"
            
        self._apply_styles(state)

