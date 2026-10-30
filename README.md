# AI Virtual Steering Wheel

Control keyboard-based racing games with two hands and a webcam. MediaPipe Tasks tracks the hands, OpenCV draws the dashboard, and pynput sends arrow keys.

## October 2026 update

The app now uses MediaPipe's **Hand Landmarker Tasks API**. It also fixes camera fallback, steering hysteresis, mirrored hand ordering, and key release on camera failure. See [UPDATE_NOTES.md](UPDATE_NOTES.md) for online sources and dependency versions checked on **2026-10-30**.

## Setup

Use **64-bit Python 3.12, 3.13, or 3.14** and a webcam. The pinned NumPy version requires Python 3.12 or newer. MediaPipe wheels must be available for your OS and architecture; Windows x64 is the development environment for this copy.

Clone this repository and open the folder containing `app.py`:

```bash
git clone https://github.com/AshokRana25/LocalData.git
cd LocalData
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/download_model.py
.\.venv\Scripts\python.exe app.py --preview
```

Python 3.13 was used for validation. Use `py -3.14` or `py -3.12` instead if that is your installed Python version. Activation is optional when using the interpreter path shown above. See [validation notes](UPDATE_NOTES.md#validation) for the tested environment and remaining limitations.

Linux or macOS, on a platform supported by MediaPipe:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/download_model.py
.venv/bin/python app.py --preview
```

The model downloader retrieves Google's versioned Hand Landmarker model and checks its SHA-256 before saving it. If `assets/hand_landmarker.task` already contains the verified model, it needs no download. Camera frames are processed locally. MediaPipe documents library performance/usage telemetry in its [privacy notice](https://pypi.org/project/mediapipe/).

Install only `opencv-contrib-python`: MediaPipe depends on that distribution. Do not also install `opencv-python` or either headless package in this environment; they share the same `cv2` module. Start a fresh virtual environment if upgrading an older installation containing multiple OpenCV distributions.

## Run

First check tracking with keyboard output disabled:

```powershell
.\.venv\Scripts\python.exe app.py --preview
```

Then start normal control and focus your game:

```powershell
.\.venv\Scripts\python.exe app.py
```

Options:

```text
--camera 1          Select a different camera (default: 0)
--model PATH       Use another Hand Landmarker .task model
--preview          Display tracking without sending keyboard input
--help             Show command-line help
```

Press **Q** or **Escape** with the camera window focused, close that window, or press **Ctrl+C** in the terminal to stop. The app releases keys it holds on exit.

## Controls

| Gesture | Action |
| --- | --- |
| Both fists | Accelerate / Up arrow |
| Both open hands | Brake / Down arrow |
| One open hand and one fist | Neutral throttle |
| Tilt the wrist-to-wrist line left/right | Left/right arrow |
| Fewer than two tracked hands for 8 frames | Release held keys |
| Camera read failure | Release held keys and stop |

Keep both hands visible with fingers pointing upward. Three of the four non-thumb fingertips above their PIP joints count as an open hand. This simple gesture rule is sensitive to hand rotation and occlusion.

Steering uses wrists in **screen order** and **pixel coordinates**, preserving angles on rectangular frames. A turn starts beyond 12 degrees and remains held until the angle moves inside 6 degrees. `L` and `R` on the dashboard refer to screen positions. The speedometer is an animation, not actual game telemetry.

## Troubleshooting

- `Cannot open camera`: allow desktop apps to access the camera, close apps already using it, and try `--camera 1`. Windows tries DirectShow first and then OpenCV's default backend. Other platforms use their default backend.
- `Camera stopped providing frames`: reconnect or select another camera and restart. The app stops instead of keeping acceleration pressed.
- Missing model: run `python scripts/download_model.py` with the environment's interpreter or pass `--model PATH`. The default path is relative to the source folder, so launching from a different working directory also works.
- `mediapipe` has no `solutions`: run this updated `app.py`, which uses Tasks.
- Keyboard input may require Accessibility permission on macOS. Linux sessions must support pynput's input backend; Wayland can restrict input injection. Some games do not accept synthetic keys. See [pynput's platform limitations](https://pynput.readthedocs.io/en/latest/limitations.html).

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Regression tests use fake keyboard and camera objects. They cover steering, throttle transitions, MediaPipe timestamps, camera fallback, tracking loss, preview mode, and resource cleanup without sending real keyboard input.

For the tested local environment, replace `.venv` with `.venv313` in the test command.

## Files

```text
app.py                       Camera loop, controller, and dashboard
hand_tracking.py             MediaPipe Tasks adapter and landmark drawing
requirements.txt             Pinned direct runtime dependencies
scripts/download_model.py    Verified model download
assets/hand_landmarker.task   Local model (downloaded, not committed)
tests/                       Regression tests
UPDATE_NOTES.md               Update research and validation record
```

`config.py`, `steering/steering_math.py`, `utils/logger.py`, and `canera.py` are existing helper/prototype files; `app.py` does not currently use them. Runtime tuning constants remain near the top of `app.py`.

## Author and upstream

Original project by **Sujal Shah** (B.Tech Computer Engineering, AI/ML): [sujalshah593/GamingSteering](https://github.com/sujalshah593/GamingSteering).

The project was originally extracted without Git history. This repository contains the updated source; machine-specific environments and backups are excluded.

The original README identifies the project as MIT-licensed. No LICENSE file was included in this local copy; third-party libraries and the model retain their respective licenses.
