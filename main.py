
import cv2
import time
import mediapipe as mp
from pathlib import Path


# Pretrained MediaPipe model.
MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "hand_landmarker.task"
)

# Pairs of landmark indices that form the hand skeleton.
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]


def draw_hand_landmarks(frame, hand_landmarks):
    """
    Draw landmarks onto a mirrored display frame.

    MediaPipe landmarks come from the original camera
    frame, so their X coordinates must be mirrored.
    """

    height, width, _ = frame.shape
    display_points = []

    for landmark in hand_landmarks:
        # Coordinates in the original image.
        original_x = int(landmark.x * width)
        original_y = int(landmark.y * height)

        # Convert X to the mirrored display coordinate.
        display_x = (width - 1) - original_x
        display_y = original_y

        display_points.append((display_x, display_y))

    # Draw connections.
    for start, end in HAND_CONNECTIONS:
        cv2.line(
            frame,
            display_points[start],
            display_points[end],
            (0, 255, 0),
            2
        )

    # Draw all 21 landmark points.
    for point in display_points:
        cv2.circle(
            frame,
            point,
            4,
            (0, 0, 255),
            -1
        )

    # Highlight wrist and index fingertip.
    cv2.circle(
        frame,
        display_points[0],
        8,
        (255, 0, 0),
        -1
    )

    cv2.circle(
        frame,
        display_points[8],
        8,
        (0, 255, 255),
        -1
    )

    return display_points


def main():
    print("Starting Hand Gesture Racing Controller...")

    if not MODEL_PATH.is_file():
        print(f"Error: Model not found at {MODEL_PATH}")
        return

    # Configure the MediaPipe model.
    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # Open the default webcam.
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Unable to access webcam.")
        return

    print("Webcam started successfully!")
    print("Press Q to exit.")

    # FPS measurement variables.
    fps_start_time = time.perf_counter()
    frame_count = 0
    fps = 0.0

    # MediaPipe video timestamp variables.
    video_start_time = time.perf_counter()
    last_timestamp_ms = -1

    try:
        with mp.tasks.vision.HandLandmarker.create_from_options(
            options
        ) as landmarker:

            while True:
                # STEP 1: Capture the ORIGINAL camera frame.
                success, original_frame = camera.read()

                if not success:
                    print("Failed to capture frame.")
                    break

                height, width, _ = original_frame.shape

                # STEP 2: Convert original BGR frame to RGB.
                rgb_frame = cv2.cvtColor(
                    original_frame,
                    cv2.COLOR_BGR2RGB
                )

                # STEP 3: Create a MediaPipe image.
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame
                )

                # STEP 4: Generate increasing timestamps.
                timestamp_ms = int(
                    (time.perf_counter() - video_start_time)
                    * 1000
                )

                timestamp_ms = max(
                    timestamp_ms,
                    last_timestamp_ms + 1
                )

                last_timestamp_ms = timestamp_ms

                # STEP 5: Process the ORIGINAL image.
                result = landmarker.detect_for_video(
                    mp_image,
                    timestamp_ms
                )

                # STEP 6: Mirror a copy for display only.
                display_frame = cv2.flip(
                    original_frame,
                    1
                )

                hands_detected = len(result.hand_landmarks)

                # STEP 7: Draw landmarks and hand identity.
                for hand_index, hand_landmarks in enumerate(
                    result.hand_landmarks
                ):
                    # Convert coordinates for mirrored display.
                    display_points = draw_hand_landmarks(
                        display_frame,
                        hand_landmarks
                    )

                    # Display coordinates in mirrored space.
                    wrist_x, wrist_y = display_points[0]
                    tip_x, tip_y = display_points[8]

                    # Read handedness from the ORIGINAL image.
                    if (
                        hand_index < len(result.handedness)
                        and result.handedness[hand_index]
                    ):
                        classification = result.handedness[
                            hand_index
                        ][0]

                        hand_label = classification.category_name
                        confidence = classification.score
                    else:
                        hand_label = "Unknown"
                        confidence = 0.0

                    # Display hand identity near the wrist.
                    label_x = max(
                        0,
                        min(wrist_x, width - 140)
                    )
                    label_y = max(20, wrist_y - 15)

                    cv2.putText(
                        display_frame,
                        f"{hand_label} ({confidence:.2f})",
                        (label_x, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 255, 255),
                        2
                    )

                    # Display coordinate information.
                    text_y = 155 + hand_index * 75

                    cv2.putText(
                        display_frame,
                        f"Detected: {hand_label}",
                        (20, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 255, 255),
                        2
                    )

                    cv2.putText(
                        display_frame,
                        f"Wrist: ({wrist_x}, {wrist_y})",
                        (20, text_y + 23),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1
                    )

                    cv2.putText(
                        display_frame,
                        f"Index Tip: ({tip_x}, {tip_y})",
                        (20, text_y + 46),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1
                    )

                # STEP 8: Calculate FPS.
                frame_count += 1

                current_time = time.perf_counter()
                elapsed_time = current_time - fps_start_time

                if elapsed_time >= 1.0:
                    fps = frame_count / elapsed_time
                    frame_count = 0
                    fps_start_time = current_time

                # STEP 9: Draw information on display frame.
                cv2.putText(
                    display_frame,
                    f"Resolution: {width} x {height}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    display_frame,
                    f"FPS: {fps:.2f}",
                    (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    display_frame,
                    f"Hands Detected: {hands_detected}",
                    (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                # STEP 10: Show the final mirrored preview.
                cv2.imshow(
                    "Hand Gesture Controller - Hand Identity",
                    display_frame
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("Exiting...")
                    break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Webcam released and all windows closed.")


if __name__ == "__main__":
    main()
