# Hand Gesture Racing Controller

**Control racing games using hand gestures instead of a physical keyboard.**

A real-time computer-vision application that uses your webcam to recognize finger gestures and convert them into keyboard controls for compatible browser-based and Windows racing games.

Built with **Python, OpenCV, MediaPipe, PyDirectInput, and pynput**.

## Overview

Hand Gesture Racing Controller allows you to accelerate, steer left or right, and brake using finger combinations captured through your webcam.

Instead of relying on a particular game's API, the application simulates standard WASD keyboard inputs. This makes it usable with different racing and driving games that support compatible controls and accept simulated keyboard events.

The controller has been successfully tested with **K-Racing and multiple other racing games**.

## Key Features

- Real-time hand tracking using a webcam
- MediaPipe detection of 21 hand landmarks
- Finger-state recognition using joint angles and landmark distances
- Supports either the left or right hand
- Gesture-based acceleration, steering, and braking
- 150 ms gesture confirmation to reduce unwanted input
- Smoother acceleration and steering transitions
- Automatic release of driving keys when tracking is lost or an unknown gesture is detected
- Global keyboard shortcuts for enabling, disabling, and stopping the controller
- Windows executable distribution without requiring users to install Python separately

## Gesture Controls

The application uses five main finger combinations.

| Hand Gesture | Right Hand | Left Hand |
|---|---|---|
| Index finger only | Accelerate — W | Accelerate — W |
| Index + middle fingers | Accelerate + Right — W + D | Accelerate + Left — W + A |
| Index + thumb | Accelerate + Left — W + A | Accelerate + Right — W + D |
| Closed fist | Brake — S | Brake — S |
| Fully open palm | Neutral — release all driving keys | Neutral — release all driving keys |

**Additional behavior:**

- No hand detected: release driving keys
- Unknown gesture: release driving keys
- Multiple hands detected: release driving keys
- Controller disabled: no gesture-driven keyboard input

Only one hand can actively control the game at a time.

## Safety Shortcuts

| Keyboard Shortcut | Action |
|---|---|
| F8 | Enable or disable gesture control |
| F9 | Emergency stop and disable control until application restart |
| F10 | Exit the application |
| Q | Exit when the webcam preview window has focus |

The application always starts with gesture control **disabled**.

Show an open palm before enabling control with F8.

When the controller is disabled, it attempts to release its held driving keys.

**Important:** These are software safety mechanisms. If the application or operating system becomes unresponsive, immediate key release cannot be guaranteed.

## Download and Run on Windows

### Requirements

- Windows computer
- Working webcam
- Compatible browser-based or desktop racing game
- Game that supports WASD controls and accepts simulated keyboard input

### Installation

1. Open the **Releases** section of this GitHub repository.
2. Download `GestureRacingController-windows-v0.1.0.zip`.
3. Extract the entire ZIP file into a folder.
4. Open the extracted `GestureRacingController` folder.
5. Double-click `GestureRacingController.exe`.
6. Allow webcam access if requested by Windows.
7. Open a compatible racing game in your browser or on your desktop.
8. Start a driving session and ensure the game has keyboard focus.
9. Position one hand clearly in front of the webcam.
10. Show an open palm and press F8 to enable gesture control.
11. Use the assigned finger gestures to accelerate, steer, and brake.
12. Press F8 to disable control or F10 to exit.

**Important:** Keep the entire extracted application folder together, including the `_internal` dependency folder. Do not move the EXE out of that folder.

The packaged Windows version is intended to work without a separate Python installation.

## Game Compatibility

Hand Gesture Racing Controller is **not limited to one specific game**.

It translates recognized finger gestures into simulated WASD keyboard input sent to the currently focused application.

It can work with compatible:

- Browser-based racing games
- Windows desktop racing games
- Driving and vehicle simulation games that use the same controls

### Compatibility Requirements

For the current version, the game should:

1. Use **W** for acceleration.
2. Use **A** for left steering.
3. Use **D** for right steering.
4. Use **S** for braking.
5. Accept simulated keyboard events from Windows.

### Games Tested

The controller has been successfully tested with **K-Racing and several other racing games**.

K-Racing: https://k-racing.allmightdev.com/en/

Other tested games have not been individually documented.

**Note:** Compatibility is not guaranteed with every game. Some games use arrow keys, controller-only input, different mappings, or input systems that do not accept simulated keyboard events.

## How It Works

The application follows this processing pipeline:

```text
Webcam
   |
   v
OpenCV Frame Capture
   |
   v
MediaPipe Hand Landmark Detection
   |
   v
Finger State Recognition
   |
   v
Gesture Classification
   |
   v
Gesture Stabilization
   |
   v
Safety and Enable/Disable Checks
   |
   v
PyDirectInput Keyboard Controller
   |
   v
Compatible Racing Game
```

### 1. Webcam Capture

OpenCV continuously captures frames from the webcam.

### 2. Hand Landmark Detection

MediaPipe detects 21 landmarks for each visible hand.

### 3. Finger Recognition

The application uses joint angles and relative landmark distances to estimate whether individual fingers are extended or folded.

### 4. Gesture Classification

Specific finger combinations are mapped to commands such as acceleration, steering, braking, and neutral.

### 5. Gesture Stabilization

New driving gestures must remain consistent for approximately 150 milliseconds before being accepted.

Acceleration can remain active during confirmation of compatible steering transitions, improving the driving experience.

### 6. Keyboard Input

The KeyboardController sends simulated WASD key-down and key-up events.

It tracks the currently held keys to avoid unnecessary repeated presses.

### 7. Safety Handling

The application handles invalid gestures, tracking loss, disable requests, emergency-stop requests, and normal shutdown cleanup.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main application logic |
| OpenCV | Webcam capture and preview |
| MediaPipe | Hand landmark detection |
| PyDirectInput | Simulated Windows keyboard input |
| pynput | Global keyboard shortcut listening |
| PyInstaller | Windows executable packaging |
| Git and GitHub | Version control and distribution |

## Project Structure

```text
hand-gesture-racing-controller/
├── main.py
├── keyboard_controller.py
├── safety_hotkeys.py
├── test_keyboard.py
├── test_game.py
├── test_hotkeys.py
├── models/
│   └── hand_landmarker.task
├── requirements.txt
├── README.md
└── .gitignore
```

Build output and local virtual-environment files are excluded from the source repository.

## Running from Source

For developers who want to study or modify the application.

### Prerequisites

- Windows
- Python 3.14 or a compatible Python version
- Webcam
- Git

### 1. Clone the repository

```powershell
git clone https://github.com/sanjaykumarmugada18/hand-gesture-racing-controller.git
```

### 2. Enter the directory

```powershell
cd hand-gesture-racing-controller
```

### 3. Create a virtual environment

```powershell
python -m venv .venv
```

### 4. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 6. Verify the hand-tracking model

Ensure that the following model file exists:

```text
models/hand_landmarker.task
```

The model is required for MediaPipe hand landmark detection.

### 7. Start the application

```powershell
python main.py
```

The webcam preview will open with gesture control disabled.

Use F8 to enable gesture control after opening your chosen compatible racing game.

## Troubleshooting

### Webcam does not open

- Check Windows camera permissions.
- Close other applications that may be using the webcam.
- Restart the application.

### Gestures are not being recognized

- Ensure adequate lighting.
- Keep your hand visible to the camera.
- Avoid covering fingers with other fingers or objects.
- Try positioning your palm toward the webcam.

### Game does not respond

- Confirm that gesture control is enabled with F8.
- Check that the preview recognizes the intended command.
- Make sure the game window has keyboard focus.
- Verify the game uses WASD controls.
- Confirm the game accepts simulated keyboard events.

### F8, F9, or F10 does not respond

- Check whether your laptop requires the Fn key for function-key input.
- Make sure the application is still running.
- Some applications or system restrictions may interfere with global shortcuts.

### Windows displays a security warning

The application may be unsigned. Download releases only from the official project repository and verify their authenticity.

Do not disable Windows security protections to run the application.

## Known Limitations

- Windows-only implementation
- Requires a functioning webcam
- Supports one active controlling hand
- Current keyboard mappings use WASD
- Gesture mappings are fixed in the current version
- Recognition can be affected by poor lighting, occlusion, and unusual hand orientations
- The game must accept simulated keyboard input
- Keyboard events are directed to the currently focused application
- Safety shortcuts and key-release cleanup depend on the application's responsiveness
- Gesture steering is digital, not analog steering-wheel control

## Project Status

**Functional Windows application — version 0.1.0 release preparation.**

Core hand tracking, gesture recognition, keyboard integration, stabilization, and multi-game operation have been successfully demonstrated.

The application has also been successfully packaged and launched as a Windows executable.

## Author

**Sanjay Kumar Mugada**

GitHub: https://github.com/sanjaykumarmugada18

---

Built as a hands-on computer-vision and Python software-engineering project.