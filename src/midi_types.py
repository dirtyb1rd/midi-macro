"""
Type definitions for midi-macro configuration and data structures.
"""

from typing import TypedDict, NotRequired, Protocol, Callable
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import numpy.typing as npt


# Configuration Types (from YAML)

class SoundConfig(TypedDict):
    """Configuration for a single sound file."""
    file: str
    volume: NotRequired[float]


class ActionConfig(TypedDict):
    """Configuration for an automation action."""
    type: str
    file: NotRequired[str]
    args: NotRequired[List[str]]
    blocking: NotRequired[bool]
    url: NotRequired[str]
    method: NotRequired[str]
    headers: NotRequired[Dict[str, str]]
    body: NotRequired[Dict[str, Any]]
    shortcut: NotRequired[str]


class ButtonMapping(TypedDict):
    """Configuration for a single button mapping."""
    sound: NotRequired[str]
    volume: NotRequired[float]
    action: NotRequired[ActionConfig]


class BankConfig(TypedDict):
    """Configuration for a single bank."""
    sounds: Dict[str, SoundConfig]
    mappings: Dict[str, ButtonMapping]


class MidiConfig(TypedDict):
    """MIDI device configuration."""
    port_name: str
    grid_channel: int
    bank_channel: int


class MainConfig(TypedDict):
    """Root configuration structure."""
    midi: MidiConfig
    banks: Dict[str, Optional[str]]


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


# Callback Protocols

class BankCallback(Protocol):
    """Protocol for bank switch callbacks."""
    def __call__(self, bank: str) -> None: ...


class ButtonCallback(Protocol):
    """Protocol for button press callbacks."""
    def __call__(self, bank: str, note: int) -> None: ...


# Type alias for optional callbacks
OptionalBankCallback = Optional[BankCallback]
OptionalButtonCallback = Optional[ButtonCallback]

# MIDI message types
MidiMessageType = str

# MIDI channel (0-15, mido uses 0-indexed internally)
MidiChannel = int

# MIDI note number (0-127)
MidiNote = int

# MIDI velocity (0-127)
MidiVelocity = int

# Bank note mapping: (bank_switch_note, min_grid_note, max_grid_note)
BankNoteRange = Tuple[int, int, int]
