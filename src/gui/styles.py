"""
Modern dark theme for midi-macro GUI.
Inspired by professional DAW interfaces and modern code editors.
"""

# Color palette
COLORS = {
    # Backgrounds
    'bg_primary': '#1a1a1a',
    'bg_secondary': '#252525',
    'bg_tertiary': '#2d2d2d',
    'bg_dark': '#0d0d0d',
    
    # Accents
    'accent_primary': '#00a8ff',
    'accent_secondary': '#00ff88',
    'accent_warning': '#ffcc00',
    'accent_error': '#ff3366',
    'accent_success': '#00ff00',
    
    # Text
    'text_primary': '#ffffff',
    'text_secondary': '#aaaaaa',
    'text_muted': '#888888',
    'text_dark': '#666666',
    
    # Borders
    'border_light': '#404040',
    'border_medium': '#333333',
    'border_dark': '#222222',
    
    # Bank colors
    'bank_a': '#00a8ff',
    'bank_b': '#00ff88',
    'bank_c': '#ffcc00',
    'bank_d': '#ff3366',
}

DARK_THEME = f"""
/* Global */
QMainWindow {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLORS['border_medium']};
    background-color: {COLORS['bg_primary']};
    border-radius: 4px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_muted']};
    padding: 8px 24px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: bold;
    font-size: 13px;
    border: 1px solid {COLORS['border_medium']};
    border-bottom: none;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['accent_primary']};
    color: {COLORS['text_primary']};
    border-color: {COLORS['accent_primary']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
}}

/* MIDI Buttons */
MidiButton {{
    background-color: {COLORS['bg_tertiary']};
    border: 2px solid {COLORS['border_light']};
    border-radius: 6px;
    color: {COLORS['text_muted']};
    font-size: 11px;
    font-weight: bold;
    padding: 8px;
    min-width: 80px;
    min-height: 80px;
}}

MidiButton:hover {{
    border-color: {COLORS['accent_primary']};
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
}}

MidiButton[active="true"] {{
    background-color: {COLORS['accent_primary']};
    border-color: #33bbff;
    color: {COLORS['text_primary']};
}}

MidiButton[type="sound"] {{
    border-left: 4px solid {COLORS['accent_primary']};
}}

MidiButton[type="script"] {{
    border-left: 4px solid {COLORS['accent_secondary']};
}}

MidiButton[type="keyboard"] {{
    border-left: 4px solid {COLORS['accent_warning']};
}}

MidiButton[type="webhook"] {{
    border-left: 4px solid {COLORS['accent_error']};
}}

/* Text Editors */
QPlainTextEdit {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['accent_success']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
    padding: 8px;
    selection-background-color: #49483e;
}}

QPlainTextEdit:focus {{
    border-color: {COLORS['accent_primary']};
}}

/* Splitters */
QSplitter::handle {{
    background-color: {COLORS['border_medium']};
}}

QSplitter::handle:horizontal {{
    width: 4px;
}}

QSplitter::handle:vertical {{
    height: 4px;
}}

QSplitter::handle:hover {{
    background-color: {COLORS['accent_primary']};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background-color: {COLORS['bg_primary']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_light']};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #555555;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_primary']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border_light']};
    border-radius: 6px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: #555555;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_muted']};
    border-top: 1px solid {COLORS['border_medium']};
}}

QStatusBar::item {{
    border: none;
}}

/* Menu Bar */
QMenuBar {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border_medium']};
}}

QMenuBar::item {{
    padding: 4px 12px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['accent_primary']};
    border-radius: 4px;
}}

QMenu {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['accent_primary']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border_medium']};
    margin: 4px 8px;
}}

/* Tool Buttons */
QToolButton {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 6px;
    color: {COLORS['text_primary']};
}}

QToolButton:hover {{
    background-color: {COLORS['bg_secondary']};
    border-color: {COLORS['accent_primary']};
}}

QToolButton:checked {{
    background-color: {COLORS['accent_primary']};
}}

/* Labels */
QLabel {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
}}

QLabel#title {{
    color: {COLORS['text_primary']};
    font-size: 16px;
    font-weight: bold;
}}

/* Group Boxes */
QGroupBox {{
    border: 1px solid {COLORS['border_medium']};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: {COLORS['text_muted']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
}}

/* Push Buttons */
QPushButton {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_secondary']};
    border-color: {COLORS['accent_primary']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_primary']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_dark']};
    border-color: {COLORS['border_dark']};
}}

/* Combo Box */
QComboBox {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 80px;
}}

QComboBox:hover {{
    border-color: {COLORS['accent_primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    selection-background-color: {COLORS['accent_primary']};
}}

/* Line Edit */
QLineEdit {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    padding: 6px 8px;
}}

QLineEdit:focus {{
    border-color: {COLORS['accent_primary']};
}}

/* Check Box */
QCheckBox {{
    color: {COLORS['text_secondary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_light']};
    border-radius: 3px;
    background-color: {COLORS['bg_tertiary']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['accent_primary']};
}}

/* Radio Button */
QRadioButton {{
    color: {COLORS['text_secondary']};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_light']};
    border-radius: 9px;
    background-color: {COLORS['bg_tertiary']};
}}

QRadioButton::indicator:checked {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
}}

QRadioButton::indicator:hover {{
    border-color: {COLORS['accent_primary']};
}}

/* Progress Bar */
QProgressBar {{
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    background-color: {COLORS['bg_dark']};
    text-align: center;
    color: {COLORS['text_primary']};
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent_primary']};
    border-radius: 3px;
}}

/* Tool Tip */
QToolTip {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""

# Bank-specific button styles
BANK_STYLES = {
    'A': f"""
        QLabel {{
            color: {COLORS['bank_a']};
        }}
    """,
    'B': f"""
        QLabel {{
            color: {COLORS['bank_b']};
        }}
    """,
    'C': f"""
        QLabel {{
            color: {COLORS['bank_c']};
        }}
    """,
    'D': f"""
        QLabel {{
            color: {COLORS['bank_d']};
        }}
    """,
}
