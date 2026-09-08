import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import cv2
import os
from detector import BeaconRegressor

class SyntheticBeaconDataset(Dataset):
    def __init__(self, csv_path, frames_dir):
        self.df = pd.read_csv(csv_path)
        self.frames_dir = frames_dir

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        frame_name = f"frame_{int(row['frame']):04d}.png"
        img_path = os.path.join(self.frames_dir, frame_name)
        
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            img = np.zeros((480, 640), dtype=np.uint8)
            
        img = cv2.resize(img, (128, 128))
        tensor_img = torch.tensor(img, dtype=torch.float32).unsqueeze(0) / 255.0
        
        # Normalize coordinates to [-1, 1]
        x_norm = (row['true_x'] / 640.0) * 2.0 - 1.0
        y_norm = (row['true_y'] / 480.0) * 2.0 - 1.0
        target = torch.tensor([x_norm, y_norm], dtype=torch.float32)
        
        return tensor_img, target

def train():
    os.makedirs('models', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    csv_path = 'data/ground_truth.csv'
    frames_dir = 'data/frames'
    
    if not os.path.exists(csv_path):
        print("Ground truth CSV not found. Run scene_simulator.py first.")
        return

    dataset = SyntheticBeaconDataset(csv_path, frames_dir)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

    model = BeaconRegressor()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    model.train()
    print("Training BeaconRegressor CNN...")
    for epoch in range(3):
        epoch_loss = 0
        for imgs, targets in dataloader:
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        print(f"Epoch {epoch+1}/3, Loss: {epoch_loss/len(dataloader):.4f}")

    torch.save(model.state_dict(), 'models/beacon_detector.pth')
    print("Model saved to models/beacon_detector.pth")

if __name__ == '__main__':
    train()