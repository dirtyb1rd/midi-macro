"""
Custom MIDI button widget with blinking animation and tooltips.
"""

from typing import Optional
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QTimer


class MidiButton(QPushButton):
    """Custom button widget for MIDI controller buttons."""
    
    def __init__(self, note: int, parent=None):
        super().__init__(parent)
        self.note = note
        self._is_active = False
        self._blink_state = False
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        
        # Configuration
        self.button_type = "none"  # sound, script, keyboard, webhook
        self.sound_name = ""
        self.volume = 1.0
        self.current_bank = "A"  # Track which bank this button belongs to
        self.display_bank = "A"  # Which bank is currently being displayed
        
        # Setup - use fixed size to prevent layout shifts
        self.setFixedSize(100, 100)
        self.setToolTip(f"Button {note}: Unassigned")
        
        # Set size policy to fixed
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self._update_style()
    
    def set_bank(self, bank: str):
        """Set which bank this button belongs to."""
        self.current_bank = bank
    
    def set_display_bank(self, bank: str):
        """Set which bank is currently being displayed."""
        self.display_bank = bank
        # If we're not in the displayed bank, stop blinking
        if self.current_bank != bank:
            self._blink_timer.stop()
            self._blink_state = False
            self._is_active = False
            self._update_style()
    
    def set_config(self, name: str, button_type: str, volume: float = 1.0):
        """Set button configuration."""
        self.sound_name = name
        self.button_type = button_type
        self.volume = volume
        
        # Update tooltip
        tooltip = f"Button {self.note}: {name}"
        if button_type == "sound":
            tooltip += f"\nType: Sound (Vol: {volume:.0%})"
        elif button_type == "script":
            tooltip += f"\nType: Script"
        elif button_type == "keyboard":
            tooltip += f"\nType: Keyboard Shortcut"
        elif button_type == "webhook":
            tooltip += f"\nType: Webhook"
        
        self.setToolTip(tooltip)
        
        # Update display text (truncated if too long)
        display_text = name[:12] + "..." if len(name) > 12 else name
        self.setText(display_text)
        
        # Update style
        self.setProperty("type", button_type)
        self._update_style()
    
    def set_active(self, active: bool):
        """Set button active state (playing/running)."""
        # Only blink if we're in the currently displayed bank
        if active and self.current_bank != self.display_bank:
            return
        
        self._is_active = active
        self.setProperty("active", str(active).lower())
        
        if active:
            # Start blinking
            self._blink_timer.start(100)  # 100ms blink rate (10Hz)
        else:
            self._blink_timer.stop()
            self._blink_state = False
        
        self._update_style()
    
    def _toggle_blink(self):
        """Toggle blink state."""
        # Only blink if we're in the displayed bank
        if self.current_bank != self.display_bank:
            self._blink_timer.stop()
            self._blink_state = False
            self._update_style()
            return
        
        self._blink_state = not self._blink_state
        self._update_style()
    
    def flash_pressed(self):
        """Quick flash when button is pressed on controller."""
        # Only flash if we're in the currently displayed bank
        if self.current_bank != self.display_bank:
            return
        
        # Set bright color temporarily - keep 3px border to prevent layout shift
        self.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 3px solid #00a8ff;
                border-radius: 6px;
                color: #000000;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        # Reset after 100ms
        QTimer.singleShot(100, self._update_style)
    
    def _update_style(self):
        """Update button styling - always use 3px border to prevent layout shifts."""
        # Get border color based on type
        border_color = {
            "sound": "#00a8ff",
            "script": "#00ff88",
            "keyboard": "#ffcc00",
            "webhook": "#ff3366",
            "none": "#404040"
        }.get(self.button_type, "#404040")
        
        if self._is_active and self._blink_state:
            # Blinking on state - bright color with 3px border
            if self.button_type == "sound":
                bg_color = "#ff6b00"
                border_color = "#ff8533"
            elif self.button_type == "script":
                bg_color = "#00ff88"
                border_color = "#33ffaa"
            else:
                bg_color = "#00a8ff"
                border_color = "#33bbff"
            
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 3px solid {border_color};
                    border-radius: 6px;
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
        elif self._is_active:
            # Blinking off state - dimmed but still 3px border
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2d2d2d;
                    border: 3px solid #555555;
                    border-radius: 6px;
                    color: #888888;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
        else:
            # Standby state - dim with type indicator, always 3px border
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2d2d2d;
                    border: 3px solid {border_color};
                    border-radius: 6px;
                    color: #888888;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    border-color: #00a8ff;
                    background-color: #353535;
                }}
            """)
