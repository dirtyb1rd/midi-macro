"""
Soundboard module for multi-bank audio playback with pre-loaded sounds.
Supports volume control per sound and per-button override.
"""

import sounddevice as sd
import soundfile as sf
import threading
import numpy as np
from pathlib import Path


class Soundboard:
    def __init__(self, sounds_config, banks_config):
        """
        Initialize soundboard with pre-loaded sounds and multi-bank configuration.

        Args:
            sounds_config: {sound_name: {file: path, volume: float}}
            banks_config: {bank_name: {note: {sound: name, volume: float}}}
        """
        self.sounds = {}  # Pre-loaded audio data: {sound_name: (data, samplerate, default_volume)}
        self.banks = {}  # Button mappings: {bank_name: {note: (sound_name, volume)}}
        self._lock = threading.Lock()
        self._active_streams = {}

        # Pre-load all unique sound files into memory
        print("Loading sounds...")
        loaded_count = 0
        for sound_name, sound_def in sounds_config.items():
            filepath = sound_def.get("file")
            default_volume = sound_def.get("volume", 1.0)

            if not filepath:
                print(f"Warning: No file specified for sound '{sound_name}'")
                continue

            path = Path(filepath)
            if path.exists():
                try:
                    data, samplerate = sf.read(str(path), dtype="float32")
                    # Ensure data is 2D (frames, channels)
                    if len(data.shape) == 1:
                        data = data.reshape(-1, 1)
                    self.sounds[sound_name] = (data, samplerate, default_volume)
                    loaded_count += 1
                    print(f"  Loaded: {sound_name} ({filepath})")
                except Exception as e:
                    print(f"Error loading sound '{sound_name}' from {filepath}: {e}")
            else:
                print(f"Warning: Sound file not found: {filepath}")

        print(f"Loaded {loaded_count} sounds into memory")

        # Build button mappings with volume overrides
        for bank_name, buttons in banks_config.items():
            self.banks[bank_name] = {}
            for note, button_def in buttons.items():
                if isinstance(button_def, dict):
                    sound_name = button_def.get("sound")
                    volume = button_def.get("volume")  # Can be None to use default
                else:
                    # Legacy format support (just a string)
                    sound_name = button_def
                    volume = None

                if sound_name and sound_name in self.sounds:
                    self.banks[bank_name][int(note)] = (sound_name, volume)

    def play(self, bank, note):
        """
        Play sound mapped to bank and normalized note number.
        Sound data is pre-loaded in memory for instant playback.

        Args:
            bank: Bank name ('A', 'B', 'C', or 'D')
            note: Normalized note number (0-15)
        """
        if bank not in self.banks:
            return
        if note not in self.banks[bank]:
            return

        sound_name, button_volume = self.banks[bank][note]
        stream_key = (bank, note)

        # Stop existing playback for this button (toggle behavior)
        with self._lock:
            if stream_key in self._active_streams:
                try:
                    self._active_streams[stream_key].stop()
                except:
                    pass
                del self._active_streams[stream_key]

        # Start new playback in background thread
        thread = threading.Thread(
            target=self._play_sound, args=(bank, note, sound_name, button_volume)
        )
        thread.daemon = True
        thread.start()

    def _play_sound(self, bank, note, sound_name, button_volume):
        """Internal method to play pre-loaded sound data."""
        try:
            data, samplerate, default_volume = self.sounds[sound_name]

            # Use button volume if specified, otherwise use sound's default volume
            volume = button_volume if button_volume is not None else default_volume

            # Apply volume scaling
            if volume != 1.0:
                data = data * volume

            # Create output stream
            channels = data.shape[1]
            stream = sd.OutputStream(
                samplerate=samplerate,
                channels=channels,
                dtype="float32",
            )

            stream_key = (bank, note)
            with self._lock:
                self._active_streams[stream_key] = stream

            with stream:
                stream.write(data)

            # Clean up when done
            with self._lock:
                if stream_key in self._active_streams:
                    del self._active_streams[stream_key]

        except Exception as e:
            print(
                f"Error playing sound '{sound_name}' for bank {bank} note {note}: {e}"
            )
