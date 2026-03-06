"""
YAML editor widget with syntax validation and crash recovery.
"""

import os
import yaml
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, 
    QPushButton, QLabel, QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter


class YamlHighlighter(QSyntaxHighlighter):
    """YAML syntax highlighter with Monokai-inspired colors."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Key format (cyan)
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(QColor("#66d9ef"))
        self.key_format.setFontWeight(QFont.Weight.Bold)
        
        # String format (green)
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#a6e22e"))
        
        # Number format (purple)
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#ae81ff"))
        
        # Comment format (gray)
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#75715e"))
    
    def highlightBlock(self, text):
        """Highlight YAML syntax."""
        import re
        
        # Comments
        for match in re.finditer(r'#.*$', text):
            self.setFormat(match.start(), match.end() - match.start(), self.comment_format)
        
        # Keys (before colon)
        for match in re.finditer(r'^\s*(\w+):', text):
            self.setFormat(match.start(1), match.end(1) - match.start(1), self.key_format)
        
        # Strings (quoted)
        for match in re.finditer(r'"[^"]*"', text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        # Numbers
        for match in re.finditer(r'\b\d+(\.\d+)?\b', text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)


class YamlEditor(QWidget):
    """
    YAML configuration editor widget with validation.
    
    Signals:
        config_saved: Emitted when configuration is saved successfully
        file_loaded: Emitted when a file is loaded, passes filepath
        validation_changed: Emitted when validation status changes, passes (is_valid, message)
    """
    
    config_saved = pyqtSignal()
    file_loaded = pyqtSignal(str)
    validation_changed = pyqtSignal(bool, str)
    
    def __init__(self, parent=None, show_title: bool = True):
        """
        Initialize YAML editor widget.
        
        Args:
            parent: Parent widget
            show_title: Whether to show the title bar
        """
        super().__init__(parent)
        
        self.current_file = None
        self.backup_content = None
        self._is_valid = True
        self._show_title = show_title
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title bar (optional)
        if self._show_title:
            title_frame = QFrame()
            title_frame.setObjectName("titleFrame")
            title_layout = QHBoxLayout(title_frame)
            title_layout.setContentsMargins(0, 0, 0, 0)
            
            self.title_label = QLabel("YAML Editor")
            self.title_label.setObjectName("titleLabel")
            title_layout.addWidget(self.title_label)
            
            title_layout.addStretch()
            
            self.file_label = QLabel("No file loaded")
            self.file_label.setObjectName("fileLabel")
            title_layout.addWidget(self.file_label)
            
            layout.addWidget(title_frame)
        else:
            # Just the file label
            self.file_label = QLabel("No file loaded")
            self.file_label.setObjectName("fileLabel")
            layout.addWidget(self.file_label)
        
        # Editor frame
        editor_frame = QFrame()
        editor_frame.setObjectName("editorFrame")
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # Text editor
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("# Load a YAML file or start typing...")
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Monospace font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        
        # Syntax highlighter
        self.highlighter = YamlHighlighter(self.text_edit.document())
        
        editor_layout.addWidget(self.text_edit)
        layout.addWidget(editor_frame, stretch=1)
        
        # Button bar
        button_frame = QFrame()
        button_frame.setObjectName("buttonFrame")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        # Load button
        self.load_btn = QPushButton("Load")
        self.load_btn.setToolTip("Load YAML file (Ctrl+O)")
        self.load_btn.setShortcut("Ctrl+O")
        self.load_btn.clicked.connect(self._load_file)
        button_layout.addWidget(self.load_btn)
        
        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setToolTip("Save with validation (Ctrl+S)")
        self.save_btn.setShortcut("Ctrl+S")
        self.save_btn.clicked.connect(self._save_file)
        button_layout.addWidget(self.save_btn)
        
        # Validate button
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.setToolTip("Check YAML syntax (Ctrl+Return)")
        self.validate_btn.setShortcut("Ctrl+Return")
        self.validate_btn.clicked.connect(self._validate)
        button_layout.addWidget(self.validate_btn)
        
        # Revert button
        self.revert_btn = QPushButton("Revert")
        self.revert_btn.setToolTip("Revert to last saved version (Ctrl+Z)")
        self.revert_btn.setShortcut("Ctrl+Z")
        self.revert_btn.clicked.connect(self._revert)
        button_layout.addWidget(self.revert_btn)
        
        button_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        button_layout.addWidget(self.status_label)
        
        layout.addWidget(button_frame)
    
    def _apply_styles(self):
        """Apply widget-specific styles."""
        self.setStyleSheet("""
            YamlEditor {
                background-color: #1a1a1a;
            }
            
            #titleFrame {
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px;
            }
            
            #titleLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            
            #fileLabel {
                color: #888888;
                font-size: 12px;
            }
            
            #editorFrame {
                background-color: #0d0d0d;
                border: 1px solid #333333;
                border-radius: 4px;
            }
            
            QPlainTextEdit {
                background-color: #0d0d0d;
                color: #f8f8f2;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
                selection-background-color: #49483e;
            }
            
            QPlainTextEdit:focus {
                border: 1px solid #00a8ff;
            }
            
            #buttonFrame {
                background-color: transparent;
            }
            
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #00a8ff;
            }
            
            QPushButton:pressed {
                background-color: #00a8ff;
            }
            
            #statusLabel {
                color: #00ff00;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            
            #statusLabel[valid="false"] {
                color: #ff3333;
            }
            
            #statusLabel[valid="true"] {
                color: #00ff00;
            }
        """)
    
    def load_file(self, filepath: str) -> bool:
        """
        Load a YAML file into the editor.
        
        Args:
            filepath: Path to the YAML file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            path = Path(filepath)
            if not path.exists():
                self._set_status(f"File not found: {filepath}", False)
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.text_edit.setPlainText(content)
            self.current_file = filepath
            self.backup_content = content
            
            self.file_label.setText(f"Editing: {filepath}")
            self._set_status("Loaded", True)
            self.file_loaded.emit(filepath)
            
            # Validate on load
            self._validate()
            
            return True
            
        except Exception as e:
            self._set_status(f"Error loading: {e}", False)
            return False
    
    def save_file(self, filepath: Optional[str] = None) -> bool:
        """
        Save the current content to a file.
        
        Args:
            filepath: Path to save to (uses current_file if None)
            
        Returns:
            True if saved successfully, False otherwise
        """
        target = filepath or self.current_file
        
        if not target:
            # Show save dialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save YAML", "", "YAML files (*.yaml *.yml);;All files (*.*)"
            )
            if not filename:
                return False
            target = filename
        
        # Validate first
        if not self._validate():
            reply = QMessageBox.question(
                self, "Invalid YAML",
                "YAML has errors. Save anyway?\n(You can revert later)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return False
        
        try:
            content = self.text_edit.toPlainText()
            
            # Atomic save: write to temp first
            temp_file = target + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Validate the temp file can be loaded
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                
                # Success - replace original
                os.replace(temp_file, target)
                self.backup_content = content
                self.current_file = target
                
                self._set_status("Saved", True)
                self.config_saved.emit()
                return True
                
            except yaml.YAMLError:
                os.remove(temp_file)
                self._set_status("Save failed: Invalid YAML", False)
                QMessageBox.critical(self, "Save Failed", 
                    "File was not saved because it contains invalid YAML.\n"
                    "Fix the errors and try again.")
                return False
                
        except Exception as e:
            self._set_status(f"Save error: {e}", False)
            return False
    
    def get_content(self) -> str:
        """Get the current editor content."""
        return self.text_edit.toPlainText()
    
    def set_content(self, content: str):
        """Set the editor content."""
        self.text_edit.setPlainText(content)
        self._validate()
    
    def is_valid(self) -> bool:
        """Check if current content is valid YAML."""
        return self._is_valid
    
    def get_current_file(self) -> Optional[str]:
        """Get currently loaded file path."""
        return self.current_file
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self.text_edit.toPlainText() != self.backup_content
    
    def _load_file(self):
        """Open file dialog to load YAML."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open YAML", "", "YAML files (*.yaml *.yml);;All files (*.*)"
        )
        if filename:
            self.load_file(filename)
    
    def _save_file(self):
        """Save current file."""
        self.save_file()
    
    def _validate(self) -> bool:
        """Validate YAML syntax."""
        content = self.text_edit.toPlainText()
        
        try:
            yaml.safe_load(content)
            self._is_valid = True
            self._set_status("Valid", True)
            self.validation_changed.emit(True, "Valid YAML")
            return True
        except yaml.YAMLError as e:
            self._is_valid = False
            error_msg = str(e).split('\n')[0]
            self._set_status(f"Invalid: {error_msg}", False)
            self.validation_changed.emit(False, error_msg)
            return False
    
    def _revert(self):
        """Revert to last saved version."""
        if self.backup_content is None:
            self._set_status("Nothing to revert to", False)
            return
        
        if not self.has_unsaved_changes():
            self._set_status("No changes to revert", True)
            return
        
        reply = QMessageBox.question(
            self, "Confirm Revert",
            "Revert to last saved version?\nUnsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.text_edit.setPlainText(self.backup_content)
            self._set_status("Reverted", True)
    
    def _set_status(self, message: str, is_valid: bool):
        """Set status label with appropriate styling."""
        self.status_label.setText(message)
        self.status_label.setProperty("valid", "true" if is_valid else "false")
        # Force style refresh
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)