import subprocess, sys, platform, os

# --- these must match your actual filenames exactly ---
SCENE_SCRIPT = "scene_simulator.py"
DETECTOR_SCRIPT = "detector.py"
TRACKER_SOURCE = "tracker.cpp"
ANALYSIS_SCRIPT = "performance_analyser.py"

IS_WINDOWS = platform.system() == "Windows"
TRACKER_BINARY = os.path.join(".", "tracker.exe" if IS_WINDOWS else "tracker")


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

# 3. Compile the tracker
compile_cmd = ["g++", "-std=c++17", "-O2", TRACKER_SOURCE, "-o", "tracker.exe" if IS_WINDOWS else "tracker"]
run_step("Compiling tracker", compile_cmd)

# 4. Run the tracker — reads ground_truth.csv + detections.csv, produces tracking_data.csv
run_step("Running tracker", [TRACKER_BINARY])

# 5. Performance analysis — produces performance_report.png
run_step("Performance analysis", [sys.executable, ANALYSIS_SCRIPT])

print("\nPipeline complete. Check performance_report.png for results.")