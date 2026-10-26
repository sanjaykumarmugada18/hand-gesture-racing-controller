
import threading
from pynput import keyboard


class SafetyHotkeys:
    """Listen for global controller shortcuts."""

    def __init__(self):
        self.toggle_requested = threading.Event()
        self.stop_requested = threading.Event()
        self.exit_requested = threading.Event()

        self.pressed_keys = set()
        self.listener = None

    def on_press(self, key):
        # Ignore repeated key-down events.
        if key in self.pressed_keys:
            return

        self.pressed_keys.add(key)

        if key == keyboard.Key.f8:
            self.toggle_requested.set()

        elif key == keyboard.Key.f9:
            self.stop_requested.set()

        elif key == keyboard.Key.f10:
            self.exit_requested.set()

    def on_release(self, key):
        self.pressed_keys.discard(key)

    def start(self):
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

        self.listener.start()

    def close(self):
        if self.listener is not None:
            self.listener.stop()
            self.listener.join(timeout=1.0)
