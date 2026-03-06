# Midi Fighter 3D Macro Controller

Turn a Midi Fighter 3D controller into a stream deck, soundboard, and automation controller. Maps 64 buttons across 4 banks to play sounds, run scripts, trigger webhooks, and inject keyboard shortcuts.

## Features

- 4 Banks: A, B, C, D - 64 total buttons
- Auto-switching: Press any grid button to automatically switch to its bank
- Pre-loaded: All sounds loaded into memory at startup for instant playback
- Volume Control: Set per-sound default and per-button override
- Toggle Behavior: Press button again to stop currently playing sound
- Automation: Run bash scripts, send webhooks, inject keyboard shortcuts
- GUI Interface: PyQt6-based interface with real-time feedback

## GUI Interface

A PyQt6-based GUI with the following features:

- 4x4 Button Grid: Visual representation of the physical controller
- Bank Display: Large indicator showing current bank (A/B/C/D) with color coding
- Audio Visualizer: Real-time waveform display using PyQtGraph
- Script Output Panel: Real-time TTY showing script execution output
- Config Editor: Built-in YAML editor with syntax validation and revert capability
- Button Feedback: Buttons flash when pressed on the controller, blink while sounds play
- Bank-Specific Display: Only shows buttons for the currently selected bank

### Running the GUI

```bash
nix develop
python src/gui/main_window.py
```

The GUI integrates with the backend:
- MIDI input from controller triggers GUI button flashing
- Sound playback causes button blinking while active
- Script execution shows real-time output in TTY panel
- Bank switching updates button labels and colors
- Audio visualizer displays real-time waveform

## Quick Start

### NixOS / Nix Users (Recommended)

This project includes a `flake.nix` for reproducible builds. Use `nix develop` not `nix-shell`.

```bash
# Enter the development environment
nix develop

# Or with direnv (auto-loads when you cd into directory)
direnv allow

# Run the CLI version
python src/main.py

# Run the GUI version
python src/gui/main_window.py
```

Why not `nix-shell`?
- `nix-shell` with `shell.nix` has issues where build tools aren't visible in uv's isolated build environment
- The `flake.nix` properly manages Python packages through nixpkgs, avoiding compilation issues with `evdev`, `python-rtmidi`, and other C-extension packages
- All dependencies are pre-built and cached from nixpkgs

### Other Systems

```bash
# Install system dependencies (Debian/Ubuntu)
sudo apt-get install libasound2-dev libjack-jackd2-dev libportaudio2 python3-dev python3-pkgconfig

# Install dependencies
pip install mido python-rtmidi sounddevice soundfile httpx pynput pyyaml pyqt6 pyqtgraph

# Run the controller
python src/main.py

# Or run the GUI
python src/gui/main_window.py
```

## Configuration

The system uses a modular configuration structure:

```
config/
├── main.yaml          # MIDI settings + bank file references
└── banks/
    ├── bass.yaml      # Bank A: Bass sounds
    ├── drums.yaml     # Bank B: Drum sounds  
    ├── synth.yaml     # Bank C: Synth sounds
    └── automation.yaml # Bank D: Scripts and shortcuts
```

### Main Config (config/main.yaml)

```yaml
midi:
  port_name: "Midi Fighter 3D:Midi Fighter 3D MIDI 1 20:0"
  grid_channel: 1
  bank_channel: 2

banks:
  A: config/banks/bass.yaml
  B: config/banks/drums.yaml
  C: config/banks/synth.yaml
  D: config/banks/automation.yaml
```

### Bank Config (config/banks/drums.yaml)

```yaml
sounds:
  drum_kick:
    file: sounds/kick.wav
    volume: 1.0

mappings:
  0:
    sound: drum_kick
    volume: 1.0
  1:
    action:
      type: script
      file: get_ip.sh
      blocking: true
```

### Automation Scripts (Bank D)

Bank D is configured for automation with no sounds:

```yaml
sounds: {}

mappings:
  0:
    action:
      type: script
      file: get_ip.sh
  1:
    action:
      type: script
      file: get_weather.sh
      args: ["Portland"]
```

Included Scripts:
- `get_ip.sh` - Display public IP address
- `get_weather.sh` - Show current weather
- `get_space_fact.sh` - NASA astronomy fact
- `get_joke.sh` - Random joke
- `system_info.sh` - CPU/RAM/disk usage
- `screenshot.sh` - Take timestamped screenshot

## Audio Architecture

### Current Implementation: Single Persistent Stream + Mixer Thread

One persistent OutputStream created at startup, with a background mixer thread continuously writing mixed audio.

```
Startup: Create Persistent OutputStream → Start Mixer Thread
Button Press: Add sound to active list (immediate, ~0.1ms)
Mixer Thread: Continuously mix active sounds → Write to stream
```

Key Design Decisions:
- Pre-created Stream: Audio device opened once and kept open throughout application lifetime
- Background Mixer Thread: Continuously generates audio blocks (2048 samples) by mixing all active sounds
- Resampling: All sounds normalized to 44.1kHz stereo at load time for consistent mixing
- Toggle Behavior: Pressing the same button twice restarts the sound

Benefits:
- Zero ALSA Conflicts: Only one stream ever exists
- Minimal Latency: ~2-10ms button-to-sound
- Overlapping Sounds: Natural mixing of multiple simultaneous sounds
- No Stream Creation Overhead: Immediate playback

## Technical Notes

### MIDI Mapping

- Grid buttons: Notes 36-99 on Channel 3 (mido channel 2)
- Bank switches: Notes 0-3 on Channel 4 (mido channel 3)
- Bank A: 36-51, B: 52-67, C: 68-83, D: 84-99

### Type Safety

All modules use comprehensive type hints with mypy strict mode:
- SoundConfig, ActionConfig, ButtonMapping - TypedDict definitions
- BankCallback, ButtonCallback - Protocol types
- npt.NDArray[np.float32] for audio data

### GUI Development Notes

Visualizer: Implemented using PyQtGraph for high-performance real-time plotting with proper audio/display synchronization.

## File Structure

```
/home/bp/git/midi-macro/
├── src/
│   ├── main.py              # CLI entry point
│   ├── main_gui.py          # GUI entry point
│   ├── bank_manager.py      # Bank state machine
│   ├── midi_handler.py      # MIDI input
│   ├── soundboard.py        # Audio engine
│   ├── action_runner.py     # Scripts/webhooks/keyboard
│   ├── midi_types.py        # Type definitions
│   └── gui/                 # GUI package
│       ├── main_window.py   # Main GUI window
│       ├── midi_button.py   # Custom button widget
│       ├── midi_button_enhanced.py  # Animated button widget
│       ├── visualizer_pyqtgraph.py  # Audio visualizer
│       ├── tty_display.py   # Script output panel
│       ├── yaml_editor.py   # Config editor
│       ├── worker.py        # QThreadPool workers
│       └── styles.py        # Theme definitions
├── config/
│   ├── main.yaml
│   └── banks/
├── scripts/                 # Automation scripts
├── sounds/                  # Audio files
├── flake.nix               # Nix development environment
└── AGENTS.md              # Development guidelines
```

## Future Roadmap

- Audio: Multi-device routing, audio looping
- LED Control: RGB per button, animations
- Motion Sensors: CC passthrough, gesture triggers
- Security: Script sandboxing, execution timeouts
- Deployment: systemd service, AppImage release

## Credits

Built with:
- Python 3.13+
- PyQt6 for GUI
- mido/python-rtmidi for MIDI
- sounddevice/soundfile for audio
- PyQtGraph for visualization
- Nix for reproducible builds
