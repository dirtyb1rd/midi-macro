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

## Audio Architecture Evolution

### The ALSA Problem

The journey to reliable audio playback involved testing three different architectures, each with trade-offs between latency, complexity, and ALSA compatibility.

#### Architecture 1: Per-Button Thread + Per-Stream Creation ❌

**Implementation:** Each button press spawned a new thread, which created a new `sounddevice.OutputStream`, played the sound, then cleaned up.

```
Button Press → New Thread → New OutputStream → Play → Close Stream
```

**Issues:**
- **ALSA Resource Conflicts**: Direct ALSA access doesn't support concurrent streams. Each new stream attempted to open the audio device, causing `mmap` failures and "Invalid stream pointer" errors
- **Race Conditions**: Multiple threads opening/closing streams simultaneously corrupted ALSA's internal state
- **High Latency**: Creating a new stream for each button press added 10-50ms overhead
- **Device Exhaustion**: Rapid button presses eventually exhausted available PCM devices

**Error Examples:**
```
PaErrorCode -9999: Unanticipated host error [alsa_snd_pcm_mmap_begin]
PaErrorCode -9988: Invalid stream pointer
PaErrorCode -9993: Illegal combination of I/O devices
```

#### Architecture 2: Retry Logic + Explicit Device Parameters ⚠️

**Implementation:** Added explicit ALSA parameters (blocksize=1024, latency='high') and retry logic with exponential backoff.

**Improvements:**
- Explicit device selection (`device=sd.default.device[1]`)
- Configured ALSA-friendly buffer settings
- 3-attempt retry with exponential backoff (50ms → 100ms → 200ms)

**Remaining Issues:**
- **Still Failed Under Load**: While individual sounds played, rapid button mashing (drum rolls) still caused stream corruption
- **Retry Delays**: Added audible latency when ALSA was busy
- **Fundamental Design Flaw**: Creating multiple streams for concurrent playback is incompatible with ALSA's single-stream model (without dmix plugin)

#### Architecture 3: Single Persistent Stream + Mixer Thread ✅ (Current)

**Implementation:** One persistent `OutputStream` created at startup, with a background mixer thread continuously writing mixed audio.

```
Startup: Create Persistent OutputStream → Start Mixer Thread
Button Press: Add sound to active list (immediate, ~0.1ms)
Mixer Thread: Continuously mix active sounds → Write to stream
```

**Key Design Decisions:**
- **Pre-created Stream**: Audio device opened once and kept open throughout application lifetime
- **Background Mixer Thread**: Continuously generates audio blocks (2048 samples) by mixing all active sounds
- **Resampling**: All sounds normalized to 44.1kHz at load time for consistent mixing
- **Toggle Behavior**: Pressing the same button twice restarts the sound (resets position to 0)
- **Lock-free Design**: Uses threading.Lock only for the active sounds list, not for stream access

**Benefits:**
- ✅ **Zero ALSA Conflicts**: Only one stream ever exists
- ✅ **Minimal Latency**: ~2-10ms button-to-sound (limited by buffer size)
- ✅ **Overlapping Sounds**: Natural mixing of multiple simultaneous sounds
- ✅ **No Stream Creation Overhead**: Immediate playback, no allocation
- ✅ **Predictable Performance**: Constant latency regardless of button press rate

**Trade-offs:**
- **Memory Usage**: All sounds resampled to 44.1kHz stereo at load time (2x memory for mono files)
- **CPU Usage**: Mixer thread runs continuously (~5% CPU on modern hardware)
- **Complexity**: More code than simple per-stream approach

### Configuration Architecture

**Monolithic Config → Modular Config**

Evolved from a single `config.yaml` to a modular structure:

```
config/
├── main.yaml          # MIDI settings + bank file references
└── banks/
    ├── bass.yaml      # 16 bass sounds (sorted by duration)
    ├── drums.yaml     # 16 drum sounds (one-shots)
    └── synth.yaml     # 16 synth sounds
```

**Rationale:**
- Bank configs can be edited independently
- Duration-sorted sounds (shortest → longest per bank)
- Easy to swap entire banks
- Bank D reserved for automation (future)

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

The system uses a **modular configuration** structure:

```
config/
├── main.yaml          # MIDI settings + bank file references
└── banks/
    ├── bass.yaml      # Bank A: Bass sounds (sorted by duration)
    ├── drums.yaml     # Bank B: Drum sounds (one-shots)
    └── synth.yaml     # Bank C: Synth sounds
```

### Main Config (`config/main.yaml`)

```yaml
midi:
  port_name: "Midi Fighter 3D:Midi Fighter 3D MIDI 1 20:0"
  grid_channel: 1
  bank_channel: 2

# Bank configuration files
banks:
  A: config/banks/bass.yaml
  B: config/banks/drums.yaml
  C: config/banks/synth.yaml
  D: null  # Reserved for automation
```

### Bank Config (`config/banks/drums.yaml`)

Each bank file contains sounds and button mappings:

```yaml
# Define sounds for this bank
sounds:
  drum_kick:
    file: sounds/kick.wav
    volume: 1.0
  drum_snare:
    file: sounds/snare.wav
    volume: 0.9

# Map buttons 0-15 to sounds
mappings:
  0:
    sound: drum_kick
    volume: 1.0  # Optional: override default volume
  1:
    sound: drum_snare
```

### Duration-Sorted Banks

Sounds in each bank are sorted by duration (shortest → longest):
- **Bank A (Bass)**: 10.67s → 21.33s
- **Bank B (Drums)**: 0.42s → 2.82s (all one-shots)
- **Bank C (Synth)**: 14.77s → 21.33s

This makes short sounds easily accessible on buttons 0-3, longer sounds on 12-15.

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
