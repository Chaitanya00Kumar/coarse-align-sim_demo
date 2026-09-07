import csv

class KalmanFilter2D:
    def __init__(self, dt, q, r):
        self.dt = dt
        self.process_noise = q
        self.meas_noise = r
        self.x = [0.0, 0.0, 0.0, 0.0]
        self.P = [1.0, 1.0, 1000.0, 1000.0]
        self.initialized = False

    def predict(self):
        self.x[0] += self.x[2] * self.dt
        self.x[1] += self.x[3] * self.dt
        for i in range(4):
            self.P[i] += self.process_noise

    def correct(self, zx, zy):
        if not self.initialized:
            self.x[0] = zx
            self.x[1] = zy
            self.initialized = True
            return
        kx = self.P[0] / (self.P[0] + self.meas_noise)
        ky = self.P[1] / (self.P[1] + self.meas_noise)
        ix = zx - self.x[0]
        iy = zy - self.x[1]
        self.x[0] += kx * ix
        self.x[1] += ky * iy
        self.x[2] += (kx * ix) / self.dt * 0.3
        self.x[3] += (ky * iy) / self.dt * 0.3
        self.P[0] *= (1.0 - kx)
        self.P[1] *= (1.0 - ky)

class PID:
    def __init__(self, kp, ki, kd):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.integral = 0.0
        self.prev_error = 0.0

    def update(self, error, dt):
        self.integral += error * dt
        deriv = (error - self.prev_error) / dt
        self.prev_error = error
        return self.kp * error + self.ki * self.integral + self.kd * deriv

class Servo:
    def __init__(self):
        self.angle = 90.0

    def move_by(self, delta):
        self.angle = max(0.0, min(180.0, self.angle + delta))

def main():
    dt = 1.0 / 60.0
    cx, cy = 320.0, 240.0

    with open("ground_truth.csv") as f:
        gt = {int(r["frame"]): (float(r["true_x"]), float(r["true_y"])) for r in csv.DictReader(f)}

    with open("detections.csv") as f:
        det = {int(r["frame"]): (int(r["detected"]) != 0, float(r["det_x"]), float(r["det_y"])) for r in csv.DictReader(f)}

    kf = KalmanFilter2D(dt, 4.0, 25.0)
    pan_pid = PID(0.06, 0.0, 0.015)
    tilt_pid = PID(0.06, 0.0, 0.015)
    pan_servo, tilt_servo = Servo(), Servo()

    print("Frame | TrueTarget(x,y) | Detected(x,y) | KalmanEst(x,y) | Pan | Tilt")
    print("-" * 75)

    with open("tracking_data.csv", "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["frame", "true_x", "true_y", "detected", "det_x", "det_y", "est_x", "est_y", "pan", "tilt"])

        for frame in range(min(gt.keys()), max(gt.keys()) + 1):
            if frame not in gt:
                continue
            tx, ty = gt[frame]
            detected, dx, dy = det.get(frame, (False, 0.0, 0.0))

            kf.predict()
            if detected:
                kf.correct(dx, dy)

            est_x, est_y = kf.x[0], kf.x[1]
            pan_adjust = pan_pid.update(est_x - cx, dt)
            tilt_adjust = tilt_pid.update(est_y - cy, dt)

            pan_servo.move_by(-pan_adjust * dt)
            tilt_servo.move_by(tilt_adjust * dt)

            det_str = f"({int(dx)},{int(dy)})" if detected else " MISSED "
            print(f"{frame:5d} | ({tx:5.1f},{ty:5.1f}) | {det_str:>13} | ({est_x:5.1f},{est_y:5.1f}) | {pan_servo.angle:5.1f}|{tilt_servo.angle:5.1f}")

            writer.writerow([frame, tx, ty, int(detected), dx, dy, est_x, est_y, pan_servo.angle, tilt_servo.angle])

    print("\nDemo complete. Kalman filter smoothed noisy detections,")
    print("predicted through missed-detection frames, and pan/tilt")
    print("servo angles tracked the target toward frame center.")

if __name__ == "__main__":
    main()