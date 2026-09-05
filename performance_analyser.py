import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("tracking_data.csv")

df["error"] = np.sqrt((df.true_x - df.est_x) ** 2 + (df.true_y - df.est_y) ** 2)

print(f"Frames: {len(df)}")
print(f"Detected: {df.detected.sum()} / {len(df)} ({100 * df.detected.mean():.1f}%)")
print(f"Mean tracking error: {df.error.mean():.2f} px")
print(f"Max tracking error:  {df.error.max():.2f} px")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Trajectory: true path vs Kalman-estimated path
ax1.plot(df.true_x, df.true_y, label="True position", color="green")
ax1.plot(df.est_x, df.est_y, label="Kalman estimate", color="orange", linestyle="--")
ax1.set_title("Target trajectory: true vs tracked")
ax1.set_xlabel("x (px)")
ax1.set_ylabel("y (px)")
ax1.legend()
ax1.invert_yaxis()  # image coordinates: y increases downward

# Error over time
ax2.plot(df.frame, df.error, color="red")
ax2.set_title("Tracking error per frame")
ax2.set_xlabel("Frame")
ax2.set_ylabel("Error (px)")

plt.tight_layout()
plt.savefig("performance_report.png", dpi=150)
plt.show()
