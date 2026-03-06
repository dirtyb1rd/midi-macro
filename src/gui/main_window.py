"""
Main window for midi-macro GUI.
Integrates all components: button grid, TTY, YAML editor.
"""

import sys
import signal
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QSplitter, QTabWidget, QStatusBar,
    QLabel, QMenuBar, QMenu, QMessageBox,
    QApplication, QToolBar, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QMetaObject
from PyQt6.QtGui import QAction, QKeySequence, QShortcut

# Import our GUI components
from midi_button_enhanced import MidiButton
from visualizer_pyqtgraph import AudioVisualizer
from tty_display import TtyDisplay
from yaml_editor import YamlEditor
from styles import DARK_THEME

# Import existing modules
from midi_handler import MidiHandler
from bank_manager import BankManager
from soundboard import Soundboard
from action_runner import ActionRunner
import yaml


# AudioCaptureThread disabled - see _setup_ui() for visualizer notes
# class AudioCaptureThread(QThread):
#     """Thread to capture audio levels for visualizer."""
#     
#     level_update = pyqtSignal(float, float, float)  # left, right, waveform_sample
#     
#     def __init__(self, soundboard):
#         super().__init__()
#         self.soundboard = soundboard
#         self._running = True
#     
#     def run(self):
#         """Capture audio levels at ~60fps."""
#         while self._running:
#             if self.soundboard and hasattr(self.soundboard, '_active_sounds'):
#                 try:
#                     # Calculate levels from active sounds
#                     with self.soundboard._lock:
#                         total_samples = 0
#                         mixed_sample = 0.0
#                         
#                         for sound_data, position, volume in self.soundboard._active_sounds:
#                             if position < len(sound_data):
#                                 # Get stereo samples
#                                 left = sound_data[position][0] * volume
#                                 right = sound_data[position][1] * volume
#                                 mixed_sample = (left + right) / 2
#                                 total_samples += 1
#                         
#                         if total_samples > 0:
#                             # Calculate RMS-like level
#                             level = min(1.0, abs(mixed_sample))
#                             self.level_update.emit(level, level, mixed_sample)
#                         else:
#                             self.level_update.emit(0.0, 0.0, 0.0)
#                 except:
#                     pass
#             
#             time.sleep(0.016)  # ~60fps
#     
#     def stop(self):
#         """Stop the thread."""
#         self._running = False


class MainWindow(QMainWindow):
    """Main application window with full MIDI/audio integration."""
    
    # Signals for thread-safe GUI updates
    midi_button_pressed_signal = pyqtSignal(str, int)  # bank, note
    midi_bank_switched_signal = pyqtSignal(str)  # bank
    script_output_signal = pyqtSignal(str, str, bool)  # source, text, is_error
    
    def __init__(self, log_to_file: bool = False):
        super().__init__()
        
        self.setWindowTitle("Midi Fighter 3D - Macro Controller")
        self.setMinimumSize(1200, 800)
        
        # Current state
        self.current_bank = "A"
        self.buttons: Dict[int, MidiButton] = {}
        self.config = None
        self._bank_data = {}
        
        # Backend components
        self.soundboard = None
        self.action_runner = None
        self.bank_manager = None
        self.midi_handler = None
        self.audio_thread = None
        
        # Active sounds tracking
        self.active_sounds = set()  # (bank, note) tuples
        
        # Setup UI first
        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        
        # Connect signals
        self.midi_button_pressed_signal.connect(self._on_midi_button_pressed)
        self.midi_bank_switched_signal.connect(self._on_midi_bank_switched)
        self.script_output_signal.connect(self._on_script_output)
        
        # Apply theme
        self.setStyleSheet(DARK_THEME)
        
        # Initialize backend
        self._init_backend()
        self._load_config()
        
        # Update timer for button states
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_button_states)
        self.update_timer.start(16)  # 60fps
    
    def _init_backend(self):
        """Initialize and connect all backend components."""
        try:
            # Load config first
            config_path = Path(__file__).parent.parent.parent / "config" / "main.yaml"
            with open(config_path) as f:
                main_config = yaml.safe_load(f)
            self.config = main_config
            
            # Load all bank configs
            all_sounds = {}
            all_banks = {}
            
            for bank_name, bank_file in main_config.get("banks", {}).items():
                if bank_file is None:
                    all_banks[bank_name] = {}
                    continue
                
                bank_path = Path(__file__).parent.parent.parent / bank_file
                if bank_path.exists():
                    with open(bank_path) as f:
                        bank_config = yaml.safe_load(f)
                    
                    bank_sounds = bank_config.get("sounds", {})
                    all_sounds.update(bank_sounds)
                    all_banks[bank_name] = bank_config.get("mappings", {})
                    self._bank_data[bank_name] = bank_config
            
            # Initialize soundboard
            self.tty_display.add_line("INIT", "Loading soundboard...", False)
            self.soundboard = Soundboard(
                sounds_config=all_sounds,
                banks_config=all_banks
            )
            self.tty_display.add_line("INIT", f"Loaded {len(self.soundboard.sounds)} sounds", False)
            
            # Connect soundboard to visualizer
            self.soundboard.set_audio_callback(self.visualizer.update_audio_data)
            self.tty_display.add_line("INIT", "Audio visualizer connected", False)
            
            # Initialize action runner with TTY capture
            self.tty_display.add_line("INIT", "Loading action runner...", False)
            self.action_runner = ActionRunner(scripts_dir="scripts")
            # Patch action runner to capture output
            self._patch_action_runner()
            
            # Initialize bank manager with callbacks
            self.tty_display.add_line("INIT", "Initializing bank manager...", False)
            self.bank_manager = BankManager(
                bank_callback=self._bank_callback,
                button_callback=self._button_callback
            )
            
            # Initialize MIDI handler
            port_name = main_config["midi"]["port_name"]
            self.tty_display.add_line("INIT", f"Connecting to MIDI: {port_name}...", False)
            self.midi_handler = MidiHandler(
                port_name=port_name,
                bank_manager=self.bank_manager
            )
            self.midi_handler.start()
            
            # Update status
            self.midi_status.setText("MIDI: ●")
            self.midi_status.setStyleSheet("color: #00ff00;")  # Green = connected
            self.audio_status.setText("Audio: ●")
            self.audio_status.setStyleSheet("color: #00ff00;")
            
            self.tty_display.add_line("INIT", "System ready!", False)
            self.status_bar.showMessage("Ready - Connected to Midi Fighter 3D")
            
            # Audio capture thread for visualizer - DISABLED
            # See visualizer notes in _setup_ui() for details on why this is disabled
            # self.audio_thread = AudioCaptureThread(self.soundboard)
            # self.audio_thread.level_update.connect(self._update_visualizer)
            # self.audio_thread.start()
            
        except Exception as e:
            self.tty_display.add_line("INIT", f"Error: {e}", True)
            self.status_bar.showMessage(f"Initialization error: {e}")
            QMessageBox.critical(self, "Initialization Error", str(e))
    
    def _patch_action_runner(self):
        """Patch action runner to capture script output to TTY."""
        original_run_script = self.action_runner._run_script
        
        def patched_run_script(config):
            """Wrapped script execution with TTY capture."""
            filename = config.get("file", "unknown")
            display_name = filename.replace('.sh', '').replace('.py', '').replace('_', ' ').title()
            
            # Send start notification
            self.script_output_signal.emit("SCRIPT", f"▶️ Starting: {display_name}", False)
            
            try:
                # Run with capture
                import subprocess
                import threading
                
                scripts_dir = Path(self.action_runner.scripts_dir)
                script_path = scripts_dir / filename
                
                if not script_path.exists():
                    script_path = Path(filename)
                
                args = config.get("args", [])
                blocking = config.get("blocking", False)
                
                cmd = ["bash", str(script_path)] + args
                
                if blocking:
                    # Run synchronously with capture
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=30
                    )
                    
                    # Output stdout
                    if result.stdout:
                        for line in result.stdout.strip().split('\n'):
                            self.script_output_signal.emit(filename[:20], line, False)
                    
                    # Output stderr
                    if result.stderr:
                        for line in result.stderr.strip().split('\n'):
                            self.script_output_signal.emit(filename[:20], line, True)
                    
                    if result.returncode == 0:
                        self.script_output_signal.emit("SCRIPT", f"✅ {display_name} completed", False)
                    else:
                        self.script_output_signal.emit("SCRIPT", f"❌ {display_name} failed (code {result.returncode})", True)
                    
                    return result.returncode == 0
                else:
                    # Run in background with threaded capture
                    def capture_output(process):
                        for line in iter(process.stdout.readline, ''):
                            if line:
                                self.script_output_signal.emit(filename[:20], line.strip(), False)
                        process.stdout.close()
                        for line in iter(process.stderr.readline, ''):
                            if line:
                                self.script_output_signal.emit(filename[:20], line.strip(), True)
                        process.stderr.close()
                    
                    process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, bufsize=1
                    )
                    
                    # Start capture threads
                    threading.Thread(target=capture_output, args=(process,), daemon=True).start()
                    
                    script_key = f"{filename}_{threading.current_thread().ident}"
                    with self.action_runner._lock:
                        self.action_runner._running_scripts[script_key] = process
                    
                    self.script_output_signal.emit("SCRIPT", f"🔄 {display_name} running in background", False)
                    return True
                    
            except Exception as e:
                self.script_output_signal.emit("SCRIPT", f"❌ Error: {e}", True)
                return False
        
        # Replace the method
        self.action_runner._run_script = patched_run_script
    
    def _bank_callback(self, bank):
        """Called when bank switches on device."""
        self.midi_bank_switched_signal.emit(bank)
    
    def _button_callback(self, bank, note):
        """Called when button pressed on device."""
        self.midi_button_pressed_signal.emit(bank, note)
    
    def _on_midi_bank_switched(self, bank):
        """Handle bank switch in GUI thread."""
        self.current_bank = bank
        self._switch_bank_display(bank)
    
    def _on_midi_button_pressed(self, bank, note):
        """Handle button press in GUI thread."""
        # Set the bank on the button so it knows if it should flash
        if note in self.buttons:
            btn = self.buttons[note]
            btn.set_bank(bank)
            btn.flash_pressed()
        
        # Get button config
        if bank in self._bank_data:
            bank_data = self._bank_data[bank]
            mappings = bank_data.get("mappings", {})
            
            # Check if note is in mappings (keys are integers from YAML)
            if note in mappings:
                mapping = mappings[note]
                
                # Play sound if configured
                if isinstance(mapping, dict) and "sound" in mapping:
                    sound_name = mapping["sound"]
                    self.tty_display.add_line("AUDIO", f"Playing: {sound_name}", False)
                    
                    # Track active sound
                    self.active_sounds.add((bank, note))
                    if note in self.buttons:
                        self.buttons[note].set_active(True)
                    
                    # Play sound
                    try:
                        self.soundboard.play(bank, note)
                    except Exception as e:
                        self.tty_display.add_line("AUDIO", f"Error: {e}", True)
                
                # Execute action if configured
                if isinstance(mapping, dict) and "action" in mapping:
                    action_config = mapping["action"]
                    self.action_runner.execute(action_config)
            else:
                print(f"DEBUG: Note {note} not found in mappings for bank {bank}")
    
    def _on_script_output(self, source, text, is_error):
        """Handle script output in GUI thread."""
        self.tty_display.add_line(source, text, is_error)
    
    # def _update_visualizer(self, left, right, waveform):
    #     """Update audio visualizer - DISABLED."""
    #     # See _setup_ui() for detailed notes on visualizer issues
    #     # self.visualizer.update_audio_data(left, right, waveform)
    #     pass
    
    def _update_button_states(self):
        """Update button active states at 60fps."""
        # Check which sounds are still active
        if self.soundboard:
            try:
                with self.soundboard._lock:
                    active = set()
                    for sound_data, position, volume in self.soundboard._active_sounds:
                        # Find which button this sound belongs to
                        for bank in ["A", "B", "C", "D"]:
                            if bank in self.soundboard.banks:
                                for note, sound_name in self.soundboard.banks[bank].items():
                                    if self.soundboard.sounds.get(sound_name) and self.soundboard.sounds[sound_name][0] is sound_data:
                                        active.add((bank, note))
                    
                    # Update button states
                    for bank, note in self.active_sounds:
                        if (bank, note) not in active:
                            if note in self.buttons:
                                self.buttons[note].set_active(False)
                    
                    self.active_sounds = active
                    
                    # Update active sounds count
                    self.active_sounds_label.setText(f"Active: {len(active)}")
                    
            except:
                pass
    
    def _setup_ui(self):
        """Setup the main UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top section: Bank indicator
        bank_layout = QHBoxLayout()
        self.bank_label = QLabel("Bank: A")
        self.bank_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #00a8ff;
                padding: 10px;
                background-color: #2d2d2d;
                border-radius: 6px;
            }
        """)
        bank_layout.addWidget(self.bank_label)
        bank_layout.addStretch()
        main_layout.addLayout(bank_layout)
        
        # Middle section: Button grid
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(8)
        
        # Create 16 buttons (4x4 grid)
        for i in range(16):
            row = i // 4
            col = i % 4
            btn = MidiButton(i)
            btn.setEnabled(False)  # Display only - physical device controls
            btn.setToolTip(f"Button {i}: Press on device to activate")
            self.buttons[i] = btn
            grid_layout.addWidget(btn, row, col)
        
        main_layout.addWidget(grid_container, stretch=2)
        
        # Bottom section: Tabbed displays
        bottom_tabs = QTabWidget()
        
        # Visualizer tab - Audio waveform display
        self.visualizer = AudioVisualizer(buffer_size=1024, update_rate_ms=30)
        bottom_tabs.addTab(self.visualizer, "Audio Visualizer")
        
        # TTY tab - Script output
        self.tty_display = TtyDisplay(log_to_file="--log" in sys.argv)
        bottom_tabs.addTab(self.tty_display, "Script Output")
        
        # YAML editor tab - auto-load main config
        self.yaml_editor = YamlEditor(show_title=False)
        self.yaml_editor.config_saved.connect(self._reload_config)
        bottom_tabs.addTab(self.yaml_editor, "Config Editor")
        
        # Auto-load main config file
        config_path = Path(__file__).parent.parent.parent / "config" / "main.yaml"
        if config_path.exists():
            self.yaml_editor.load_file(str(config_path))
        
        main_layout.addWidget(bottom_tabs, stretch=1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status indicators
        self.midi_status = QLabel("MIDI: ●")
        self.midi_status.setStyleSheet("color: #ff3333;")
        self.status_bar.addWidget(self.midi_status)
        
        self.audio_status = QLabel("Audio: ●")
        self.audio_status.setStyleSheet("color: #ff3333;")
        self.status_bar.addWidget(self.audio_status)
        
        self.active_sounds_label = QLabel("Active: 0")
        self.status_bar.addWidget(self.active_sounds_label)
        
        self.status_bar.showMessage("Initializing...")
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        load_action = QAction("Load Config...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_config_dialog)
        file_menu.addAction(load_action)
        
        reload_action = QAction("Reload Config", self)
        reload_action.setShortcut("Ctrl+R")
        reload_action.triggered.connect(self._reload_config)
        file_menu.addAction(reload_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        toggle_visualizer = QAction("Show Visualizer", self)
        toggle_visualizer.setCheckable(True)
        toggle_visualizer.setChecked(True)
        view_menu.addAction(toggle_visualizer)
        
        toggle_tty = QAction("Show Script Output", self)
        toggle_tty.setCheckable(True)
        toggle_tty.setChecked(True)
        view_menu.addAction(toggle_tty)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # F1-F4 for bank switching (GUI display only)
        QShortcut(QKeySequence("F1"), self, lambda: self._switch_bank_display("A"))
        QShortcut(QKeySequence("F2"), self, lambda: self._switch_bank_display("B"))
        QShortcut(QKeySequence("F3"), self, lambda: self._switch_bank_display("C"))
        QShortcut(QKeySequence("F4"), self, lambda: self._switch_bank_display("D"))
    
    def _load_config(self):
        """Load configuration from YAML files."""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "main.yaml"
            
            with open(config_path) as f:
                main_config = yaml.safe_load(f)
            
            self.config = main_config
            
            # Load bank configs
            banks_config = main_config.get("banks", {})
            for bank_name, bank_file in banks_config.items():
                if bank_file:
                    bank_path = Path(__file__).parent.parent.parent / bank_file
                    if bank_path.exists():
                        with open(bank_path) as f:
                            bank_data = yaml.safe_load(f)
                        self._bank_data[bank_name] = bank_data
            
            # Update display for current bank
            self._update_buttons_for_bank(self.current_bank)
            
            self.status_bar.showMessage("Configuration loaded")
            
        except Exception as e:
            self.tty_display.add_line("CONFIG", f"Error: {e}", True)
    
    def _update_buttons_for_bank(self, bank: str):
        """Update button display for selected bank."""
        # First, update display bank for all buttons
        for btn in self.buttons.values():
            btn.set_display_bank(bank)
        
        if bank not in self._bank_data:
            for btn in self.buttons.values():
                btn.set_config("Empty", "none")
                btn.set_bank(bank)
            return
        
        bank_data = self._bank_data[bank]
        mappings = bank_data.get("mappings", {})
        sounds = bank_data.get("sounds", {})
        
        for note_str, mapping in mappings.items():
            note = int(note_str)
            if note not in self.buttons:
                continue
            
            btn = self.buttons[note]
            btn.set_bank(bank)  # Set which bank this button belongs to
            
            if isinstance(mapping, dict):
                sound_name = mapping.get("sound")
                if sound_name and sound_name in sounds:
                    sound_data = sounds[sound_name]
                    volume = mapping.get("volume", sound_data.get("volume", 1.0))
                    btn.set_config(sound_name, "sound", volume)
                
                action = mapping.get("action")
                if action:
                    action_type = action.get("type", "unknown")
                    btn.set_config(action.get("file", action_type), action_type)
            elif isinstance(mapping, str):
                if mapping in sounds:
                    sound_data = sounds[mapping]
                    btn.set_config(mapping, "sound", sound_data.get("volume", 1.0))
    
    def _switch_bank_display(self, bank: str):
        """Switch bank display."""
        self.current_bank = bank
        self.bank_label.setText(f"Bank: {bank}")
        
        colors = {"A": "#00a8ff", "B": "#00ff88", "C": "#ffcc00", "D": "#ff3366"}
        self.bank_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {colors.get(bank, "#ffffff")};
                padding: 10px;
                background-color: #2d2d2d;
                border-radius: 6px;
            }}
        """)
        
        self._update_buttons_for_bank(bank)
        self.tty_display.add_line("GUI", f"Switched to Bank {bank}", False)
    
    def _load_config_dialog(self):
        """Open dialog to load config file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Config", "", "YAML files (*.yaml);;All files (*.*)"
        )
        if filename:
            self.yaml_editor.load_file(filename)
    
    def _reload_config(self):
        """Reload configuration."""
        self._load_config()
        self.tty_display.add_line("CONFIG", "Configuration reloaded", False)
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Midi Fighter 3D Macro Controller",
            "<h2>Midi Fighter 3D Macro Controller</h2>"
            "<p>Version 0.1.0</p>"
            "<p>A stream deck, soundboard, and automation controller.</p>"
        )
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.update_timer.stop()
        
        # Stop audio thread
        if self.audio_thread:
            self.audio_thread.stop()
            self.audio_thread.wait(1000)
        
        # Stop MIDI
        if self.midi_handler:
            self.midi_handler.stop()
        
        # Cleanup soundboard
        if self.soundboard:
            self.soundboard.cleanup()
        
        # Cleanup action runner
        if self.action_runner:
            self.action_runner.cleanup()
        
        # Cleanup TTY
        if self.tty_display:
            self.tty_display.close()
        
        event.accept()


def main():
    """Main entry point for GUI."""
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Midi Fighter 3D")
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
