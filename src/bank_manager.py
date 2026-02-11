"""
Bank manager for multi-bank support on Midi Fighter 3D.
Handles bank switching (Channel 3) and note normalization.
"""

import threading


class BankManager:
    """
    Manages 4 banks (A/B/C/D) with note normalization.

    Bank switches: Channel 3, notes 0-3
    Grid buttons: Channel 2, notes per bank:
      Bank A: 36-51, Bank B: 52-67, Bank C: 68-83, Bank D: 84-99
    """

    BANK_NOTES = {
        "A": (0, 36, 51),  # (bank_note, min_grid, max_grid)
        "B": (1, 52, 67),
        "C": (2, 68, 83),
        "D": (3, 84, 99),
    }

    def __init__(self, bank_callback=None, button_callback=None):
        """
        Initialize bank manager.

        Args:
            bank_callback: Called when bank changes, receives (bank_name)
            button_callback: Called when button pressed, receives (bank, normalized_note)
        """
        self.current_bank = "A"
        self.bank_callback = bank_callback
        self.button_callback = button_callback
        self._lock = threading.Lock()

    def handle_midi_message(self, msg_type, channel, note, velocity):
        """
        Process incoming MIDI message.
        Returns True if message was handled, False otherwise.
        """
        if velocity == 0:
            return False

        # Bank switching on Channel 4 (mido uses 0-indexed, so channel 3)
        if msg_type == "note_on" and channel == 3:
            for bank_name, (bank_note, _, _) in self.BANK_NOTES.items():
                if note == bank_note:
                    with self._lock:
                        old_bank = self.current_bank
                        self.current_bank = bank_name
                    if old_bank != bank_name and self.bank_callback:
                        self.bank_callback(bank_name)
                    return True

        # Grid buttons on Channel 3 (mido uses 0-indexed, so channel 2)
        if msg_type == "note_on" and channel == 2:
            # Find which bank this note belongs to
            detected_bank = None
            for bank_name, (_, min_note, max_note) in self.BANK_NOTES.items():
                if min_note <= note <= max_note:
                    detected_bank = bank_name
                    break

            if detected_bank:
                # Switch to the detected bank if different
                with self._lock:
                    old_bank = self.current_bank
                    self.current_bank = detected_bank

                if old_bank != detected_bank and self.bank_callback:
                    self.bank_callback(detected_bank)

                # Normalize and play
                _, min_note, _ = self.BANK_NOTES[detected_bank]
                normalized = note - min_note  # 0-15
                if self.button_callback:
                    self.button_callback(detected_bank, normalized)
                return True

        return False

    def get_current_bank(self):
        """Get current active bank name."""
        with self._lock:
            return self.current_bank
