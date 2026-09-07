import os
import glob
import cv2
import numpy as np

script_dir = os.path.dirname(os.path.abspath(__file__))
frames_dir = os.path.join(script_dir, "frames")
output_csv = os.path.join(script_dir, "detections.csv")

# Target is drawn as pure red (255, 0, 0) in RGB / (0, 0, 255) in BGR,
# but blur/noise smear it, so threshold with tolerance in HSV space.
LOWER_RED_1 = np.array([0, 100, 100])
UPPER_RED_1 = np.array([10, 255, 255])
LOWER_RED_2 = np.array([170, 100, 100])
UPPER_RED_2 = np.array([180, 255, 255])
MIN_BLOB_AREA = 3  # px^2 — ignore stray noise pixels


def detect_target(frame_bgr):
    """Return (found, x, y) — centroid of the largest red blob, if any."""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_RED_1, UPPER_RED_1) | cv2.inRange(hsv, LOWER_RED_2, UPPER_RED_2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False, 0.0, 0.0

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_BLOB_AREA:
        return False, 0.0, 0.0

    M = cv2.moments(largest)
    if M["m00"] == 0:
        return False, 0.0, 0.0

    cx = M["m10"] / M["m00"]
    cy = M["m01"] / M["m00"]
    return True, cx, cy


def main():
    frame_paths = sorted(glob.glob(os.path.join(frames_dir, "frame_*.png")))
    if not frame_paths:
        raise SystemExit(
            f"No frames found in {frames_dir} — run scene_simulator.py first."
        )

    hits = 0
    with open(output_csv, "w") as out:
        out.write("frame,detected,det_x,det_y\n")
        for path in frame_paths:
            frame_num = int(os.path.splitext(os.path.basename(path))[0].split("_")[1])
            frame = cv2.imread(path)
            if frame is None:
                out.write(f"{frame_num},0,0,0\n")
                continue

            found, x, y = detect_target(frame)
            if found:
                hits += 1
                out.write(f"{frame_num},1,{x:.2f},{y:.2f}\n")
            else:
                out.write(f"{frame_num},0,0,0\n")

    print(f"Processed {len(frame_paths)} frames -> {output_csv}")
    print(f"Detected target in {hits}/{len(frame_paths)} frames ({100 * hits / len(frame_paths):.1f}%)")


if __name__ == "__main__":
    main()