"""
MIDI input handler for Midi Fighter 3D.
Routes all messages to BankManager for bank switching and note normalization.
"""

import mido
import threading


class MidiHandler:
    def __init__(self, port_name, bank_manager):
        """
        Initialize MIDI handler.

        Args:
            port_name: MIDI port name string
            bank_manager: BankManager instance to route messages to
        """
        self.port_name = port_name
        self.bank_manager = bank_manager
        self._running = False
        self._thread = None

    def start(self):
        """Start listening for MIDI messages in background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._listen)
        self._thread.daemon = True
        self._thread.start()
        print(f"MIDI listener started on {self.port_name}")

    def stop(self):
        """Stop listening for MIDI messages."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _listen(self):
        """Internal loop for MIDI message processing."""
        try:
            with mido.open_input(self.port_name) as port:
                while self._running:
                    for msg in port.iter_pending():
                        self._process_message(msg)
        except Exception as e:
            print(f"MIDI error: {e}")

    def _process_message(self, msg):
        """Process incoming MIDI message and route to BankManager."""
        if msg.type == "note_on":
            # Route to BankManager which handles both bank switches and grid buttons
            self.bank_manager.handle_midi_message(
                msg.type, msg.channel, msg.note, msg.velocity
            )
