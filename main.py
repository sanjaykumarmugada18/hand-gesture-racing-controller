
import cv2
import time


def main():
    print("Starting Hand Gesture Racing Controller...")

    # Open the default webcam.
    camera = cv2.VideoCapture(0)

    # Verify that the webcam opened successfully.
    if not camera.isOpened():
        print("Error: Unable to access the webcam.")
        return

    print("Webcam started successfully!")
    print("Press Q in the camera window to exit.")

    # Initialize FPS measurement variables.
    fps_start_time = time.perf_counter()
    frame_count = 0
    fps = 0.0

    try:
        while True:
            # Step 1: Capture a frame from the webcam.
            success, frame = camera.read()

            if not success:
                print("Failed to capture a frame.")
                break

            # Step 2: Mirror the webcam frame.
            frame = cv2.flip(frame, 1)

            # Step 3: Get frame dimensions.
            height, width, channels = frame.shape

            # Step 4: Count the current frame.
            frame_count += 1

            # Get current time.
            current_time = time.perf_counter()

            # Calculate elapsed time.
            elapsed_time = current_time - fps_start_time

            # Update FPS approximately every second.
            if elapsed_time >= 1.0:
                fps = frame_count / elapsed_time

                # Reset measurement variables.
                frame_count = 0
                fps_start_time = current_time

            # Step 5: Display resolution.
            cv2.putText(
                frame,
                f"Resolution: {width} x {height}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Step 6: Display FPS.
            cv2.putText(
                frame,
                f"FPS: {fps:.2f}",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Step 7: Display webcam preview.
            cv2.imshow(
                "Hand Gesture Controller - Webcam",
                frame
            )

            # Step 8: Press Q to exit.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Exiting...")
                break

    finally:
        # Release webcam and close all windows.
        camera.release()
        cv2.destroyAllWindows()

        print("Webcam released and all windows closed.")


if __name__ == "__main__":
    main()
