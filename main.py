
import cv2
import time
import math
import mediapipe as mp
from pathlib import Path


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "hand_landmarker.task"
)

# Finger detection thresholds.
FINGER_OPEN_ANGLE = 160
THUMB_OPEN_ANGLE = 150
THUMB_SPREAD_RATIO = 1.15

# New: Gesture confirmation time in seconds.
GESTURE_CONFIRMATION_TIME = 0.15

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

FINGER_NAMES = [
    "Thumb", "Index", "Middle", "Ring", "Pinky"
]

DRIVING_COMMANDS = {
    "ACCELERATE",
    "ACCELERATE + LEFT",
    "ACCELERATE + RIGHT",
    "BRAKE"
}


def landmark_distance(a, b, width, height):
    dx = (a.x - b.x) * width
    dy = (a.y - b.y) * height

    return math.hypot(dx, dy)


def joint_angle(a, b, c, width, height):
    """Calculate angle ABC in degrees."""

    ab_x = (a.x - b.x) * width
    ab_y = (a.y - b.y) * height

    cb_x = (c.x - b.x) * width
    cb_y = (c.y - b.y) * height

    dot = ab_x * cb_x + ab_y * cb_y

    length_ab = math.hypot(ab_x, ab_y)
    length_cb = math.hypot(cb_x, cb_y)

    if length_ab == 0 or length_cb == 0:
        return 0.0

    cosine = dot / (length_ab * length_cb)
    cosine = max(-1.0, min(1.0, cosine))

    return math.degrees(math.acos(cosine))


def detect_finger_states(landmarks, width, height):
    """Detect which fingers are extended."""

    states = {}

    fingers = {
        "Index": (5, 6, 7, 8),
        "Middle": (9, 10, 11, 12),
        "Ring": (13, 14, 15, 16),
        "Pinky": (17, 18, 19, 20)
    }

    for name, (mcp, pip, dip, tip) in fingers.items():
        pip_angle = joint_angle(
            landmarks[mcp],
            landmarks[pip],
            landmarks[dip],
            width,
            height
        )

        dip_angle = joint_angle(
            landmarks[pip],
            landmarks[dip],
            landmarks[tip],
            width,
            height
        )

        states[name] = (
            pip_angle >= FINGER_OPEN_ANGLE
            and dip_angle >= FINGER_OPEN_ANGLE
        )

    thumb_angle = joint_angle(
        landmarks[1],
        landmarks[2],
        landmarks[3],
        width,
        height
    )

    thumb_tip_distance = landmark_distance(
        landmarks[4],
        landmarks[17],
        width,
        height
    )

    thumb_base_distance = landmark_distance(
        landmarks[2],
        landmarks[17],
        width,
        height
    )

    states["Thumb"] = (
        thumb_angle >= THUMB_OPEN_ANGLE
        and thumb_base_distance > 0
        and thumb_tip_distance
        > thumb_base_distance * THUMB_SPREAD_RATIO
    )

    return states


def recognize_gesture(states, hand_label):
    """Convert finger combinations into driving commands."""

    if hand_label not in ("Left", "Right"):
        return "UNKNOWN"

    pattern = tuple(
        states[finger] for finger in FINGER_NAMES
    )

    # Closed fist.
    if pattern == (False, False, False, False, False):
        return "BRAKE"

    # Open palm.
    if pattern == (True, True, True, True, True):
        return "NEUTRAL"

    # Index only.
    if pattern == (False, True, False, False, False):
        return "ACCELERATE"

    # Index + middle.
    if pattern == (False, True, True, False, False):
        if hand_label == "Right":
            return "ACCELERATE + RIGHT"
        return "ACCELERATE + LEFT"

    # Index + thumb.
    if pattern == (True, True, False, False, False):
        if hand_label == "Right":
            return "ACCELERATE + LEFT"
        return "ACCELERATE + RIGHT"

    return "UNKNOWN"


def get_control_state(result, width, height):
    """Read the current raw gesture and active hand."""

    hand_count = len(result.hand_landmarks)

    if hand_count == 0:
        return "TRACKING LOST", None, None

    if hand_count > 1:
        return "MULTIPLE HANDS", None, None

    if not result.handedness or not result.handedness[0]:
        return "UNKNOWN", None, None

    landmarks = result.hand_landmarks[0]
    hand_label = result.handedness[0][0].category_name

    finger_states = detect_finger_states(
        landmarks,
        width,
        height
    )

    command = recognize_gesture(
        finger_states,
        hand_label
    )

    return command, hand_label, finger_states


class GestureStabilizer:
    """
    Confirm valid driving gestures before accepting them.

    Unsafe or unavailable input immediately clears
    the active driving command.
    """

    def __init__(self, confirmation_time=0.15):
        self.confirmation_time = confirmation_time

        self.active_command = "NEUTRAL"
        self.active_hand = None

        self.pending_command = None
        self.pending_hand = None
        self.pending_since = None

    def clear_pending(self):
        self.pending_command = None
        self.pending_hand = None
        self.pending_since = None

    def update(self, raw_command, hand_label, now):
        """
        Return (stable_command, status).

        This class does not send keyboard inputs.
        """

        # Safety: Unavailable or invalid input takes
        # effect immediately, without waiting.
        if raw_command in (
            "TRACKING LOST",
            "MULTIPLE HANDS",
            "UNKNOWN"
        ):
            self.active_command = "NEUTRAL"
            self.active_hand = None
            self.clear_pending()

            return raw_command, "SAFETY RESET"

        # Open palm means release movement immediately.
        if raw_command == "NEUTRAL":
            self.active_command = "NEUTRAL"
            self.active_hand = hand_label
            self.clear_pending()

            return "NEUTRAL", "STABLE"

        # Reject unexpected commands safely.
        if raw_command not in DRIVING_COMMANDS:
            self.active_command = "NEUTRAL"
            self.active_hand = None
            self.clear_pending()

            return "UNKNOWN", "SAFETY RESET"

        # If the command and hand are already accepted,
        # continue using that stable command.
        if (
            raw_command == self.active_command
            and hand_label == self.active_hand
        ):
            self.clear_pending()

            return self.active_command, "STABLE"

        # New gesture or different controlling hand.
        if (
            raw_command != self.pending_command
            or hand_label != self.pending_hand
        ):
            self.pending_command = raw_command
            self.pending_hand = hand_label
            self.pending_since = now

            # Do not maintain the previous driving key
            # while a different gesture is being confirmed.
            self.active_command = "NEUTRAL"
            self.active_hand = None

            return "NEUTRAL", "CONFIRMING"

        # Check how long the same gesture has persisted.
        elapsed = now - self.pending_since

        if elapsed >= self.confirmation_time:
            self.active_command = self.pending_command
            self.active_hand = self.pending_hand

            self.clear_pending()

            return self.active_command, "STABLE"

        return "NEUTRAL", "CONFIRMING"


def draw_hand_landmarks(frame, landmarks):
    """Draw original-image landmarks on mirrored preview."""

    height, width, _ = frame.shape
    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        display_x = width - 1 - x
        points.append((display_x, y))

    for start, end in HAND_CONNECTIONS:
        cv2.line(
            frame,
            points[start],
            points[end],
            (0, 255, 0),
            2
        )

    for point in points:
        cv2.circle(
            frame,
            point,
            4,
            (0, 0, 255),
            -1
        )


def main():
    print("Starting Hand Gesture Racing Controller...")

    if not MODEL_PATH.is_file():
        print(f"Model not found: {MODEL_PATH}")
        return

    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Unable to access webcam.")
        return

    # NEW: Create our gesture stabilizer.
    stabilizer = GestureStabilizer(
        GESTURE_CONFIRMATION_TIME
    )

    print("Webcam started successfully!")
    print("Gesture stabilization enabled.")
    print("No keyboard inputs will be sent.")
    print("Press Q to exit.")

    fps_start_time = time.perf_counter()
    frame_count = 0
    fps = 0.0

    video_start_time = time.perf_counter()
    last_timestamp_ms = -1

    try:
        with mp.tasks.vision.HandLandmarker.create_from_options(
            options
        ) as landmarker:

            while True:
                # Capture original webcam frame.
                success, original_frame = camera.read()

                if not success:
                    print("Failed to capture frame.")
                    break

                height, width, _ = original_frame.shape

                # Convert BGR into RGB.
                rgb_frame = cv2.cvtColor(
                    original_frame,
                    cv2.COLOR_BGR2RGB
                )

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame
                )

                # MediaPipe requires increasing timestamps.
                timestamp_ms = int(
                    (time.perf_counter() - video_start_time)
                    * 1000
                )

                timestamp_ms = max(
                    timestamp_ms,
                    last_timestamp_ms + 1
                )

                last_timestamp_ms = timestamp_ms

                result = landmarker.detect_for_video(
                    mp_image,
                    timestamp_ms
                )

                # Mirror only the preview.
                display_frame = cv2.flip(
                    original_frame,
                    1
                )

                # Draw hand skeletons.
                for landmarks in result.hand_landmarks:
                    draw_hand_landmarks(
                        display_frame,
                        landmarks
                    )

                # Read raw command from finger gestures.
                raw_command, hand_label, finger_states = (
                    get_control_state(result, width, height)
                )

                # NEW: Stabilize command using elapsed time.
                stable_command, stability_status = (
                    stabilizer.update(
                        raw_command,
                        hand_label,
                        time.perf_counter()
                    )
                )

                # Calculate FPS.
                frame_count += 1
                current_time = time.perf_counter()
                elapsed_time = current_time - fps_start_time

                if elapsed_time >= 1.0:
                    fps = frame_count / elapsed_time
                    frame_count = 0
                    fps_start_time = current_time

                # Draw camera information.
                cv2.putText(
                    display_frame,
                    f"Resolution: {width} x {height}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    display_frame,
                    f"FPS: {fps:.2f}",
                    (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    display_frame,
                    f"Hands Detected: {len(result.hand_landmarks)}",
                    (20, 95),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

                active_hand = hand_label or "None"

                cv2.putText(
                    display_frame,
                    f"Active Hand: {active_hand}",
                    (20, 125),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )

                if finger_states is not None:
                    finger_text = "  ".join(
                        f"{name[0]}:{int(finger_states[name])}"
                        for name in FINGER_NAMES
                    )

                    cv2.putText(
                        display_frame,
                        finger_text,
                        (20, 155),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.48,
                        (255, 255, 255),
                        1
                    )

                # NEW: Display raw and accepted commands.
                cv2.putText(
                    display_frame,
                    f"RAW: {raw_command}",
                    (20, height - 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2
                )

                cv2.putText(
                    display_frame,
                    f"STATUS: {stability_status}",
                    (20, height - 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 255),
                    2
                )

                # Green when actively driving;
                # otherwise orange.
                if stable_command in DRIVING_COMMANDS:
                    command_color = (0, 255, 0)
                else:
                    command_color = (0, 165, 255)

                cv2.putText(
                    display_frame,
                    f"COMMAND: {stable_command}",
                    (20, height - 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    command_color,
                    2
                )

                cv2.imshow(
                    "Hand Gesture Controller - Stabilized",
                    display_frame
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("Exiting...")
                    break

    finally:
        # Clear the internal command state on exit.
        stabilizer.active_command = "NEUTRAL"
        stabilizer.active_hand = None
        stabilizer.clear_pending()

        camera.release()
        cv2.destroyAllWindows()

        print("Webcam released and windows closed.")


if __name__ == "__main__":
    main()
