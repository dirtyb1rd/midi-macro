"""
High-performance audio visualizer using PyQtGraph.
"""

import numpy as np
from collections import deque
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer, pyqtSignal
import pyqtgraph as pg


class AudioVisualizer(QWidget):
    """Real-time audio waveform visualizer using PyQtGraph."""
    
    level_changed = pyqtSignal(float)
    
    def __init__(self, parent=None, buffer_size: int = 1024, update_rate_ms: int = 30):
        super().__init__(parent)
        
        self.buffer_size = buffer_size
        self.update_rate_ms = update_rate_ms
        
        self._audio_buffer = deque(maxlen=buffer_size)
        self._audio_buffer.extend([0.0] * buffer_size)
        
        self._peak_level = 0.0
        self._peak_decay = 0.95
        
        self._setup_ui()
        self._setup_plot()
        
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(update_rate_ms)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMinimumHeight(120)
        self.plot_widget.setMaximumHeight(160)
        
        layout.addWidget(self.plot_widget)
    
    def _setup_plot(self):
        self.plot_widget.setBackground('#0d0d0d')
        
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.showAxis('left', False)
        self.plot_item.showAxis('bottom', False)
        
        self.plot_item.setYRange(-1.5, 1.5)
        self.plot_item.setXRange(0, self.buffer_size)
        
        pen = pg.mkPen(color='#00a8ff', width=2)
        self.waveform_curve = self.plot_item.plot(pen=pen)
        
        peak_pen = pg.mkPen(color='#ff3366', width=2, style=pg.QtCore.Qt.PenStyle.DotLine)
        self.peak_line = self.plot_item.plot(pen=peak_pen)
        
        zero_pen = pg.mkPen(color='#333333', width=1)
        self.zero_line = self.plot_item.plot(
            [0, self.buffer_size], [0, 0], pen=zero_pen
        )
        
        self._x_data = np.arange(self.buffer_size)
        self._y_data = np.zeros(self.buffer_size)
    
    def update_audio_data(self, sample: float):
        """Add a new audio sample to the buffer."""
        self._audio_buffer.append(sample)
        
        abs_sample = abs(sample)
        if abs_sample > self._peak_level:
            self._peak_level = abs_sample
    
    def _update_display(self):
        buffer_list = list(self._audio_buffer)
        
        if len(buffer_list) < self.buffer_size:
            buffer_list = [0.0] * (self.buffer_size - len(buffer_list)) + buffer_list
        
        self._y_data = np.array(buffer_list)
        
        self.waveform_curve.setData(self._x_data, self._y_data)
        
        peak_y = np.full(self.buffer_size, self._peak_level)
        self.peak_line.setData(self._x_data, peak_y)
        
        self._peak_level *= self._peak_decay
        
        self.level_changed.emit(self._peak_level)
    
    def set_buffer_size(self, size: int):
        self.buffer_size = size
        self._audio_buffer = deque(maxlen=size)
        self._audio_buffer.extend([0.0] * size)
        self._x_data = np.arange(size)
        self._y_data = np.zeros(size)
        self.plot_item.setXRange(0, size)
        self.zero_line.setData([0, size], [0, 0])
    
    def set_update_rate(self, rate_ms: int):
        self.update_rate_ms = rate_ms
        self._update_timer.stop()
        self._update_timer.start(rate_ms)
    
    def clear(self):
        self._audio_buffer.clear()
        self._audio_buffer.extend([0.0] * self.buffer_size)
        self._peak_level = 0.0
        self._update_display()
    
    def start(self):
        if not self._update_timer.isActive():
            self._update_timer.start(self.update_rate_ms)
    
    def stop(self):
        self._update_timer.stop()
