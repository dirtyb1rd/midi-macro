"""
Type definitions for midi-macro configuration and data structures.

This module contains TypedDict definitions for YAML configurations,
callback protocols, and shared type aliases used across the codebase.
"""

from typing import TypedDict, NotRequired, Protocol, Callable
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import numpy.typing as npt


# =============================================================================
# Configuration Types (from YAML)
# =============================================================================

class SoundConfig(TypedDict):
    """Configuration for a single sound file.
    
    Example from YAML:
        drum_kick:
          file: sounds/kick.wav
          volume: 1.0
    """
    file: str
    volume: NotRequired[float]


class ActionConfig(TypedDict):
    """Configuration for an automation action.
    
    Supports three action types:
    - script: Execute bash/Python scripts
    - webhook: Send HTTP requests
    - keyboard: Inject keyboard shortcuts
    
    Example from YAML:
        action:
          type: script
          file: hello.sh
          args: ["World"]
          blocking: false
    """
    type: str
    # Script action fields
    file: NotRequired[str]
    args: NotRequired[List[str]]
    blocking: NotRequired[bool]
    # Webhook action fields
    url: NotRequired[str]
    method: NotRequired[str]
    headers: NotRequired[Dict[str, str]]
    body: NotRequired[Dict[str, Any]]
    # Keyboard action fields
    shortcut: NotRequired[str]


class ButtonMapping(TypedDict):
    """Configuration for a single button mapping.
    
    Example from YAML:
        0:
          sound: drum_kick
          volume: 1.0
          action:
            type: script
            file: hello.sh
    """
    sound: NotRequired[str]
    volume: NotRequired[float]
    action: NotRequired[ActionConfig]


class BankConfig(TypedDict):
    """Configuration for a single bank (sounds + button mappings).
    
    Example from YAML:
        sounds:
          drum_kick:
            file: sounds/kick.wav
        mappings:
          0:
            sound: drum_kick
    """
    sounds: Dict[str, SoundConfig]
    mappings: Dict[str, ButtonMapping]


class MidiConfig(TypedDict):
    """MIDI device configuration from main.yaml."""
    port_name: str
    grid_channel: int
    bank_channel: int


class MainConfig(TypedDict):
    """Root configuration structure from main.yaml."""
    midi: MidiConfig
    banks: Dict[str, Optional[str]]  # bank_name -> file path or None


# =============================================================================
# Runtime Data Types
# =============================================================================

# Audio data: (numpy_array, volume_multiplier)
AudioData = Tuple[npt.NDArray[np.float32], float]

# Active sound entry: (audio_data, position_in_samples, volume)
ActiveSound = Tuple[npt.NDArray[np.float32], int, float]

# Sound dictionary: sound_name -> (audio_data, default_volume)
SoundsDict = Dict[str, AudioData]

# Bank mappings: bank_name -> {note_number -> sound_name}
BankMappings = Dict[str, Dict[int, str]]

# Configuration dictionary returned by load_config()
ConfigDict = Dict[str, Any]


# =============================================================================
# Callback Protocols
# =============================================================================

class BankCallback(Protocol):
    """Protocol for bank switch callbacks.
    
    Called when the active bank changes (A, B, C, or D).
    """
    def __call__(self, bank: str) -> None: ...


class ButtonCallback(Protocol):
    """Protocol for button press callbacks.
    
    Called when a grid button is pressed. Note is normalized to 0-15.
    """
    def __call__(self, bank: str, note: int) -> None: ...


# Type alias for optional callbacks
OptionalBankCallback = Optional[BankCallback]
OptionalButtonCallback = Optional[ButtonCallback]


# =============================================================================
# MIDI Types
# =============================================================================

# MIDI message types
MidiMessageType = str  # "note_on", "note_off", "control_change", etc.

# MIDI channel (0-15, though mido uses 0-indexed internally)
MidiChannel = int

# MIDI note number (0-127)
MidiNote = int

# MIDI velocity (0-127)
MidiVelocity = int

# Bank note mapping: (bank_switch_note, min_grid_note, max_grid_note)
BankNoteRange = Tuple[int, int, int]
