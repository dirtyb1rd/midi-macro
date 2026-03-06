"""
Main entry point for Midi Fighter 3D Stream Deck with multi-bank and automation support.
Uses modular configuration: config/main.yaml + config/banks/*.yaml
"""

from pathlib import Path
import signal
import sys
from types import FrameType
from typing import Any, Dict, Optional

import yaml

from action_runner import ActionRunner
from bank_manager import BankManager
from midi_handler import MidiHandler
from soundboard import Soundboard


def load_config() -> Dict[str, Any]:
    """Load modular configuration from main.yaml and bank files."""
    config_path: Path = Path(__file__).parent.parent / "config" / "main.yaml"

    with open(config_path) as f:
        main_config: Dict[str, Any] = yaml.safe_load(f)

    # Load individual bank configurations
    all_sounds: Dict[str, Dict[str, Any]] = {}
    all_banks: Dict[str, Dict[str, Any]] = {}

    banks_config: Dict[str, Optional[str]] = main_config.get("banks", {})
    for bank_name, bank_file in banks_config.items():
        if bank_file is None:
            # Bank D is reserved/empty
            all_banks[bank_name] = {}
            continue

        bank_path: Path = Path(__file__).parent.parent / bank_file
        with open(bank_path) as f:
            bank_config: Dict[str, Any] = yaml.safe_load(f)

        # Merge sounds from this bank
        bank_sounds: Dict[str, Dict[str, Any]] = bank_config.get("sounds", {})
        all_sounds.update(bank_sounds)

        # Store bank mappings
        all_banks[bank_name] = bank_config.get("mappings", {})

    return {
        "midi": main_config.get("midi", {}),
        "sounds": all_sounds,
        "banks": all_banks,
    }


# Load configuration
config: Dict[str, Any] = load_config()

# Initialize components
soundboard: Soundboard = Soundboard(
    sounds_config=config.get("sounds", {}), banks_config=config.get("banks", {})
)

action_runner: ActionRunner = ActionRunner(scripts_dir="scripts")

# Track current bank for action execution
current_bank: str = "A"


def on_bank_switch(bank: str) -> None:
    """Handle bank switch event."""
    global current_bank
    current_bank = bank
    print(f"Switched to Bank {bank}")


def on_button_press(bank: str, note: int) -> None:
    """Handle button press - play sound and/or execute action."""
    # Get button configuration
    bank_config: Dict[str, Any] = config.get("banks", {}).get(bank, {})
    button_config: Any = bank_config.get(note, {})

    # Play sound if configured
    if isinstance(button_config, dict):
        sound_name: Optional[str] = button_config.get("sound")
        if sound_name:
            soundboard.play(bank, note)

        # Execute action if configured
        action_config: Optional[Dict[str, Any]] = button_config.get("action")
        if action_config:
            action_runner.execute(action_config)
    elif isinstance(button_config, str):
        # Legacy format - just a sound name
        soundboard.play(bank, note)


# BankManager handles bank switching and routes button presses
bank_manager: BankManager = BankManager(
    bank_callback=on_bank_switch,
    button_callback=on_button_press,
)

midi: MidiHandler = MidiHandler(
    port_name=config["midi"]["port_name"],
    bank_manager=bank_manager,
)


# Graceful shutdown
def signal_handler(sig: int, frame: Optional[FrameType]) -> None:
    """Handle shutdown signals gracefully."""
    print("\nShutting down...")
    action_runner.cleanup()
    soundboard.cleanup()
    midi.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main loop
if __name__ == "__main__":
    banks_dict: Dict[str, Dict[str, Any]] = config.get("banks", {})
    total_buttons: int = sum(len(bank) for bank in banks_dict.values())

    # Count buttons with actions
    action_count: int = 0
    for bank_name, bank_config in banks_dict.items():
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
