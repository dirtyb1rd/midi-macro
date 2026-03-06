"""
Action runner for automation engine.
Handles script execution, HTTP webhooks, and keyboard shortcuts.
"""

from pathlib import Path
import subprocess
import threading
from typing import Dict, List, Optional

from midi_types import ActionConfig


class ActionRunner:
    """
    Executes actions triggered by MIDI button presses.
    Supports scripts, webhooks, and keyboard shortcuts.
    """

    def __init__(self, scripts_dir: str = "scripts") -> None:
        """
        Initialize action runner.

        Args:
            scripts_dir: Directory containing script files
        """
        self.scripts_dir: Path = Path(scripts_dir)
        self._lock: threading.Lock = threading.Lock()
        self._running_scripts: Dict[str, subprocess.Popen] = {}

    def execute(self, action_config: ActionConfig) -> bool:
        """
        Execute an action based on configuration.

        Args:
            action_config: Dict with action type and parameters

        Returns:
            True if action was triggered, False otherwise
        """
        action_type: Optional[str] = action_config.get("type")

        if action_type == "script":
            return self._run_script(action_config)
        elif action_type == "webhook":
            return self._run_webhook(action_config)
        elif action_type == "keyboard":
            return self._run_keyboard(action_config)
        else:
            print(f"Unknown action type: {action_type}")
            return False

    def _send_notification(self, title: str, message: str, urgency: str = "normal") -> None:
        """Send desktop notification using notify-send."""
        try:
            subprocess.run(
                ["notify-send", title, message, f"--urgency={urgency}"],
                capture_output=True,
                check=False
            )
        except Exception:
            # Silently fail if notify-send not available
            pass

    def _run_script(self, config: ActionConfig) -> bool:
        """
        Execute a bash or Python script with notifications.

        Config format:
        {
            "type": "script",
            "file": "script.sh",
            "args": ["arg1", "arg2"],
            "blocking": False  # Run in background or wait for completion
        }
        """
        filename: Optional[str] = config.get("file")
        args: List[str] = config.get("args", [])
        blocking: bool = config.get("blocking", False)

        if not filename:
            print("Script action missing 'file' parameter")
            self._send_notification("❌ Script Error", "Missing file parameter", "critical")
            return False

        # Resolve script path
        script_path: Path = self.scripts_dir / filename
        if not script_path.exists():
            # Try absolute path
            script_path = Path(filename)
            if not script_path.exists():
                print(f"Script not found: {filename}")
                self._send_notification("❌ Script Not Found", filename, "critical")
                return False

        # Build command
        cmd: List[str]
        if filename.endswith(".py"):
            cmd = ["python", str(script_path)] + args
        else:
            cmd = ["bash", str(script_path)] + args

        # Send start notification
        display_name = filename.replace('.sh', '').replace('.py', '').replace('_', ' ').title()
        self._send_notification("▶️ Script Started", display_name, "low")

        try:
            if blocking:
                # Run synchronously
                result: subprocess.CompletedProcess = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    error_msg = result.stderr[:100] if result.stderr else "Unknown error"
                    self._send_notification(
                        f"❌ {display_name} Failed",
                        f"Exit code {result.returncode}: {error_msg}",
                        "critical"
                    )
                    print(f"Script failed with code {result.returncode}: {result.stderr}")
                    return False
                
                # Success notification
                output_preview = result.stdout[:100] if result.stdout else "Completed successfully"
                self._send_notification(
                    f"✅ {display_name} Complete",
                    output_preview,
                    "normal"
                )
                return True
            else:
                # Run in background
                process: subprocess.Popen = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                script_key: str = f"{filename}_{threading.current_thread().ident}"
                with self._lock:
                    # Clean up finished scripts
                    for key, proc in list(self._running_scripts.items()):
                        if proc.poll() is not None:
                            del self._running_scripts[key]
                    self._running_scripts[script_key] = process
                
                # Background notification
                self._send_notification(
                    f"🔄 {display_name} Running",
                    "Script started in background",
                    "low"
                )
                return True

        except Exception as e:
            error_str = str(e)[:100]
            self._send_notification(
                f"❌ {display_name} Error",
                error_str,
                "critical"
            )
            print(f"Error running script {filename}: {e}")
            return False

    def _run_webhook(self, config: ActionConfig) -> bool:
        """
        Send HTTP webhook request.

        Config format:
        {
            "type": "webhook",
            "url": "https://api.example.com/webhook",
            "method": "POST",
            "headers": {"Authorization": "Bearer token"},
            "body": {"key": "value"}
        }
        """
        url: Optional[str] = config.get("url")
        method: str = config.get("method", "POST").upper()
        headers: Dict[str, str] = config.get("headers", {})
        body: Optional[Dict] = config.get("body")

        if not url:
            print("Webhook action missing 'url' parameter")
            return False

        try:
            import httpx

            response: httpx.Response
            if method == "POST":
                response = httpx.post(url, json=body, headers=headers, timeout=10.0)
            elif method == "GET":
                response = httpx.get(url, headers=headers, timeout=10.0)
            else:
                print(f"Unsupported HTTP method: {method}")
                return False

            response.raise_for_status()
            return True

        except ImportError:
            print("httpx not installed, cannot send webhooks")
            return False
        except Exception as e:
            print(f"Error sending webhook to {url}: {e}")
            return False

    def _run_keyboard(self, config: ActionConfig) -> bool:
        """
        Inject keyboard shortcut.

        Config format:
        {
            "type": "keyboard",
            "shortcut": "ctrl+shift+a"
        }
        """
        shortcut: Optional[str] = config.get("shortcut")

        if not shortcut:
            print("Keyboard action missing 'shortcut' parameter")
            return False

        try:
            from pynput.keyboard import Controller, Key

            # Parse shortcut string (e.g., "ctrl+shift+a")
            keys: List[str] = shortcut.lower().split("+")

            keyboard: Controller = Controller()

            # Map key names to pynput Key objects
            key_map: Dict[str, Key] = {
                "ctrl": Key.ctrl,
                "control": Key.ctrl,
                "shift": Key.shift,
                "alt": Key.alt,
                "cmd": Key.cmd,
                "command": Key.cmd,
                "win": Key.cmd,
                "tab": Key.tab,
                "enter": Key.enter,
                "return": Key.enter,
                "esc": Key.esc,
                "escape": Key.esc,
                "space": Key.space,
                "up": Key.up,
                "down": Key.down,
                "left": Key.left,
                "right": Key.right,
                "f1": Key.f1,
                "f2": Key.f2,
                "f3": Key.f3,
                "f4": Key.f4,
                "f5": Key.f5,
                "f6": Key.f6,
                "f7": Key.f7,
                "f8": Key.f8,
                "f9": Key.f9,
                "f10": Key.f10,
                "f11": Key.f11,
                "f12": Key.f12,
            }

            # Separate modifier keys from regular keys
            modifiers: List[Key] = []
            regular_keys: List = []

            for key in keys:
                if key in key_map:
                    if key in [
                        "ctrl",
                        "control",
                        "shift",
                        "alt",
                        "cmd",
                        "command",
                        "win",
                    ]:
                        modifiers.append(key_map[key])
                    else:
                        regular_keys.append(key_map[key])
                else:
                    # Regular character key
                    regular_keys.append(key)

            # Press modifiers
            for modifier in modifiers:
                keyboard.press(modifier)

            # Press regular keys
            for key in regular_keys:
                if isinstance(key, str):
                    keyboard.press(key)
                else:
                    keyboard.press(key)

            # Release in reverse order
            for key in reversed(regular_keys):
                if isinstance(key, str):
                    keyboard.release(key)
                else:
                    keyboard.release(key)

            for modifier in reversed(modifiers):
                keyboard.release(modifier)

            return True

        except ImportError:
            print("pynput not installed, cannot inject keyboard shortcuts")
            return False
        except Exception as e:
            print(f"Error injecting keyboard shortcut '{shortcut}': {e}")
            return False

    def cleanup(self) -> None:
        """Terminate any running background scripts."""
        with self._lock:
            for script_key, process in list(self._running_scripts.items()):
                try:
                    process.terminate()
                    process.wait(timeout=1.0)
                except:
                    try:
                        process.kill()
                    except:
                        pass
            self._running_scripts.clear()
