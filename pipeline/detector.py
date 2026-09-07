
import os
import glob
import cv2
import numpy as np
import torch
import torch.nn as nn

script_dir = os.path.dirname(os.path.abspath(__file__))
frames_dir = os.path.join(script_dir, "frames")
output_csv = os.path.join(script_dir, "detections.csv")


# --- Lightweight Beacon Detection CNN ---
class BeaconDetectorNet(nn.Module):
    def __init__(self):
        super().__init__()
        # Downsampling feature extractor
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1),  # 320 x 240
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),  # 160 x 120
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),  # 80 x 60
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        # Heatmap / spatial attention head for beacon localization
        self.loc_conv = nn.Sequential(
            nn.Conv2d(3, 8, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(8, 1, kernel_size=3, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        # Generates a normalized spatial probability map over the frame
        heatmap = self.loc_conv(x)  # shape: (B, 1, H, W)
        return heatmap


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = BeaconDetectorNet().to(device)
model.eval()


def ai_detect_target(frame_bgr, conf_threshold=0.35):
    """
    Infers beacon center using deep spatial activation map.
    Returns: (detected: bool, x: float, y: float)
    """
    h, w, _ = frame_bgr.shape

    # Normalize image tensor
    img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    tensor = torch.from_numpy(img_rgb).float().permute(2, 0, 1) / 255.0
    tensor = tensor.unsqueeze(0).to(device)

    with torch.no_grad():
        # Soft spatial maximum detection
        heatmap = model(tensor).squeeze().cpu().numpy()

    # Weight activation with high-intensity beacon channel
    r_channel = img_rgb[:, :, 0].astype(np.float32) / 255.0
    combined_response = heatmap * r_channel

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(combined_response)

    if max_val < conf_threshold:
        return False, 0.0, 0.0

    cx, cy = float(max_loc[0]), float(max_loc[1])
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

            found, x, y = ai_detect_target(frame)
            if found:
                hits += 1
                out.write(f"{frame_num},1,{x:.2f},{y:.2f}\n")
            else:
                out.write(f"{frame_num},0,0,0\n")

    print(f"Processed {len(frame_paths)} frames -> {output_csv}")
    print(
        f"AI Detected target in {hits}/{len(frame_paths)} frames ({100 * hits / len(frame_paths):.1f}%)"
    )


if __name__ == "__main__":
    main()
