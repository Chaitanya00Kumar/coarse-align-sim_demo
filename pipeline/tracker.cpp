#include <iostream>
#include <cmath>
#include <iomanip>
#include <vector>
#include <fstream>
#include <sstream>
#include <string>
#include <unordered_map>

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

// ---------- Minimal CSV loading ----------
struct GroundTruthRow { double x, y; };
struct DetectionRow { bool detected; double x, y; };

static std::vector<std::string> splitCsv(const std::string &line)
{
    std::vector<std::string> fields;
    std::stringstream ss(line);
    std::string field;
    while (std::getline(ss, field, ','))
        fields.push_back(field);
    return fields;
}

static std::unordered_map<int, GroundTruthRow> loadGroundTruth(const std::string &path)
{
    std::unordered_map<int, GroundTruthRow> rows;
    std::ifstream file(path);
    if (!file.is_open())
    {
        std::cerr << "ERROR: could not open " << path
                  << " — run scene_simulator.py first.\n";
        std::exit(1);
    }
    std::string line;
    std::getline(file, line); // header
    while (std::getline(file, line))
    {
        if (line.empty())
            continue;
        auto f = splitCsv(line);
        int frame = std::stoi(f[0]);
        rows[frame] = {std::stod(f[1]), std::stod(f[2])};
    }
    return rows;
}

static std::unordered_map<int, DetectionRow> loadDetections(const std::string &path)
{
    std::unordered_map<int, DetectionRow> rows;
    std::ifstream file(path);
    if (!file.is_open())
    {
        std::cerr << "ERROR: could not open " << path
                  << " — run detector.py first.\n";
        std::exit(1);
    }
    std::string line;
    std::getline(file, line); // header
    while (std::getline(file, line))
    {
        if (line.empty())
            continue;
        auto f = splitCsv(line);
        int frame = std::stoi(f[0]);
        bool detected = std::stoi(f[1]) != 0;
        rows[frame] = {detected, std::stod(f[2]), std::stod(f[3])};
    }
    return rows;
}

int main()
{
    const double dt = 1.0 / 60.0; // matches scene_simulator.py's clock.tick(60)
    const int frameWidth = 640, frameHeight = 480; // matches scene_simulator.py SIM_WIDTH/HEIGHT
    const int centerX = frameWidth / 2, centerY = frameHeight / 2;

    auto groundTruth = loadGroundTruth("ground_truth.csv");
    auto detections = loadDetections("detections.csv");

    if (groundTruth.empty())
    {
        std::cerr << "ERROR: ground_truth.csv has no rows.\n";
        return 1;
    }

    int firstFrame = groundTruth.begin()->first, lastFrame = groundTruth.begin()->first;
    for (const auto &kv : groundTruth)
    {
        firstFrame = std::min(firstFrame, kv.first);
        lastFrame = std::max(lastFrame, kv.first);
    }

    KalmanFilter2D kf(dt, /*processNoise=*/4.0, /*measNoise=*/25.0);
    PID panPID(0.06, 0.0, 0.015);
    PID tiltPID(0.06, 0.0, 0.015);
    Servo panServo, tiltServo;

    std::cout << std::fixed << std::setprecision(1);
    std::cout << "Frame | TrueTarget(x,y) | Detected(x,y) | KalmanEst(x,y) | Pan | Tilt\n";
    std::cout << "---------------------------------------------------------------------------\n";

    std::ofstream csv("tracking_data.csv");
    csv << "frame,true_x,true_y,detected,det_x,det_y,est_x,est_y,pan,tilt\n";

    int missingDetectionRows = 0;

    for (int frame = firstFrame; frame <= lastFrame; frame++)
    {
        const auto gtIt = groundTruth.find(frame);
        if (gtIt == groundTruth.end())
            continue; // shouldn't happen, but skip gracefully
        double trueX = gtIt->second.x;
        double trueY = gtIt->second.y;

        bool detected = false;
        double detX = 0, detY = 0;
        const auto detIt = detections.find(frame);
        if (detIt != detections.end())
        {
            detected = detIt->second.detected;
            detX = detIt->second.x;
            detY = detIt->second.y;
        }
        else
        {
            missingDetectionRows++; // detections.csv didn't cover this frame at all
        }

        // --- Kalman predict step (always runs) ---
        kf.predict();

        // --- Kalman correct step (only if detection available) ---
        if (detected)
            kf.correct(detX, detY);

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

        csv << frame << "," << trueX << "," << trueY << ","
            << (detected ? 1 : 0) << ","
            << (detected ? detX : 0) << "," << (detected ? detY : 0) << ","
            << estX << "," << estY << ","
            << panServo.angle << "," << tiltServo.angle << "\n";
    }

    csv.close();

    std::cout << "\nDemo complete. Kalman filter smoothed noisy detections,\n";
    std::cout << "predicted through missed-detection frames, and pan/tilt\n";
    std::cout << "servo angles tracked the target toward frame center.\n";
    if (missingDetectionRows > 0)
        std::cout << missingDetectionRows << " frame(s) had no row at all in detections.csv "
                     "(treated as missed detections).\n";

    return 0;
}
