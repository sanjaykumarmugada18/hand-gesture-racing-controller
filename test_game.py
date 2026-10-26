
import time
from keyboard_controller import KeyboardController


# Short test durations to keep movement controlled.
ACCELERATE_TIME = 1.5
STEERING_TIME = 0.7
BRAKING_TIME = 0.7


def main():
    print("====================================")
    print("   Racing Game Compatibility Test")
    print("====================================")

    print("\nTest sequence:")
    print("1. Accelerate using W")
    print("2. Accelerate and steer right using W + D")
    print("3. Brake using S")
    print("4. Release all keys")

    print("\nOpen K-Racing in a single-player session.")
    print("Ensure the game is ready to receive keyboard input.")

    input("\nPress Enter to begin the countdown...")

    print("\nSwitch to the game now!")

    for seconds in range(5, 0, -1):
        print(f"Starting in {seconds}...")
        time.sleep(1)

    controller = KeyboardController()

    try:
        controller.enable()

        # Test 1: Accelerate.
        print("\nTEST 1: Accelerating...")
        controller.update("ACCELERATE")
        time.sleep(ACCELERATE_TIME)

        # Test 2: Continue accelerating and steer right.
        print("\nTEST 2: Steering right...")
        controller.update("ACCELERATE + RIGHT")
        time.sleep(STEERING_TIME)

        # Release both W and D before braking.
        print("\nReleasing movement keys...")
        controller.update("NEUTRAL")
        time.sleep(0.4)

        # Test 3: Brake.
        print("\nTEST 3: Braking...")
        controller.update("BRAKE")
        time.sleep(BRAKING_TIME)

        # Test 4: Release all keys.
        controller.update("NEUTRAL")

        print("\nAll tests completed!")

    finally:
        # Always attempt to disable and release
        # controller-held keys when leaving the test.
        controller.disable()
        print("Keyboard cleanup attempted.")


if __name__ == "__main__":
    main()
