import cv2
import numpy as np

def add_disturbance(frame, enabled, blur_strength=5, noise_level=15, jitter_px=3):
    if not enabled:
        return frame

    frame = cv2.GaussianBlur(frame, (blur_strength*2+1, blur_strength*2+1), 0)

    noise = np.random.normal(0, noise_level, frame.shape).astype(np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    dx, dy = np.random.randint(-jitter_px, jitter_px + 1, 2)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    frame = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))

    return frame