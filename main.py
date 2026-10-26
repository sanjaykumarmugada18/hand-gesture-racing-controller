
import cv2
import time
import math
import mediapipe as mp

from pathlib import Path

# Import our previously tested components.
from keyboard_controller import KeyboardController
from safety_hotkeys import SafetyHotkeys


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "hand_landmarker.task"
)

# Finger recognition settings.
FINGER_OPEN_ANGLE = 160
THUMB_OPEN_ANGLE = 150
THUMB_SPREAD_RATIO = 1.15

# Gesture must remain consistent for 150 ms.
GESTURE_CONFIRMATION_TIME = 0.15

FINGER_NAMES = [
    "Thumb", "Index", "Middle", "Ring", "Pinky"
]

DRIVING_COMMANDS = {
    "ACCELERATE",
    "ACCELERATE + LEFT",
    "ACCELERATE + RIGHT",
    "BRAKE"
}

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]


def landmark_distance(a, b, width, height):
    """Calculate pixel distance between landmarks."""

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
    """Determine which individual fingers are open."""

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

    tip_distance = landmark_distance(
        landmarks[4],
        landmarks[17],
        width,
        height
    )

    base_distance = landmark_distance(
        landmarks[2],
        landmarks[17],
        width,
        height
    )

    states["Thumb"] = (
        thumb_angle >= THUMB_OPEN_ANGLE
        and base_distance > 0
        and tip_distance > base_distance * THUMB_SPREAD_RATIO
    )

    return states


def recognize_gesture(states, hand_label):
    """Translate finger combinations into commands."""

    if hand_label not in ("Left", "Right"):
        return "UNKNOWN"

    pattern = tuple(
        states[finger] for finger in FINGER_NAMES
    )

    # Closed fist.
    if pattern == (False, False, False, False, False):
        return "BRAKE"

    # Fully open palm.
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
    """Obtain command from exactly one detected hand."""

    count = len(result.hand_landmarks)

    if count == 0:
        return "TRACKING LOST", None, None

    if count > 1:
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
    """Confirm driving gestures and reset unsafe states."""

    def __init__(self, confirmation_time=0.15):
        self.confirmation_time = confirmation_time
        self.reset()

    def reset(self):
        self.active_command = "NEUTRAL"
        self.active_hand = None
        self.clear_pending()

    def clear_pending(self):
        self.pending_command = None
        self.pending_hand = None
        self.pending_since = None

    def update(self, raw_command, hand_label, now):

        # Tracking errors and invalid gestures immediately
        # clear the active driving command.
        if raw_command in (
            "TRACKING LOST",
            "MULTIPLE HANDS",
            "UNKNOWN"
        ):
            self.reset()
            return raw_command, "SAFETY RESET"

        # Neutral takes effect immediately.
        if raw_command == "NEUTRAL":
            self.reset()
            return "NEUTRAL", "STABLE"

        if raw_command not in DRIVING_COMMANDS:
            self.reset()
            return "UNKNOWN", "SAFETY RESET"

        # Continue an already stable gesture.
        if (
            raw_command == self.active_command
            and hand_label == self.active_hand
        ):
            self.clear_pending()
            return self.active_command, "STABLE"

        # Start confirmation of a new gesture.
        if (
            raw_command != self.pending_command
            or hand_label != self.pending_hand
        ):
            self.pending_command = raw_command
            self.pending_hand = hand_label
            self.pending_since = now

            # Release previous driving input immediately
            # while confirming the new gesture.
            self.active_command = "NEUTRAL"
            self.active_hand = None

            return "NEUTRAL", "CONFIRMING"

        elapsed = now - self.pending_since

        if elapsed >= self.confirmation_time:
            self.active_command = self.pending_command
            self.active_hand = self.pending_hand
            self.clear_pending()

            return self.active_command, "STABLE"

        return "NEUTRAL", "CONFIRMING"


def draw_hand_landmarks(frame, landmarks):
    """Draw hand skeleton on the mirrored preview."""

    height, width, _ = frame.shape
    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        points.append((width - 1 - x, y))

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


def draw_text(frame, text, x, y, color, scale=0.55):
    """Small helper for webcam status labels."""

    cv2.putText(
        frame,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        2
    )


def main():
    print("======================================")
    print(" Hand Gesture Racing Controller")
    print("======================================")

    if not MODEL_PATH.is_file():
        print(f"Missing model: {MODEL_PATH}")
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

    # Our three integration components.
    stabilizer = GestureStabilizer(
        GESTURE_CONFIRMATION_TIME
    )

    controller = KeyboardController()
    hotkeys = SafetyHotkeys()

    # Software emergency-stop latch.
    emergency_stopped = False

    camera = None

    fps = 0.0
    frame_count = 0
    fps_start_time = time.perf_counter()

    video_start_time = time.perf_counter()
    last_timestamp_ms = -1

    print("\nControls:")
    print("F8  - Enable / Disable")
    print("F9  - Emergency stop")
    print("F10 - Exit")
    print("Q   - Exit (when webcam window is focused)")

    print("\nController starts DISABLED.")
    print("Open palm before enabling control.")

    try:
        camera = cv2.VideoCapture(0)

        if not camera.isOpened():
            print("Error: Could not open webcam.")
            return

        hotkeys.start()

        print("\nWebcam and safety listener started.")

        with mp.tasks.vision.HandLandmarker.create_from_options(
            options
        ) as landmarker:

            while True:

                # ------------------------------------
                # 1. Handle global safety shortcuts.
                # ------------------------------------

                if hotkeys.exit_requested.is_set():
                    print("\nF10: Exit requested.")
                    break

                # Emergency stop takes priority over F8.
                if hotkeys.stop_requested.is_set():
                    hotkeys.stop_requested.clear()
                    hotkeys.toggle_requested.clear()

                    emergency_stopped = True

                    controller.emergency_stop()
                    stabilizer.reset()

                    print(
                        "Emergency stop locked. "
                        "Restart required to re-enable."
                    )

                if hotkeys.toggle_requested.is_set():
                    hotkeys.toggle_requested.clear()

                    if emergency_stopped:
                        print(
                            "Cannot enable: emergency stop active."
                        )

                    elif controller.enabled:
                        controller.disable()
                        stabilizer.reset()

                    else:
                        stabilizer.reset()
                        controller.enable()

                # ------------------------------------
                # 2. Capture webcam frame.
                # ------------------------------------

                success, original_frame = camera.read()

                if not success:
                    print("Webcam frame capture failed.")
                    break

                height, width, _ = original_frame.shape

                # ------------------------------------
                # 3. MediaPipe hand detection.
                # ------------------------------------

                rgb_frame = cv2.cvtColor(
                    original_frame,
                    cv2.COLOR_BGR2RGB
                )

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame
                )

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

                display_frame = cv2.flip(
                    original_frame,
                    1
                )

                for landmarks in result.hand_landmarks:
                    draw_hand_landmarks(
                        display_frame,
                        landmarks
                    )

                # ------------------------------------
                # 4. Recognize driving gesture.
                # ------------------------------------

                raw_command, hand_label, finger_states = (
                    get_control_state(result, width, height)
                )

                stable_command, stability_status = (
                    stabilizer.update(
                        raw_command,
                        hand_label,
                        time.perf_counter()
                    )
                )

                # ------------------------------------
                # 5. Game keyboard integration.
                # ------------------------------------

                # Recheck safety requests before
                # sending new keyboard events.
                if hotkeys.exit_requested.is_set():
                    break

                if hotkeys.stop_requested.is_set():
                    hotkeys.stop_requested.clear()
                    hotkeys.toggle_requested.clear()

                    emergency_stopped = True

                    controller.emergency_stop()
                    stabilizer.reset()

                    print("Emergency stop activated.")

                if controller.enabled and not emergency_stopped:
                    controller.update(stable_command)
                else:
                    # Disabled state never sends driving keys.
                    stabilizer.reset()

                # ------------------------------------
                # 6. Update FPS.
                # ------------------------------------

                frame_count += 1
                now = time.perf_counter()
                elapsed = now - fps_start_time

                if elapsed >= 1.0:
                    fps = frame_count / elapsed
                    frame_count = 0
                    fps_start_time = now

                # ------------------------------------
                # 7. Draw the information overlay.
                # ------------------------------------

                green = (0, 255, 0)
                white = (255, 255, 255)
                orange = (0, 165, 255)
                red = (0, 0, 255)

                draw_text(
                    display_frame,
                    f"FPS: {fps:.1f} | Hands: {len(result.hand_landmarks)}",
                    15, 30, green
                )

                if emergency_stopped:
                    mode = "EMERGENCY STOP"
                    mode_color = red

                elif controller.enabled:
                    mode = "ENABLED"
                    mode_color = green

                else:
                    mode = "DISABLED"
                    mode_color = orange

                draw_text(
                    display_frame,
                    f"CONTROL: {mode}",
                    15, 60, mode_color
                )

                draw_text(
                    display_frame,
                    f"Hand: {hand_label or 'None'}",
                    15, 90, white
                )

                if finger_states is not None:
                    finger_text = " ".join(
                        f"{name[0]}:{int(finger_states[name])}"
                        for name in FINGER_NAMES
                    )

                    draw_text(
                        display_frame,
                        finger_text,
                        15, 120, white, 0.46
                    )

                draw_text(
                    display_frame,
                    f"RAW: {raw_command}",
                    15, height - 115, white, 0.5
                )

                draw_text(
                    display_frame,
                    f"STATUS: {stability_status}",
                    15, height - 85, orange, 0.5
                )

                # Show what is actually allowed
                # to reach the keyboard controller.
                if controller.enabled and not emergency_stopped:
                    output_command = stable_command
                else:
                    output_command = "NEUTRAL"

                draw_text(
                    display_frame,
                    f"OUTPUT: {output_command}",
                    15, height - 55,
                    green if output_command in DRIVING_COMMANDS
                    else orange,
                    0.57
                )

                draw_text(
                    display_frame,
                    "F8 Toggle | F9 Stop | F10 Exit",
                    15, height - 18, white, 0.48
                )

                cv2.imshow(
                    "Gesture Racing Controller - LIVE",
                    display_frame
                )

                # Q works when OpenCV has focus.
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("\nQ: Exit requested.")
                    break

    except KeyboardInterrupt:
        print("\nInterrupted from terminal.")

    except Exception as exc:
        print(f"\nController error: {exc}")

    finally:
        # The controller should not remain enabled.
        # Attempt key release even on errors.
        try:
            controller.disable()
        except Exception as exc:
            print(f"Key release warning: {exc}")

        try:
            hotkeys.close()
        except Exception as exc:
            print(f"Hotkey listener warning: {exc}")

        if camera is not None:
            camera.release()

        cv2.destroyAllWindows()

        print("Webcam closed.")
        print("Controller cleanup completed.")


if __name__ == "__main__":
    main()
