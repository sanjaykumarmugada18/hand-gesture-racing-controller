
import time
from keyboard_controller import KeyboardController


# Keep each test hold short.
TEST_DURATION = 0.6


def main():
    print("=================================")
    print("   Keyboard Controller Test")
    print("=================================")

    print("This test sends WASD keyboard events.")
    print("Open a blank Windows Notepad window.")
    print("The test starts with the controller disabled.")

    input("\nPress Enter when ready...")

    print("\nSwitch to Notepad now!")

    for seconds in range(5, 0, -1):
        print(f"Starting in {seconds}...")
        time.sleep(1)

    controller = KeyboardController()

    try:
        controller.enable()

        test_commands = [
            "ACCELERATE",
            "ACCELERATE + RIGHT",
            "ACCELERATE",
            "ACCELERATE + LEFT",
            "NEUTRAL",
            "BRAKE",
            "NEUTRAL"
        ]

        for command in test_commands:
            print(f"\nCOMMAND: {command}")

            controller.update(command)

            time.sleep(TEST_DURATION)

        print("\nTesting emergency stop...")

        controller.update("ACCELERATE")
        time.sleep(0.3)

        controller.emergency_stop()

        print("\nTest completed successfully!")

    finally:
        # Attempt cleanup even if an error occurs.
        controller.disable()


if __name__ == "__main__":
    main()
