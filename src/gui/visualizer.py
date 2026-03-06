"""
Real-time audio visualizer - DISABLED.

Disabled due to sync issues between 44.1kHz audio and 60fps display.
Proper solution would require double-buffering and audio buffer sync.
"""

import numpy as np
from collections import deque
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QLinearGradient


class AudioVisualizer(QWidget):
    """Real-time audio waveform display - CURRENTLY DISABLED."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Fixed-size buffer for stable display
        self.buffer_size = 512
        self.waveform_buffer = deque(maxlen=self.buffer_size)
        self.waveform_buffer.extend([0.0] * self.buffer_size)
        
        # Display buffer with smoothing
        self.display_buffer = [0.0] * self.buffer_size
        self.smoothing = 0.7  # Higher = more smoothing
        
        # Update timer (60fps)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(17)
        
        self.setMinimumHeight(120)
        self.setMaximumHeight(160)
    
    def update_audio_data(self, left_level: float, right_level: float, 
                          waveform_sample: float):
        """Called from audio thread to update levels."""
        self.waveform_buffer.append(waveform_sample)
    
    def _update_display(self):
        """Update smoothed buffer and trigger repaint."""
        # Apply smoothing to reduce jitter
        buffer_list = list(self.waveform_buffer)
        for i in range(len(buffer_list)):
            self.display_buffer[i] = (self.display_buffer[i] * self.smoothing + 
                                     buffer_list[i] * (1 - self.smoothing))
        
        self.update()
    
    def paintEvent(self, event):
        """Draw smooth waveform."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_y = height // 2
        
        # Background
        painter.fillRect(0, 0, width, height, QColor("#0d0d0d"))
        
        # Draw subtle grid
        pen = QPen(QColor("#222222"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(0, center_y, width, center_y)
        
        # Draw waveform
        if len(self.display_buffer) > 10:
            # Fixed number of points across width
            num_points = min(width, len(self.display_buffer))
            step = len(self.display_buffer) / num_points
            
            points = []
            for i in range(num_points):
                # Sample from buffer at fixed intervals
                idx = int(i * step)
                if idx < len(self.display_buffer):
                    x = i
                    y = center_y - int(self.display_buffer[idx] * (height * 0.4))
                    points.append((x, y))
            
            if len(points) > 2:
                # Create gradient
                gradient = QLinearGradient(0, 0, 0, height)
                gradient.setColorAt(0.0, QColor("#00a8ff"))
                gradient.setColorAt(0.5, QColor("#0088cc"))
                gradient.setColorAt(1.0, QColor("#006699"))
                
                # Build filled path
                path = QPainterPath()
                path.moveTo(points[0][0], center_y)
                path.lineTo(points[0][0], points[0][1])
                
                # Smooth curve through points
                for i in range(1, len(points) - 1):
                    # Catmull-Rom spline for smoothness
                    x = points[i][0]
                    y = points[i][1]
                    path.lineTo(x, y)
                
                path.lineTo(points[-1][0], points[-1][1])
                path.lineTo(points[-1][0], center_y)
                path.closeSubpath()
                
                # Fill
                painter.fillPath(path, gradient)
                
                # Draw outline
                outline_pen = QPen(QColor("#00ccff"))
                outline_pen.setWidth(2)
                painter.setPen(outline_pen)
                
                outline_path = QPainterPath()
                outline_path.moveTo(points[0][0], points[0][1])
                for i in range(1, len(points)):
                    outline_path.lineTo(points[i][0], points[i][1])
                painter.drawPath(outline_path)
        
        # Level bar at bottom
        if len(self.display_buffer) > 0:
            current_level = abs(self.display_buffer[-1])
            bar_width = int(width * current_level)
            
            if current_level > 0.8:
                color = QColor("#ff3333")
            elif current_level > 0.5:
                color = QColor("#ffcc00")
            else:
                color = QColor("#00ff88")
            
            painter.fillRect(0, height - 4, bar_width, 4, color)
