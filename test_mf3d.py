#!/usr/bin/env python3
"""
Midi Fighter 3D Discovery Script
Press buttons on your controller to see their MIDI mappings.
"""

import mido
import sys
from datetime import datetime

# MF3D port - update this if your port name differs
MF3D_PORT = "Midi Fighter 3D:Midi Fighter 3D MIDI 1 20:0"


def test_input():
    """Monitor and display all incoming MIDI messages."""
    print("=" * 60)
    print("MIDI INPUT TEST")
    print("=" * 60)
    print(f"\nListening on: {MF3D_PORT}")
    print("Press buttons on your Midi Fighter 3D...")
    print("Press Ctrl+C to stop\n")

    try:
        with mido.open_input(MF3D_PORT) as port:
            for msg in port:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                if msg.type == "note_on":
                    print(
                        f"[{timestamp}] NOTE ON  - note={msg.note:3d}, velocity={msg.velocity:3d}, channel={msg.channel}"
                    )
                elif msg.type == "note_off":
                    print(
                        f"[{timestamp}] NOTE OFF - note={msg.note:3d}, velocity={msg.velocity:3d}, channel={msg.channel}"
                    )
                elif msg.type == "control_change":
                    print(
                        f"[{timestamp}] CC       - control={msg.control:3d}, value={msg.value:3d}, channel={msg.channel}"
                    )
                else:
                    print(f"[{timestamp}] {msg}")

    except KeyboardInterrupt:
        print("\n\nTest complete!")
    except Exception as e:
        print(f"\nError: {e}")


def test_led_output():
    """Test LED control by sending Note On messages."""
    print("=" * 60)
    print("LED OUTPUT TEST")
    print("=" * 60)
    print(f"\nOpening output port: {MF3D_PORT}")

    try:
        with mido.open_output(MF3D_PORT) as port:
            print("\nSending test LED commands...")
            print("Note: You should see button colors change on your MF3D")

            # Test notes 36-51 (typical grid range)
            print("\nTesting grid buttons (notes 36-51)...")
            for note in range(36, 52):
                msg = mido.Message("note_on", note=note, velocity=127, channel=1)
                port.send(msg)
                print(f"  Sent note_on note={note}, velocity=127")

            print("\nWaiting 2 seconds...")
            import time

            time.sleep(2)

            # Turn all off
            print("\nTurning all LEDs off...")
            for note in range(36, 52):
                msg = mido.Message("note_on", note=note, velocity=0, channel=1)
                port.send(msg)

            print("LED test complete!")

    except Exception as e:
        print(f"Error: {e}")


def main():
    print("\n" + "=" * 60)
    print("Midi Fighter 3D Discovery Tool")
    print("=" * 60)
    print("\n1. Test input (button mapping)")
    print("2. Test output (LED control)")
    print("3. Test both")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        test_input()
    elif choice == "2":
        test_led_output()
    elif choice == "3":
        test_input()
        print("\n" + "-" * 60 + "\n")
        test_led_output()
    else:
        print("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    main()
