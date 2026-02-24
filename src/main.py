"""
Main entry point for Midi Fighter 3D Stream Deck with multi-bank and automation support.
Uses modular configuration: config/main.yaml + config/banks/*.yaml
"""

import yaml
import signal
import sys
from pathlib import Path

from midi_handler import MidiHandler
from soundboard import Soundboard
from bank_manager import BankManager
from action_runner import ActionRunner


def load_config():
    """Load modular configuration from main.yaml and bank files."""
    config_path = Path(__file__).parent.parent / "config" / "main.yaml"

    with open(config_path) as f:
        main_config = yaml.safe_load(f)

    # Load individual bank configurations
    all_sounds = {}
    all_banks = {}

    for bank_name, bank_file in main_config.get("banks", {}).items():
        if bank_file is None:
            # Bank D is reserved/empty
            all_banks[bank_name] = {}
            continue

        bank_path = Path(__file__).parent.parent / bank_file
        with open(bank_path) as f:
            bank_config = yaml.safe_load(f)

        # Merge sounds from this bank
        bank_sounds = bank_config.get("sounds", {})
        all_sounds.update(bank_sounds)

        # Store bank mappings
        all_banks[bank_name] = bank_config.get("mappings", {})

    return {
        "midi": main_config.get("midi", {}),
        "sounds": all_sounds,
        "banks": all_banks,
    }


# Load configuration
config = load_config()

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
    soundboard.cleanup()
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
    print(f"Banks: A (Bass), B (Drums), C (Synth), D (Reserved)")
    print(f"Total buttons: {total_buttons}")
    print(f"Actions configured: {action_count}")
    print("Press Ctrl+C to exit\n")

    midi.start()

    # Keep main thread alive
    while True:
        signal.pause()
