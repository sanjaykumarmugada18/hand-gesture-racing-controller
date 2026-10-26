# Hand Gesture Racing Controller

Control an existing racing game using hand gestures captured through your webcam — without using the keyboard for driving.

A Windows desktop application built using **Python, OpenCV, MediaPipe, and PyDirectInput**.

## Overview

Hand Gesture Racing Controller uses computer vision to recognize finger combinations and translate them into keyboard inputs for racing games.

The application detects hand landmarks in real time, identifies finger positions, recognizes driving gestures, stabilizes the commands, and sends simulated keyboard events to the currently focused game.

The project has been successfully tested with the browser-based racing game **K-Racing**.

## Features

- Real-time webcam hand tracking with OpenCV and MediaPipe
- Recognition of individual finger states
- Support for physical left and right hands
- Gesture-based acceleration, steering, and braking
- Gesture stabilization and smoother steering transitions
- Automatic release of movement keys when tracking is lost
- Enable/disable controls and emergency-stop shortcuts
- Packaged Windows executable

## Gesture Controls

| Gesture | Right hand | Left hand |
|---|---|---|
| Index finger only | Accelerate (W) | Accelerate (W) |
| Index + middle | Accelerate + Right (W + D) | Accelerate + Left (W + A) |
| Index + thumb | Accelerate + Left (W + A) | Accelerate + Right (W + D) |
| Closed fist | Brake (S) | Brake (S) |
| Fully open palm | Neutral — release keys | Neutral — release keys |

Unknown gestures, tracking loss, and simultaneous detection of multiple hands release driving controls.

## Safety Shortcuts

| Key | Action |
|---|---|
| F8 | Enable or disable gesture control |
| F9 | Emergency stop; restart required to re-enable |
| F10 | Exit the application |
| Q | Exit when the webcam preview is focused |

The application always starts with gesture control disabled. Show an open palm before pressing F8 to enable it.

The emergency stop is software-based and depends on the application remaining responsive.

## Download and Run on Windows

1. Open the **Releases** section of this repository once a Windows release is available.
2. Download the Windows ZIP package.
3. Extract the entire ZIP into a folder.
4. Double-click `GestureRacingController.exe`.
5. Allow webcam access if Windows requests it.
6. Open a racing game that supports WASD keyboard controls.
7. Start a driving session, keep the game focused, and position your hand in view of the webcam.
8. Press F8 to enable gesture control.
9. Use your finger gestures to drive.

**Important:** Keep the executable and its `_internal` dependency folder together. Do not move the EXE out of the extracted folder.

The Windows release is intended to run without requiring a separate Python installation.

## Run from Source

For developers who want to inspect, learn from, or modify the project:

**Requirements:** Windows, a working webcam, Python, and Git.

Clone the repository:

`git clone https://github.com/sanjaykumarmugada18/hand-gesture-racing-controller.git`

Enter the project:

`cd hand-gesture-racing-controller`

Create a virtual environment:

`python -m venv .venv`

Activate it in PowerShell:

`.\.venv\Scripts\Activate.ps1`

Install dependencies:

`python -m pip install -r requirements.txt`

Run the application:

`python main.py`

The application also requires the MediaPipe hand-landmarker model at `models/hand_landmarker.task`. Ensure that this model file is present before launching the source version.

## How It Works

1. **Camera Capture:** OpenCV reads frames from the webcam.
2. **Hand Tracking:** MediaPipe identifies 21 hand landmarks.
3. **Finger Recognition:** Joint angles and landmark distances estimate whether each finger is extended.
4. **Gesture Classification:** Finger combinations are mapped to driving commands.
5. **Stabilization:** Driving gestures are confirmed before new commands are accepted.
6. **Keyboard Control:** PyDirectInput translates accepted commands into WASD key events.
7. **Safety Handling:** The controller releases movement keys on neutral, invalid gestures, tracking loss, disable, and normal shutdown attempts.

## Tested Game

**K-Racing (Browser)**

https://k-racing.allmightdev.com/en/

The Python version has been tested with K-Racing using simulated keyboard input and live webcam hand gestures.

Other browser and Windows racing games may work if they accept simulated keyboard input, but compatibility is not guaranteed.

## Limitations

- Currently designed for Windows.
- Requires a webcam and adequate lighting.
- Supports one active hand at a time.
- Uses fixed finger-gesture mappings and WASD keyboard controls.
- Gesture accuracy may decrease with occlusion, unusual hand orientations, or poor lighting.
- Keyboard input goes to the currently focused application.
- Software emergency-stop and cleanup mechanisms cannot guarantee key release during all system or process failures.
- Some games may reject simulated keyboard events.

## Tech Stack

- Python
- OpenCV
- MediaPipe Hand Landmarker
- PyDirectInput
- pynput
- PyInstaller
- Git and GitHub

## Project Status

**Working prototype — Windows packaging validated locally.**

Gesture recognition, keyboard integration, and live browser-game control have been demonstrated. Distribution testing and the public release are the remaining steps.

## Author

Sanjay Kumar Mugada

GitHub: https://github.com/sanjaykumarmugada18

---

Built as a hands-on computer-vision and Python software-engineering project.