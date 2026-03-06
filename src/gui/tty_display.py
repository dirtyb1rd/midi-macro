"""
Script TTY display with 1000 line buffer.
Auto-clears after 1000 lines.
Optional file logging.
"""

import datetime
from collections import deque
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont


class TtyDisplay(QWidget):
    """Terminal-style display for script output."""
    
    # Signal to add line from other threads
    add_line_signal = pyqtSignal(str, str, bool)  # timestamp, text, is_error
    
    def __init__(self, log_to_file: bool = False, parent=None):
        super().__init__(parent)
        
        self.log_to_file = log_to_file
        self.log_file = None
        
        # Buffer (1000 lines)
        self.line_buffer = deque(maxlen=1000)
        
        # Setup UI
        self._setup_ui()
        
        # Connect signal
        self.add_line_signal.connect(self._add_line_slot)
        
        # Auto-scroll timer (to batch updates)
        self._pending_lines = []
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._flush_pending)
        self._update_timer.start(50)  # Update every 50ms
        
        # Open log file if requested
        if log_to_file:
            self._open_log_file()
    
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Text display
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(1000)  # Qt-level limit
        
        # Monospace font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        
        # Dark background
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d0d0d;
                color: #00ff00;
                border: 1px solid #333333;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        
        layout.addWidget(self.text_edit)
        
        # Control bar
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear all output")
        self.clear_btn.clicked.connect(self.clear)
        control_layout.addWidget(self.clear_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Log")
        self.save_btn.setToolTip("Save output to file")
        self.save_btn.clicked.connect(self._save_log)
        control_layout.addWidget(self.save_btn)
        
        # Pause checkbox
        self.pause_checkbox = QCheckBox("Pause")
        self.pause_checkbox.setToolTip("Pause auto-scroll")
        control_layout.addWidget(self.pause_checkbox)
        
        # Line count label
        self.line_count_label = QPushButton("Lines: 0")
        self.line_count_label.setEnabled(False)
        control_layout.addWidget(self.line_count_label)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
    
    def _open_log_file(self):
        """Open log file for writing."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"midi_macro_{timestamp}.log"
            self.log_file = open(filename, 'w')
            self.add_line("SYSTEM", f"Logging to: {filename}", False)
        except Exception as e:
            self.add_line("ERROR", f"Failed to open log file: {e}", True)
    
    def add_line(self, source: str, text: str, is_error: bool = False):
        """Add a line from any thread."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{source}] {text}"
        self.add_line_signal.emit(line, text, is_error)
        
        # Write to log file if enabled
        if self.log_file and not self.log_file.closed:
            try:
                self.log_file.write(line + "\n")
                self.log_file.flush()
            except:
                pass
    
    def _add_line_slot(self, line: str, text: str, is_error: bool):
        """Slot to add line from main thread."""
        self._pending_lines.append((line, is_error))
    
    def _flush_pending(self):
        """Flush pending lines to display."""
        if not self._pending_lines:
            return
        
        cursor = self.text_edit.textCursor()
        
        for line, is_error in self._pending_lines:
            # Format based on error status
            if is_error:
                # Red for errors
                fmt = QTextCharFormat()
                fmt.setForeground(QColor("#ff3333"))
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText(line + "\n", fmt)
            else:
                # Green for normal output
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText(line + "\n")
            
            # Add to buffer
            self.line_buffer.append(line)
        
        self._pending_lines.clear()
        
        # Update line count
        count = len(self.line_buffer)
        self.line_count_label.setText(f"Lines: {count}")
        
        # Auto-scroll if not paused
        if not self.pause_checkbox.isChecked():
            self.text_edit.verticalScrollBar().setValue(
                self.text_edit.verticalScrollBar().maximum()
            )
    
    def clear(self):
        """Clear all output."""
        self.text_edit.clear()
        self.line_buffer.clear()
        self.line_count_label.setText("Lines: 0")
    
    def _save_log(self):
        """Save current log to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "midi_macro.log", "Log files (*.log);;All files (*.*)"
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("\n".join(self.line_buffer))
                self.add_line("SYSTEM", f"Log saved to: {filename}", False)
            except Exception as e:
                self.add_line("ERROR", f"Failed to save log: {e}", True)
    
    def closeEvent(self, event):
        """Clean up on close."""
        if self.log_file and not self.log_file.closed:
            self.log_file.close()
        event.accept()
