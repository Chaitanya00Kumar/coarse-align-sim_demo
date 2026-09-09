import cv2
import numpy as np

def add_disturbance(frame, enabled, blur_strength=5, noise_level=15, jitter_px=3):
    if not enabled:
        return frame

    # Ensure Gaussian blur kernel size is positive and odd
    ksize = int(blur_strength) * 2 + 1
    frame = cv2.GaussianBlur(frame, (ksize, ksize), 0)

    noise = np.random.normal(0, noise_level, frame.shape).astype(np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    dx, dy = np.random.randint(-jitter_px, jitter_px + 1, 2)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    frame = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))

    return frame

def apply_disturbance(frame, scenario="baseline"):
    """
    Applies targeted disturbance profiles based on the SIH test matrix scenarios.
    """
    if scenario == "baseline":
        # Clean frame with no added distortion
        return add_disturbance(frame, enabled=False)

    elif scenario == "noise":
        # Heavy sensor/gaussian noise injection with minimal blur/jitter
        return add_disturbance(frame, enabled=True, blur_strength=1, noise_level=45, jitter_px=1)

    elif scenario == "jitter":
        # High positional jitter / high frequency motion
        return add_disturbance(frame, enabled=True, blur_strength=2, noise_level=10, jitter_px=8)

    elif scenario == "occlusion":
        # Simulate block occlusion (e.g., dropping a black bounding box patch in the center)
        frame_out = frame.copy()
        h, w, _ = frame_out.shape
        # Draw a synthetic occluding square in the middle
        box_size = int(min(h, w) * 0.2)
        start_x = (w - box_size) // 2
        start_y = (h - box_size) // 2
        cv2.rectangle(frame_out, (start_x, start_y), (start_x + box_size, start_y + box_size), (0, 0, 0), -1)
        return frame_out

    elif scenario == "dynamic" or scenario == "blur":
        # Heavy atmospheric turbulence / motion blur simulation
        return add_disturbance(frame, enabled=True, blur_strength=8, noise_level=20, jitter_px=4)

    # Fallback default
    return frame