# Midi Fighter 3D Macro Controller

Turned my midi controller into a stream deck, soundboard, and automation controller. Mapping 64 buttons across 4 banks to play sounds with volume control, run scripts, trigger webhooks, and inject keyboard shortcuts.


- Key Features:
  - 4 Banks: A, B, C, D - 64 total buttons
  - Auto-switching: Press any grid button to automatically switch to its bank
  - Pre-loaded: All sounds loaded into memory at startup for instant playback
  - Volume Control: Set per-sound default and per-button override
  - Toggle Behavior: Press button again to stop currently playing sound

---

## What Exists

- Discovery & Data Collection
- Manual testing script maps actual MIDI events
- Documented note numbers and channel assignments:
  - Grid buttons: Notes 36-99 on Channel 3 (mido channel 2)
  - Bank switches: Notes 0-3 on Channel 4 (mido channel 3)
  - Bank A: 36-51, B: 52-67, C: 68-83, D: 84-99

- Core Infrastructure
- mido/rtmidi event loop with callback-based input
- Bank state machine with 4 modes (A/B/C/D)
- Auto-bank detection (press any grid button to switch)
- Configuration system (YAML mappings with volume control)

- Soundboard Engine
- Audio playback with sounddevice
- Pre-loaded sounds for instant playback, no first-press delay
- Multi-bank soundboard with different sounds per bank
- Volume control per sound and per-button override
- Stop/restart overlapping sounds (toggle behavior)

---

## Todo List

- Automation Engine
  - Bash/Python script execution with args
  - HTTP webhooks: POST/GET with httpx
  - Keyboard shortcuts via pynput

- Audio Enhancement
  - Multi-device routing: Speakers + mic monitor simultaneously
  - Audio loop support

- LED & Polish
  - Static LED colors per bank
  - CLI interface for testing/config
  - LED flash on press animations
  - Full RGB control per button

- Code Quality & Tooling
  - Add mypy for static type checking
  - Add typer for CLI interface
  - Add ruff for linting and formatting
  - Add type hints to all modules
  - Create development documentation

Roadmap
- Motion: CC passthrough to other apps
- Motion: Gesture triggers (tilt actions)
- Security: Script sandboxing/allowlist
- Security: Execution timeouts
- Config: Include directive for split files
- Deployment: systemd service support
- Deployment: GUI tray application

---

## Quick Start

```bash
# Install system dependencies (Debian/Ubuntu)
sudo apt-get install libasound2-dev libjack-jackd2-dev libportaudio2 python3-dev python3-pkgconfig

# Install dependencies
pip install mido python-rtmidi sounddevice soundfile httpx pynput pyyaml

# Run the controller
python src/main.py
```

## Configuration

Edit `config.yaml` to map MIDI buttons to sounds:

```yaml
# Define reusable sounds with default settings
sounds:
  camera:
    file: sounds/camera.mp3
    volume: 1.0
  alert:
    file: sounds/alert.mp3
    volume: 0.8

# Map each bank's 16 buttons (0-15) to sounds
banks:
  A:  # Grid notes 36-51
    0:
      sound: camera
      volume: 1.0  # Optional: override default volume
    1:
      sound: camera  # Uses default volume from sounds section
    2:
      sound: alert
  
  B:  # Grid notes 52-67
    0:
      sound: alert
    
  C:  # Grid notes 68-83
    0:
      sound: camera
      
  D:  # Grid notes 84-99
    0:
      sound: camera
```

---

## Asteroids + 3D Sensors

The Midi Fighter 3D includes 3-axis motion sensors that output continuous controller (CC) messages. This enables controlling games and applications with physical gestures.

Planned Use Cases:
- Tilt-to-Steer: X/Y accelerometer mapped to ship rotation
- Thrust Gesture: Forward tilt for thrust, backward for reverse
- Fire Button: Velocity-sensitive grid buttons for weapons
- Bank Switch: 4 weapon/powerup modes per bank

MIDI Mapping for Game Control:
- CC 16: X-axis (tilt left/right) → ship rotation
- CC 17: Y-axis (tilt forward/back) → thrust/reverse
- CC 18: Z-axis (twist/tilt) → hyperspace/special
- Notes 0-15: Fire, shields, special weapons per bank
