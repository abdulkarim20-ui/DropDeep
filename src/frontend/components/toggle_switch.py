from PyQt5.QtWidgets import QAbstractButton
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen

class ToggleSwitch(QAbstractButton):
    def __init__(self, label="", parent=None):
        super().__init__(parent)
        self.setText(label)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Dimensions
        self._track_width = 36
        self._track_height = 18
        self._knob_size = 14
        
        # Animation for knob position
        self._knob_position = 0.0
        self._animation = QPropertyAnimation(self, b"knob_position", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        # Colors
        self._track_color_off = QColor("#D1D5DB")
        self._track_color_on = QColor("#007AFF")
        self._knob_color = QColor("#FFFFFF")
        
        # Connect state change
        self.toggled.connect(self._on_toggled)
        
        # Set minimum size
        self.setMinimumHeight(24)
    
    @pyqtProperty(float)
    def knob_position(self):
        return self._knob_position
    
    @knob_position.setter
    def knob_position(self, pos):
        self._knob_position = pos
        self.update()
    
    def _on_toggled(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._knob_position)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()
    
    def sizeHint(self):
        from PyQt5.QtCore import QSize
        from PyQt5.QtGui import QFontMetrics
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(self.text()) if self.text() else 0
        return QSize(self._track_width + 8 + text_width, max(24, self._track_height))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate track rectangle (left side)
        track_rect = QRectF(0, (self.height() - self._track_height) / 2, 
                           self._track_width, self._track_height)
        
        # Draw track background
        track_color = QColor.fromRgbF(
            self._track_color_off.redF() + (self._track_color_on.redF() - self._track_color_off.redF()) * self._knob_position,
            self._track_color_off.greenF() + (self._track_color_on.greenF() - self._track_color_off.greenF()) * self._knob_position,
            self._track_color_off.blueF() + (self._track_color_on.blueF() - self._track_color_off.blueF()) * self._knob_position
        )
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, self._track_height / 2, self._track_height / 2)
        
        # Draw knob
        knob_x_start = 2
        knob_x_end = self._track_width - self._knob_size - 2
        knob_x = knob_x_start + (knob_x_end - knob_x_start) * self._knob_position
        knob_y = (self.height() - self._knob_size) / 2
        
        painter.setBrush(self._knob_color)
        painter.drawEllipse(QRectF(knob_x, knob_y, self._knob_size, self._knob_size))
        
        # Draw text label
        if self.text():
            painter.setPen(QColor("#000000"))
            from PyQt5.QtGui import QFont
            font = QFont()
            font.setPointSize(9)
            font.setWeight(QFont.DemiBold)
            painter.setFont(font)
            text_rect = self.rect()
            text_rect.setLeft(self._track_width + 8)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())
