#include <iostream>
#include <cmath>
#include <iomanip>
#include <vector>
#include <random>
#include <fstream>

// ---------- Simple 2D Kalman Filter (constant velocity model) ----------
struct KalmanFilter2D
{
    // state: [x, y, vx, vy]
    double x[4] = {0, 0, 0, 0};
    double P[4][4] = {{1, 0, 0, 0}, {0, 1, 0, 0}, {0, 0, 1000, 0}, {0, 0, 0, 1000}}; // uncertainty
    double dt;
    double processNoise;
    double measNoise;
    bool initialized = false;

    KalmanFilter2D(double dt_, double q, double r)
        : dt(dt_), processNoise(q), measNoise(r) {}

    void predict()
    {
        // x = F * x (F: constant velocity model)
        double px = x[0] + x[2] * dt;
        double py = x[1] + x[3] * dt;
        x[0] = px;
        x[1] = py;
        // P = F P F^T + Q (simplified diagonal-ish update, good enough for demo)
        for (int i = 0; i < 4; i++)
            P[i][i] += processNoise;
    }

    void correct(double zx, double zy)
    {
        if (!initialized)
        {
            x[0] = zx;
            x[1] = zy;
            x[2] = 0;
            x[3] = 0;
            initialized = true;
            return;
        }
        // Kalman gain (simplified scalar per-dimension gain)
        double Kx = P[0][0] / (P[0][0] + measNoise);
        double Ky = P[1][1] / (P[1][1] + measNoise);
        double innov_x = zx - x[0];
        double innov_y = zy - x[1];
        x[0] += Kx * innov_x;
        x[1] += Ky * innov_y;
        x[2] += (Kx * innov_x) / dt * 0.3; // velocity nudge from residual
        x[3] += (Ky * innov_y) / dt * 0.3;
        P[0][0] *= (1 - Kx);
        P[1][1] *= (1 - Ky);
    }

    double getX() const { return x[0]; }
    double getY() const { return x[1]; }
};

// ---------- Simple PID controller ----------
struct PID
{
    double kp, ki, kd;
    double integral = 0;
    double prevError = 0;

    PID(double kp_, double ki_, double kd_) : kp(kp_), ki(ki_), kd(kd_) {}

    double update(double error, double dt)
    {
        integral += error * dt;
        double derivative = (error - prevError) / dt;
        prevError = error;
        return kp * error + ki * integral + kd * derivative;
    }
};

// ---------- Simulated servo (pan-tilt mount) ----------
struct Servo
{
    double angle = 90.0; // degrees, centered
    double minAngle = 0.0;
    double maxAngle = 180.0;

    void moveBy(double delta)
    {
        angle += delta;
        if (angle < minAngle)
            angle = minAngle;
        if (angle > maxAngle)
            angle = maxAngle;
    }
};

int main()
{
    const double dt = 1.0 / 30.0; // simulate 30 FPS
    const int frameWidth = 640, frameHeight = 480;
    const int centerX = frameWidth / 2, centerY = frameHeight / 2;

    KalmanFilter2D kf(dt, /*processNoise=*/4.0, /*measNoise=*/25.0);
    PID panPID(0.06, 0.0, 0.015);
    PID tiltPID(0.06, 0.0, 0.015);
    Servo panServo, tiltServo;

    // Simulate a target moving in a circular path across the frame,
    // with noisy detections (like a real camera detector would produce)
    std::default_random_engine rng(42);
    std::normal_distribution<double> noise(0.0, 6.0); // detection noise, px

    std::cout << std::fixed << std::setprecision(1);
    std::cout << "Frame | TrueTarget(x,y) | Detected(x,y) | KalmanEst(x,y) | Pan | Tilt\n";
    std::cout << "---------------------------------------------------------------------------\n";

    // --- NEW: CSV output for the performance-graphing script ---
    std::ofstream csv("tracking_data.csv");
    csv << "frame,true_x,true_y,detected,det_x,det_y,est_x,est_y,pan,tilt\n";

    for (int frame = 0; frame < 90; frame++)
    {
        double t = frame * dt;

        // --- simulate true target position: circular motion ---
        double trueX = centerX + 150 * std::sin(t * 1.5);
        double trueY = centerY + 100 * std::cos(t * 1.5);

        // --- simulate a noisy "detector" (like color/YOLO detection) ---
        bool detected = true;
        if (frame % 15 == 7)
            detected = false; // simulate occasional missed detection

        double detX = trueX + noise(rng);
        double detY = trueY + noise(rng);

        // --- Kalman predict step (always runs) ---
        kf.predict();

        // --- Kalman correct step (only if detection available) ---
        if (detected)
        {
            kf.correct(detX, detY);
        }

        double estX = kf.getX();
        double estY = kf.getY();

        // --- pan-tilt control: drive error (estimated pos - frame center) to zero ---
        double errorX = estX - centerX;
        double errorY = estY - centerY;
        double panAdjust = panPID.update(errorX, dt);
        double tiltAdjust = tiltPID.update(errorY, dt);
        panServo.moveBy(-panAdjust * dt); // negative: move opposite to error to recenter
        tiltServo.moveBy(tiltAdjust * dt);

        // --- print this frame's data ---
        std::cout << std::setw(5) << frame << " | "
                  << "(" << std::setw(5) << trueX << "," << std::setw(5) << trueY << ") | "
                  << (detected ? "(" : " MISSED ")
                  << (detected ? (std::to_string((int)detX) + "," + std::to_string((int)detY) + ")") : "")
                  << " | (" << std::setw(5) << estX << "," << std::setw(5) << estY << ") | "
                  << std::setw(5) << panServo.angle << "|" << std::setw(5) << tiltServo.angle
                  << "\n";

        // --- NEW: write this frame's data to the CSV too ---
        csv << frame << "," << trueX << "," << trueY << ","
            << (detected ? 1 : 0) << ","
            << (detected ? detX : 0) << "," << (detected ? detY : 0) << ","
            << estX << "," << estY << ","
            << panServo.angle << "," << tiltServo.angle << "\n";
    }

    csv.close(); // --- NEW: finish writing the CSV ---

    std::cout << "\nDemo complete. Kalman filter smoothed noisy detections,\n";
    std::cout << "predicted through the missed-detection frame, and pan/tilt\n";
    std::cout << "servo angles tracked the target toward frame center.\n";

    return 0;
}
