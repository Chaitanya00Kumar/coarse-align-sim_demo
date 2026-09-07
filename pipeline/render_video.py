import os
import cv2
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
frames_dir = os.path.join(script_dir, "frames")
tracking_csv = os.path.join(script_dir, "tracking_data.csv")
output_video = os.path.join(script_dir, "tracking_demo.mp4")

df = pd.read_csv(tracking_csv).set_index("frame")

frame_sample = cv2.imread(os.path.join(frames_dir, "frame_0001.png"))
h, w, _ = frame_sample.shape

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(output_video, fourcc, 30.0, (w, h))

for frame_num in sorted(df.index):
    path = os.path.join(frames_dir, f"frame_{frame_num:04d}.png")
    frame = cv2.imread(path)
    if frame is None:
        continue

    row = df.loc[frame_num]

    # Center crosshairs (optical axis)
    cv2.drawMarker(frame, (w // 2, h // 2), (80, 80, 80), cv2.MARKER_CROSS, 20, 1)

    # Kalman Filter Estimate (Blue Target Box)
    est_x, est_y = int(row.est_x), int(row.est_y)
    cv2.circle(frame, (est_x, est_y), 12, (255, 180, 0), 2)
    cv2.putText(frame, "Kalman Track", (est_x + 15, est_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 180, 0), 1)

    # Raw Detection (Red dot, if found)
    if row.detected:
        det_x, det_y = int(row.det_x), int(row.det_y)
        cv2.circle(frame, (det_x, det_y), 4, (0, 0, 255), -1)
    else:
        cv2.putText(frame, "DETECTION LOST - PREDICTING", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Gimbal / Pan-Tilt Telemetry HUD
    cv2.putText(frame, f"Frame: {frame_num} | Pan: {row.pan:.1f} deg | Tilt: {row.tilt:.1f} deg",
                (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    writer.write(frame)

writer.release()
print(f"Tracking video rendered: {output_video}")
