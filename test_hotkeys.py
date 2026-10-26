
import time
from safety_hotkeys import SafetyHotkeys


def main():
    print("Safety Hotkey Test")
    print("------------------")
    print("F8  = Enable / Disable")
    print("F9  = Emergency Stop")
    print("F10 = Exit")

    enabled = False
    emergency_stopped = False

    hotkeys = SafetyHotkeys()
    hotkeys.start()

    try:
        while not hotkeys.exit_requested.is_set():

            # Emergency stop has highest priority.
            if hotkeys.stop_requested.is_set():
                hotkeys.stop_requested.clear()

                emergency_stopped = True
                enabled = False

                print("EMERGENCY STOP ACTIVATED")

            # Toggle only if emergency stop is not active.
            if hotkeys.toggle_requested.is_set():
                hotkeys.toggle_requested.clear()

                if emergency_stopped:
                    print(
                        "Restart required after emergency stop."
                    )
                else:
                    enabled = not enabled

                    if enabled:
                        print("Controller ENABLED")
                    else:
                        print("Controller DISABLED")

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    finally:
        enabled = False
        hotkeys.close()
        print("Safety hotkey test finished.")


if __name__ == "__main__":
    main()
