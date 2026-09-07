# coarse-align-sim_demo

A demo build for **SIH26169 — Development of an AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile Free-Space Optical (FSO) Communication Terminals**, built by students for Smart India Hackathon.

## What this is

Free-Space Optical (FSO) links use a narrow laser beam instead of a cable or radio signal to connect two devices. If either end is moving, a camera-based **coarse alignment** system has to keep the other terminal roughly centered in view before a precision system can lock the beam.

This repo is a **simulation testbed for the tracking + control loop** that would sit behind that coarse-alignment camera — built and validated against a synthetic target before pointing it at a real one. It is not yet a full AI-based detector; see [Status & scope](#status--scope) below for exactly what's real and what's a placeholder.

## Pipeline

```
scene_simulator.py  →  detector.py  →  tracker.cpp  →  performance_analyser.py
   (fake camera)      (find target)   (filter+control)      (report)
```

All four stages live in `pipeline/` and are wired together: each stage reads the previous stage's real output file, not synthetic data of its own.

| Stage | File | What it does |
|---|---|---|
| 1. Simulated camera | `pipeline/scene_simulator.py` | Renders a target moving around a frame, degrades it with blur/noise/jitter (`disturbance.py`), saves frames to `pipeline/frames/` and the true position to `pipeline/ground_truth.csv`. |
| 2. Detector | `pipeline/detector.py` | Scans each saved frame for the target (HSV color-blob detection) and writes what it found — including missed frames — to `pipeline/detections.csv`. |
| 3. Tracker | `pipeline/tracker.cpp` | Reads `ground_truth.csv` and `detections.csv` frame-by-frame. Runs a Kalman filter to smooth noisy/missing detections, then a PID controller to drive a simulated pan-tilt servo toward the target. Writes `pipeline/tracking_data.csv`. |
| 4. Analyser | `pipeline/performance_analyser.py` | Reads `tracking_data.csv`, prints detection rate and tracking error stats, and plots `pipeline/performance_report.png` (true vs. tracked trajectory, error over time). |

`reference/kalman_pan_tilt_control_reference.cpp` is an earlier, self-contained version of the tracker (fully synthetic circular-motion target, fixed random seed, no file I/O) kept for reference only — it does not read the pipeline's CSVs. Use `pipeline/tracker.cpp` for the real, wired pipeline.

## Requirements

- Python 3.9+ with the packages in `requirements.txt`
- A C++17 compiler (`g++`, MinGW-w64, or MSVC)

```bash
pip install -r requirements.txt
```

## Running it

From the `pipeline/` directory:

```bash
cd pipeline

# Run the whole pipeline in one go
python3 run_pipeline.py

# ...or run each stage yourself:

# 1. Simulate the camera feed
python3 scene_simulator.py
# opens a window; close it, press Ctrl+C, or let it hit the 300-frame cap
# (headless machines: prefix with SDL_VIDEODRIVER=dummy)

# 2. Detect the target in the simulated frames
python3 detector.py

# 3. Compile and run the tracker
g++ -std=c++17 -O2 tracker.cpp -o tracker
./tracker

# 4. Generate the performance report
python3 performance_analyser.py
```

Each step reads the previous step's output file from the current directory, so run them from `pipeline/`, in order.

## Status & scope

This demo proves out the **filtering and control math**, which is the part most likely to be subtly wrong and the hardest to debug against a real, uncontrollable camera feed. What's genuinely working vs. what's a stand-in for the real problem statement:

| Piece | Currently | Needed for the real problem statement |
|---|---|---|
| Target | Simulated dot bouncing in a synthetic frame | A real (or photorealistic) optical terminal, seen through an actual camera |
| Detector | HSV color-threshold blob detection | An AI/vision-based detector (e.g. a trained model) robust to real-world conditions |
| Kalman filter + PID + servo control | **Real, working, and directly reusable** | No change needed — this is the reusable core |

Swapping in a real camera feed and a trained detector should drop straight into `detector.py` without touching the Kalman/PID/servo logic in `tracker.cpp` — it only depends on `detections.csv`'s column format (`frame,detected,det_x,det_y`).

## Repo layout

```
pipeline/
  scene_simulator.py                  # simulated disturbed camera feed + ground truth
  disturbance.py                      # blur/noise/jitter applied to simulated frames
  detector.py                         # finds the target in each frame -> detections.csv
  tracker.cpp                         # Kalman filter + PID + servo control -> tracking_data.csv
  performance_analyser.py             # stats + plots from tracking_data.csv
  run_pipeline.py                     # runs all of the above in order
reference/
  kalman_pan_tilt_control_reference.cpp   # earlier standalone tracker version (reference only)
requirements.txt
.gitignore
```

Generated at runtime (not committed): `pipeline/frames/`, `pipeline/ground_truth.csv`, `pipeline/detections.csv`, `pipeline/tracking_data.csv`, `pipeline/performance_report.png`, compiled binaries.
