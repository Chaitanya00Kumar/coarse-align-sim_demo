import subprocess, sys

SCENE_SCRIPT = "scene_simulator.py"
DETECTOR_SCRIPT = "detector.py"
TRACKER_SCRIPT = "tracker.py"
ANALYSIS_SCRIPT = "performance_analyser.py"

def run_step(name, command):
    print(f"\n=== {name} ===")
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"[FAILED] {name} exited with code {result.returncode} — stopping pipeline.")
        sys.exit(1)

# 1. Scene generator — produces frames/ and ground_truth.csv
run_step("Scene generator", [sys.executable, SCENE_SCRIPT])

# 2. Detector — scans frames/ and produces detections.csv
run_step("Detector", [sys.executable, DETECTOR_SCRIPT])

# 3. Tracker — reads ground_truth.csv + detections.csv, produces tracking_data.csv
run_step("Running tracker", [sys.executable, TRACKER_SCRIPT])

# 4. Performance analysis — produces performance_report.png
run_step("Performance analysis", [sys.executable, ANALYSIS_SCRIPT])

print("\nPipeline complete. Check performance_report.png for results.")