import subprocess, sys, platform, os

# --- these must match your actual filenames exactly ---
SCENE_SCRIPT = "scene_simulator.py"
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

# 2. Compile the tracker
compile_cmd = ["g++", TRACKER_SOURCE, "-o", "tracker.exe" if IS_WINDOWS else "tracker"]
run_step("Compiling tracker", compile_cmd)

# 3. Run the tracker — produces tracking_data.csv
run_step("Running tracker", [TRACKER_BINARY])

# 4. Performance analysis — produces performance_report.png
run_step("Performance analysis", [sys.executable, ANALYSIS_SCRIPT])

print("\nPipeline complete. Check performance_report.png for results.")