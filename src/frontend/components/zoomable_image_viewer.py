"""
Zoomable Image Viewer Widget - Like Microsoft Photos app.
Supports Ctrl + Mouse wheel zoom and proper centering.
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QSizePolicy, QApplication
from PyQt5.QtGui import QPixmap, QPainter, QWheelEvent, QTransform
from PyQt5.QtCore import Qt, QSize, QPoint


class ImageLabel(QLabel):
    """Custom label that can display images at various zoom levels."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(1, 1)
        self._pixmap = None
        self._scale = 1.0
    
    def setImage(self, pixmap, scale=1.0):
        """Set the image with a specific scale."""
        self._pixmap = pixmap
        self._scale = scale
        self._updateDisplay()
    
    def setScale(self, scale):
        """Update the scale and redraw."""
        self._scale = scale
        self._updateDisplay()
    
    def _updateDisplay(self):
        """Update the displayed pixmap based on current scale."""
        if self._pixmap is None or self._pixmap.isNull():
            self.clear()
            return
        
        # Calculate scaled size
        new_width = int(self._pixmap.width() * self._scale)
        new_height = int(self._pixmap.height() * self._scale)
        
        if new_width <= 0 or new_height <= 0:
            return
        
        # Scale the pixmap
        scaled = self._pixmap.scaled(
            new_width, new_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        super().setPixmap(scaled)
        self.setFixedSize(scaled.size())
    
    def getScale(self):
        return self._scale
    
    def getOriginalPixmap(self):
        return self._pixmap


class ZoomableImageViewer(QScrollArea):
    """
    A scrollable, zoomable image viewer widget.
    Supports Ctrl + Mouse wheel for zoom in/out.
    Image is always centered when smaller than viewport.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Zoom state
        self.min_scale = 0.1
        self.max_scale = 5.0
        self.current_scale = 1.0
        self.base_scale = 1.0  # The "fit to view" scale, shown as 100% to user
        
        # Setup scroll area
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F3F4F6;
            }
            
            /* Light scrollbars */
            QScrollBar:vertical {
                background: #E5E7EB;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #9CA3AF;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6B7280;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            
            QScrollBar:horizontal {
                background: #E5E7EB;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #9CA3AF;
                min-width: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #6B7280;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # Container widget to center the image
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        
        # Image label
        self.image_label = ImageLabel()
        self.image_label.setStyleSheet("background-color: transparent;")
        
        # Layout to center label in container
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label, 0, Qt.AlignCenter)
        
        self.setWidget(self.container)
        
        # Zoom indicator label (bottom-right corner)
        self.zoom_indicator = QLabel("100%", self)
        self.zoom_indicator.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.6);
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Segoe UI', sans-serif;
                padding: 4px 10px;
                border-radius: 4px;
            }
        """)
        self.zoom_indicator.setAlignment(Qt.AlignCenter)
        self.zoom_indicator.hide()  # Hidden until image is loaded
        
        # Original pixmap
        self.original_pixmap = None
    
    def _updateZoomIndicator(self):
        """Update the zoom indicator text and position."""
        # Calculate zoom percentage relative to base_scale (fit-to-view = 100%)
        if self.base_scale > 0:
            zoom_percent = int((self.current_scale / self.base_scale) * 100)
        else:
            zoom_percent = 100
        
        self.zoom_indicator.setText(f"{zoom_percent}%")
        self.zoom_indicator.adjustSize()
        
        # Position in bottom-right corner with padding
        margin = 12
        x = self.width() - self.zoom_indicator.width() - margin
        y = self.height() - self.zoom_indicator.height() - margin
        self.zoom_indicator.move(x, y)
        self.zoom_indicator.show()
    
    def set_image(self, pixmap):
        """Set the image to display."""
        if pixmap is None or pixmap.isNull():
            self.original_pixmap = None
            self.image_label.clear()
            self.image_label.setText("Could not load image")
            self.image_label.setStyleSheet("""
                font-size: 14px;
                color: #6B7280;
                background-color: transparent;
            """)
            self.image_label.setFixedSize(200, 50)
            self._updateContainerSize()
            return
        
        self.original_pixmap = pixmap
        
        # Calculate initial scale to fit in view
        self._fitToView()
        
        # Store this as the base scale (100% for user)
        self.base_scale = self.current_scale
        
        # Apply the image
        self.image_label.setImage(pixmap, self.current_scale)
        self.image_label.setStyleSheet("background-color: transparent;")
        
        # Update container size
        self._updateContainerSize()
        
        # Update zoom indicator
        self._updateZoomIndicator()
    
    def _fitToView(self):
        """Calculate scale to fit image in viewport."""
        if not self.original_pixmap:
            return
        
        # Get viewport size
        viewport_size = self.viewport().size()
        padding = 48
        
        available_width = max(100, viewport_size.width() - padding)
        available_height = max(100, viewport_size.height() - padding)
        
        img_width = self.original_pixmap.width()
        img_height = self.original_pixmap.height()
        
        if img_width == 0 or img_height == 0:
            self.current_scale = 1.0
            return
        
        # Calculate scale to fit
        scale_x = available_width / img_width
        scale_y = available_height / img_height
        
        # Use smaller scale to fit entirely, but don't upscale beyond 1.0
        self.current_scale = min(scale_x, scale_y, 1.0)
    
    def _updateContainerSize(self):
        """Update container size to allow proper scrolling and centering."""
        if not self.original_pixmap:
            self.container.setMinimumSize(self.viewport().size())
            return
        
        # Get the scaled image size
        scaled_width = int(self.original_pixmap.width() * self.current_scale)
        scaled_height = int(self.original_pixmap.height() * self.current_scale)
        
        # Get viewport size
        viewport_size = self.viewport().size()
        
        # Container should be at least viewport size (for centering small images)
        # or image size (for scrolling large images)
        container_width = max(scaled_width, viewport_size.width())
        container_height = max(scaled_height, viewport_size.height())
        
        self.container.setFixedSize(container_width, container_height)
    
    def _applyZoom(self):
        """Apply current zoom level."""
        if not self.original_pixmap:
            return
        
        # Get scroll position center before zoom
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()
        
        # Calculate center point ratio
        h_ratio = 0.5
        v_ratio = 0.5
        if h_bar.maximum() > 0:
            h_ratio = (h_bar.value() + self.viewport().width() / 2) / self.container.width()
        if v_bar.maximum() > 0:
            v_ratio = (v_bar.value() + self.viewport().height() / 2) / self.container.height()
        
        # Update image
        self.image_label.setImage(self.original_pixmap, self.current_scale)
        
        # Update container size
        self._updateContainerSize()
        
        # Update zoom indicator
        self._updateZoomIndicator()
        
        # Restore scroll position based on ratio
        QApplication.processEvents()  # Ensure layout is updated
        
        new_h = int(h_ratio * self.container.width() - self.viewport().width() / 2)
        new_v = int(v_ratio * self.container.height() - self.viewport().height() / 2)
        
        h_bar.setValue(max(0, new_h))
        v_bar.setValue(max(0, new_v))
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zoom (with Ctrl) or scroll."""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom with Ctrl + wheel
            delta = event.angleDelta().y()
            
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            
            event.accept()
        else:
            # Normal scroll
            super().wheelEvent(event)
    
    def zoom_in(self):
        """Zoom in by 15%."""
        new_scale = self.current_scale * 1.15
        if new_scale <= self.max_scale:
            self.current_scale = new_scale
            self._applyZoom()
    
    def zoom_out(self):
        """Zoom out by 15%."""
        new_scale = self.current_scale / 1.15
        if new_scale >= self.min_scale:
            self.current_scale = new_scale
            self._applyZoom()
    
    def zoom_fit(self):
        """Fit image to view."""
        self._fitToView()
        self._applyZoom()
    
    def zoom_actual(self):
        """Show image at 100% (actual size)."""
        self.current_scale = 1.0
        self._applyZoom()
    
    def resizeEvent(self, event):
        """Handle resize to update container size and zoom indicator position."""
        super().resizeEvent(event)
        if self.original_pixmap:
            self._updateContainerSize()
            self._updateZoomIndicator()
    
    def get_zoom_percent(self):
        """Get current zoom level as percentage."""
        return int(self.current_scale * 100)
