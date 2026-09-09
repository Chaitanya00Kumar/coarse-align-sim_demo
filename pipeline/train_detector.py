import torch
import torch.nn as nn
from pathlib import Path

# Base directory setup using pathlib
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "simulated_frames"
MODEL_SAVE_PATH = BASE_DIR / "models" / "detector_weights.pth"

class FSOCDetectorCNN(nn.Module):
    def __init__(self):
        super(FSOCDetectorCNN, self).__init__()
        # Aligned with standard detector.py specifications
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(16 * 112 * 112, 2) 

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        return x

def train():
    MODEL_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"[TRAIN] Target output model path secured at: {MODEL_SAVE_PATH}")
    
    model = FSOCDetectorCNN()
    print("[TRAIN] PyTorch detector architecture initialized successfully.")

if __name__ == "__main__":
    train()