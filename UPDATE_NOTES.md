# Update check: 2026-10-30

## Online findings

- **Original repository:** the latest commit is
  [`1c8557e` (Update README.md), 2026-07-26](https://github.com/sujalshah593/GamingSteering/commit/1c8557e15282fdf90d14b718e68af6f53b83e83e).
  No newer upstream commit was available when checked. These changes are local
  maintenance, not a newly published upstream release.
- **MediaPipe:** [PyPI 1.2.0](https://pypi.org/project/mediapipe/1.2.0/)
  was published on October 27 (UTC); the
  [GitHub release](https://github.com/google-ai-edge/mediapipe/releases/tag/v1.2.0)
  followed on October 28. Google's current
  [Python hand-tracking guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python)
  uses Hand Landmarker Tasks, including video-mode timestamps and tracking.
  Local inspection confirmed that the previously installed 1.0.0 has no
  `mp.solutions` attribute, which made the original app fail at import time.
- **OpenCV:** [opencv-contrib-python 5.0.0.93](https://pypi.org/project/opencv-contrib-python/5.0.0.93/)
  is the current contrib wheel. MediaPipe 1.2.0 requires it. OpenCV's package
  instructions say to install only one OpenCV distribution per environment.
- **NumPy:** [2.5.4](https://pypi.org/project/numpy/2.5.4/) was published
  October 10 and requires Python 3.12 or later.
- **pynput:** [1.8.2](https://pypi.org/project/pynput/1.8.2/) remains current.

## Applied changes

- Replaced legacy Solutions detection with Hand Landmarker in VIDEO mode,
  configured for two hands with strictly increasing monotonic timestamps.
- Reused the existing local model. Added a downloader for Google's versioned
  float16 model with SHA-256 verification and atomic installation.
- Reduced requirements to the four direct runtime libraries. Removed unrelated
  voice, GUI, gamepad, data-analysis, and inference dependencies from installation.
- Fixed the unreachable Windows camera fallback and selected a portable backend
  on non-Windows platforms. Added `--camera`, `--model`, and `--preview` options.
- Stopped on failed camera reads; ensured keys, detector, camera, and windows
  are cleaned up on normal exit and startup/runtime failures.
- Corrected steering hysteresis and non-square-frame angle calculation. Ordered
  wrists by screen position to avoid 180-degree jumps from handedness labels.
- Added regression tests and replaced outdated installation instructions.

## Validation

- **Passed:** 23 regression tests on Windows / Python 3.13.13 with MediaPipe
  1.2.0, opencv-contrib-python 5.0.0.93, NumPy 2.5.4, and pynput 1.8.2 in
  `.venv313`. Tests also passed before the package upgrade.
- **Passed:** real Hand Landmarker model initialization and inference on three
  synthetic blank frames with MediaPipe 1.2.0. This checks the native runtime,
  model format, and video timestamps, not real-hand detection accuracy.
- **Passed:** the local model matches the SHA-256 of Google's versioned
  float16/1 download:
  `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`.
- **Incomplete dependency check:** `pip check` reports that sounddevice 0.5.6
  requires CFFI. Repeated official PyPI downloads of CFFI failed with connection
  resets. MediaPipe handles the absent audio backend; this app uses only vision,
  which was tested successfully. To complete the environment when downloads work:

  ```powershell
  .\.venv313\Scripts\python.exe -m pip install cffi
  .\.venv313\Scripts\python.exe -m pip check
  ```

- **Fresh Python 3.14 environment not validated:** installation into `.venv`
  was interrupted by downloads of indirect dependencies. Use the upgraded
  `.venv313` environment for this local copy. The existing matplotlib 3.11.1 and
  its dependencies were retained there. The original installed-package list
  is saved in `.tmp/before-update-2026-10-30/requirements-installed.txt`.
- **Passed:** camera index 0 supplied five live frames, which were processed by
  the updated Hand Landmarker without sending keys or saving frames. The first
  sandboxed attempt could not open the camera; the check outside the sandbox
  succeeded. Camera fallback and disconnect behavior also passed mocked tests.
  Manual gesture accuracy and compatibility with a game remain unverified.

For the original development copy only, run from `GamingSteering-main`:

```powershell
.\.venv313\Scripts\python.exe app.py --preview
```

Remove `--preview` to enable keyboard controls.

Fresh clones of [AshokRana25/LocalData](https://github.com/AshokRana25/LocalData)
should follow the README to create `.venv` and download the model. The local
`.venv313` environment, downloaded wheels, and backups are not committed.
