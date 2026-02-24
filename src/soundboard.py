"""
Soundboard module for multi-bank audio playback with pre-loaded sounds.
Uses single persistent OutputStream with mixer thread for ALSA compatibility
and minimal latency with overlapping sound support.
"""

import sounddevice as sd
import soundfile as sf
import threading
import numpy as np
from pathlib import Path
import time


class Soundboard:
    # Standard output configuration
    OUTPUT_SAMPLE_RATE = 44100
    OUTPUT_CHANNELS = 2
    BLOCK_SIZE = 2048

    def __init__(self, sounds_config, banks_config):
        """
        Initialize soundboard with pre-loaded sounds and persistent audio stream.

        Args:
            sounds_config: {sound_name: {file: path, volume: float}}
            banks_config: {bank_name: {note: {sound: name, volume: float}}}
        """
        self.sounds = {}  # Pre-loaded audio data: {sound_name: (data, volume)}
        self.banks = {}  # Button mappings: {bank_name: {note: sound_name}}
        self._lock = threading.Lock()

        # Active sounds being played: list of (sound_data, position, volume)
        self._active_sounds = []
        self._mixer_running = False
        self._output_stream = None
        self._mixer_thread = None

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

                    # Convert to stereo if mono
                    if len(data.shape) == 1:
                        data = np.column_stack((data, data))
                    elif data.shape[1] == 1:
                        data = np.column_stack((data[:, 0], data[:, 0]))

                    # Resample to standard output rate if different
                    if samplerate != self.OUTPUT_SAMPLE_RATE:
                        data = self._resample(data, samplerate, self.OUTPUT_SAMPLE_RATE)

                    self.sounds[sound_name] = (data, default_volume)
                    loaded_count += 1
                    print(f"  Loaded: {sound_name}")
                except Exception as e:
                    print(f"Error loading sound '{sound_name}' from {filepath}: {e}")
            else:
                print(f"Warning: Sound file not found: {filepath}")

        print(f"Loaded {loaded_count} sounds into memory")

        # Build button mappings
        for bank_name, buttons in banks_config.items():
            self.banks[bank_name] = {}
            for note, button_def in buttons.items():
                if isinstance(button_def, dict):
                    sound_name = button_def.get("sound")
                else:
                    sound_name = button_def

                if sound_name and sound_name in self.sounds:
                    self.banks[bank_name][int(note)] = sound_name

        # Initialize persistent audio stream
        self._init_audio_stream()

    def _resample(self, data, orig_sr, target_sr):
        """Simple linear resampling using numpy."""
        if orig_sr == target_sr:
            return data

        # Calculate resampling ratio
        ratio = target_sr / orig_sr
        new_length = int(len(data) * ratio)

        # Create interpolation indices
        indices = np.linspace(0, len(data) - 1, new_length)

        # Linear interpolation for each channel
        result = np.zeros((new_length, data.shape[1]), dtype="float32")
        for ch in range(data.shape[1]):
            result[:, ch] = np.interp(indices, np.arange(len(data)), data[:, ch])

        return result

    def _init_audio_stream(self):
        """Initialize persistent OutputStream and start mixer thread."""
        try:
            self._output_stream = sd.OutputStream(
                samplerate=self.OUTPUT_SAMPLE_RATE,
                channels=self.OUTPUT_CHANNELS,
                dtype="float32",
                blocksize=self.BLOCK_SIZE,
                latency="high",
            )

            self._mixer_running = True
            self._mixer_thread = threading.Thread(target=self._mixer_loop)
            self._mixer_thread.daemon = True
            self._mixer_thread.start()

            print("Audio stream initialized")

        except Exception as e:
            print(f"Error initializing audio stream: {e}")
            raise

    def _mixer_loop(self):
        """Background thread: continuously mix and play active sounds."""
        self._output_stream.start()

        while self._mixer_running:
            # Calculate buffer to write
            buffer = np.zeros((self.BLOCK_SIZE, self.OUTPUT_CHANNELS), dtype="float32")

            with self._lock:
                # Mix all active sounds
                sounds_to_remove = []

                for i, (sound_data, position, volume) in enumerate(self._active_sounds):
                    remaining = len(sound_data) - position

                    if remaining <= 0:
                        # Sound finished
                        sounds_to_remove.append(i)
                        continue

                    # Calculate how much to copy
                    to_copy = min(remaining, self.BLOCK_SIZE)

                    # Add to mix buffer with volume
                    end_pos = position + to_copy
                    buffer[:to_copy] += sound_data[position:end_pos] * volume

                    # Update position
                    self._active_sounds[i] = (sound_data, end_pos, volume)

                # Remove finished sounds (in reverse order to maintain indices)
                for idx in reversed(sounds_to_remove):
                    self._active_sounds.pop(idx)

            # Clip to prevent overflow
            buffer = np.clip(buffer, -1.0, 1.0)

            # Write to output stream
            try:
                self._output_stream.write(buffer)
            except Exception as e:
                print(f"Audio stream error: {e}")
                time.sleep(0.01)  # Brief pause on error

    def play(self, bank, note):
        """
        Play sound mapped to bank and normalized note number.
        Sound added immediately to mix for minimal latency.

        Args:
            bank: Bank name ('A', 'B', 'C', or 'D')
            note: Normalized note number (0-15)
        """
        if bank not in self.banks:
            return
        if note not in self.banks[bank]:
            return

        sound_name = self.banks[bank][note]
        sound_data, default_volume = self.sounds[sound_name]

        # Add to active sounds immediately (no thread creation, no stream creation)
        with self._lock:
            # Check if this exact sound is already playing (toggle behavior)
            for i, (data, pos, vol) in enumerate(self._active_sounds):
                if data is sound_data:  # Same sound object
                    # Restart from beginning
                    self._active_sounds[i] = (sound_data, 0, default_volume)
                    return

            # Add new sound at position 0
            self._active_sounds.append((sound_data, 0, default_volume))

    def cleanup(self):
        """Stop mixer thread and close audio stream."""
        self._mixer_running = False

        if self._mixer_thread:
            self._mixer_thread.join(timeout=1.0)

        if self._output_stream:
            self._output_stream.stop()
            self._output_stream.close()

        print("Audio stream cleaned up")
