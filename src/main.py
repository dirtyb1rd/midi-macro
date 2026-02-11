"""
Main entry point for Midi Fighter 3D Stream Deck with multi-bank and automation support.
"""

import yaml
import signal
import sys
from pathlib import Path

from midi_handler import MidiHandler
from soundboard import Soundboard
from bank_manager import BankManager
from action_runner import ActionRunner

# Load configuration
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

# Initialize components
soundboard = Soundboard(
    sounds_config=config.get("sounds", {}), banks_config=config.get("banks", {})
)

action_runner = ActionRunner(scripts_dir="scripts")

# Track current bank for action execution
current_bank = "A"


def on_bank_switch(bank):
    """Handle bank switch event."""
    global current_bank
    current_bank = bank
    print(f"Switched to Bank {bank}")


def on_button_press(bank, note):
    """Handle button press - play sound and/or execute action."""
    # Get button configuration
    bank_config = config.get("banks", {}).get(bank, {})
    button_config = bank_config.get(note, {})

    # Play sound if configured
    if isinstance(button_config, dict):
        sound_name = button_config.get("sound")
        if sound_name:
            soundboard.play(bank, note)

        # Execute action if configured
        action_config = button_config.get("action")
        if action_config:
            action_runner.execute(action_config)
    elif isinstance(button_config, str):
        # Legacy format - just a sound name
        soundboard.play(bank, note)


# BankManager handles bank switching and routes button presses
bank_manager = BankManager(
    bank_callback=on_bank_switch,
    button_callback=on_button_press,
)

midi = MidiHandler(
    port_name=config["midi"]["port_name"],
    bank_manager=bank_manager,
)


# Graceful shutdown
def signal_handler(sig, frame):
    print("\nShutting down...")
    action_runner.cleanup()
    midi.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main loop
if __name__ == "__main__":
    total_buttons = sum(len(bank) for bank in config["banks"].values())

    # Count buttons with actions
    action_count = 0
    for bank_name, bank_config in config.get("banks", {}).items():
        for note, button_config in bank_config.items():
            if isinstance(button_config, dict) and button_config.get("action"):
                action_count += 1

    print("=" * 50)
    print("Midi Fighter 3D Stream Deck - Multi-Bank + Automation")
    print("=" * 50)
    print(f"Banks: A, B, C, D ({total_buttons} total buttons)")
    print(f"Actions configured: {action_count}")
    print("Press Ctrl+C to exit\n")

    midi.start()

    # Keep main thread alive
    while True:
        signal.pause()
