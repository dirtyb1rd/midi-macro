"""
Enhanced MIDI button widget with custom painting and smooth animations.
"""

from typing import Optional
from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen


class MidiButton(QPushButton):
    """Custom MIDI button widget with animated feedback and bank-aware display."""
    
    activated = pyqtSignal()
    deactivated = pyqtSignal()
    
    TYPE_COLORS = {
        "sound": QColor("#00a8ff"),
        "script": QColor("#00ff88"),
        "keyboard": QColor("#ffcc00"),
        "webhook": QColor("#ff3366"),
        "none": QColor("#404040"),
    }
    
    def __init__(self, note: int, parent=None):
        super().__init__(parent)
        
        self.note = note
        
        self._is_active = False
        self._button_type = "none"
        self._sound_name = ""
        self._volume = 1.0
        self._current_bank = "A"
        self._display_bank = "A"
        
        self._glow_intensity = 0.0
        self._pressed_scale = 1.0
        
        self._setup_animations()
        self._setup_widget()
    
    def _setup_widget(self):
        self.setFixedSize(100, 100)
        self.setToolTip(f"Button {self.note}: Unassigned")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCheckable(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def _setup_animations(self):
        self._glow_animation = QPropertyAnimation(self, b"glow_intensity", self)
        self._glow_animation.setDuration(150)
        self._glow_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        self._pressed_animation = QPropertyAnimation(self, b"pressed_scale", self)
        self._pressed_animation.setDuration(100)
        self._pressed_animation.setEasingCurve(QEasingCurve.Type.OutBounce)
    
    @pyqtProperty(float)
    def glow_intensity(self) -> float:
        return self._glow_intensity
    
    @glow_intensity.setter
    def glow_intensity(self, value: float):
        self._glow_intensity = max(0.0, min(1.0, value))
        self.update()
    
    @pyqtProperty(float)
    def pressed_scale(self) -> float:
        return self._pressed_scale
    
    @pressed_scale.setter
    def pressed_scale(self, value: float):
        self._pressed_scale = max(0.9, min(1.1, value))
        self.update()
    
    def set_bank(self, bank: str):
        self._current_bank = bank
    
    def set_display_bank(self, bank: str):
        self._display_bank = bank
        
        if self._current_bank != bank:
            self._stop_animations()
            self._is_active = False
            self._glow_intensity = 0.0
            self.update()
    
    def set_config(self, name: str, button_type: str, volume: float = 1.0):
        self._sound_name = name
        self._button_type = button_type
        self._volume = volume
        
        tooltip = f"Button {self.note}: {name}"
        if button_type == "sound":
            tooltip += f" (Vol: {volume:.0%})"
        elif button_type == "script":
            tooltip += " [Script]"
        elif button_type == "keyboard":
            tooltip += " [Key]"
        elif button_type == "webhook":
            tooltip += " [Webhook]"
        
        self.setToolTip(tooltip)
        
        display_text = name[:12] + "..." if len(name) > 12 else name
        self.setText(display_text)
        
        self.update()
    
    def set_active(self, active: bool):
        if active and self._current_bank != self._display_bank:
            return
        
        if self._is_active == active:
            return
        
        self._is_active = active
        
        if active:
            self.activated.emit()
            self._start_glow_animation()
        else:
            self.deactivated.emit()
            self._stop_glow_animation()
    
    def _start_glow_animation(self):
        self._glow_animation.stop()
        self._glow_animation.setStartValue(self._glow_intensity)
        self._glow_animation.setEndValue(1.0)
        self._glow_animation.start()
    
    def _stop_glow_animation(self):
        self._glow_animation.stop()
        self._glow_animation.setStartValue(self._glow_intensity)
        self._glow_animation.setEndValue(0.0)
        self._glow_animation.start()
    
    def _stop_animations(self):
        self._glow_animation.stop()
        self._pressed_animation.stop()
    
    def flash_pressed(self):
        if self._current_bank != self._display_bank:
            return
        
        self._pressed_animation.stop()
        self._pressed_animation.setStartValue(1.0)
        self._pressed_animation.setKeyValueAt(0.5, 0.95)
        self._pressed_animation.setEndValue(1.0)
        self._pressed_animation.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        scale = self._pressed_scale
        scaled_width = int(width * scale)
        scaled_height = int(height * scale)
        x_offset = (width - scaled_width) // 2
        y_offset = (height - scaled_height) // 2
        
        base_color = self.TYPE_COLORS.get(self._button_type, self.TYPE_COLORS["none"])
        
        if self._is_active:
            glow = self._glow_intensity
            active_color = QColor(
                int(base_color.red() * (1 - glow) + 255 * glow),
                int(base_color.green() * (1 - glow) + 150 * glow),
                int(base_color.blue() * (1 - glow) + 50 * glow),
            )
        else:
            active_color = base_color
        
        bg_color = QColor("#2d2d2d")
        if self._is_active:
            blend = self._glow_intensity * 0.3
            bg_color = QColor(
                int(bg_color.red() * (1 - blend) + active_color.red() * blend),
                int(bg_color.green() * (1 - blend) + active_color.green() * blend),
                int(bg_color.blue() * (1 - blend) + active_color.blue() * blend),
            )
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(active_color, 2))
        painter.drawRoundedRect(
            x_offset + 2, y_offset + 2,
            scaled_width - 4, scaled_height - 4,
            6, 6
        )
        
        if self._sound_name:
            painter.setPen(QPen(QColor("#ffffff") if self._is_active else QColor("#888888")))
            font = painter.font()
            font.setPointSize(11)
            font.setBold(True)
            painter.setFont(font)
            
            painter.drawText(
                x_offset + 4, y_offset + 4,
                scaled_width - 8, scaled_height - 8,
                Qt.AlignmentFlag.AlignCenter,
                self.text()
            )
        
        painter.end()
    
    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)
