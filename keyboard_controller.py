
import pydirectinput


# Default keyboard mappings for our racing controller.
COMMAND_KEYS = {
    "ACCELERATE": {"w"},
    "ACCELERATE + LEFT": {"w", "a"},
    "ACCELERATE + RIGHT": {"w", "d"},
    "BRAKE": {"s"},
    "NEUTRAL": set()
}


class KeyboardController:
    """Manage simulated keyboard holds and releases."""

    def __init__(self, key_mapping=None):
        self.key_mapping = (
            key_mapping if key_mapping is not None
            else COMMAND_KEYS
        )

        # Keys currently held by our controller.
        self.held_keys = set()

        # Control starts disabled for safety.
        self.enabled = False

        # PyDirectInput's default pause is unnecessary
        # between our individual key events.
        pydirectinput.PAUSE = 0

    def enable(self):
        self.enabled = True
        print("Keyboard controller ENABLED")

    def disable(self):
        self.enabled = False
        self.release_all()
        print("Keyboard controller DISABLED")

    def update(self, command):
        """Synchronize held keys with the requested command."""

        if not self.enabled:
            self.release_all()
            return

        # Unknown commands must not cause movement.
        target_keys = set(
            self.key_mapping.get(command, set())
        )

        # Release keys that are no longer needed.
        keys_to_release = self.held_keys - target_keys

        for key in sorted(keys_to_release):
            self._release_key(key)

        # Press newly required keys.
        keys_to_press = target_keys - self.held_keys

        for key in sorted(keys_to_press):
            self._press_key(key)

    def _press_key(self, key):
        """Send a key-down event and record the hold."""

        if key in self.held_keys:
            return

        success = pydirectinput.keyDown(
            key,
            _pause=False
        )

        if success is not True:
            self.release_all()
            self.enabled = False
            raise RuntimeError(
                f"Windows did not confirm keyDown for {key}"
            )

        self.held_keys.add(key)
        print(f"KEY DOWN: {key.upper()}")

    def _release_key(self, key):
        """Send a key-up event."""

        success = pydirectinput.keyUp(
            key,
            _pause=False
        )

        if success is not True:
            raise RuntimeError(
                f"Windows did not confirm keyUp for {key}"
            )

        self.held_keys.discard(key)
        print(f"KEY UP: {key.upper()}")

    def release_all(self):
        """Attempt to release every controller-held key."""

        errors = []

        for key in sorted(self.held_keys):
            try:
                self._release_key(key)
            except Exception as exc:
                errors.append(str(exc))

        if errors:
            raise RuntimeError(
                "Some key releases were not confirmed: "
                + "; ".join(errors)
            )

    def emergency_stop(self):
        """Immediately disable control and release keys."""

        self.enabled = False
        self.release_all()
        print("EMERGENCY STOP")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disable()
        return False
