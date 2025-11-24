#include <Arduino.h>
#include "ClassMotors.hpp"
#include "TrajectoryFollower.hpp"

// UART vers la Raspberry : ici Serial (USB)
#define SERIAL_PI   Serial
#define BAUD_PI     115200//1000000

#define EN_Motor 21

ClassMotors motors;
TrajectoryFollower follower;

// Géométrie robot (cohérente avec ClassMotors)
constexpr float WHEEL_BASE = 0.22f; // m

// Tâches
void taskControl(void* arg);
void taskSerialRx(void* arg);
void taskSerialTx(void* arg);

void setup() {
    SERIAL_PI.begin(BAUD_PI);
    delay(500);
    SERIAL_PI.println("ESP32 Trajectory + Motors ready");

    pinMode(EN_Motor, OUTPUT);
    digitalWrite(EN_Motor ,HIGH);

    motors.StartMotors();

    // Paramètres pure pursuit (à tuner)
    follower.setLookahead(0.02f);    // 25 cm
    follower.setNominalSpeed(0.25f); // 0.25 m/s

    xTaskCreatePinnedToCore(taskControl, "Control", 6000, nullptr, 3, nullptr, 1);
    xTaskCreatePinnedToCore(taskSerialRx, "SerialRx", 6000, nullptr, 2, nullptr, 1);
    xTaskCreatePinnedToCore(taskSerialTx, "SerialTx", 4000, nullptr, 1, nullptr, 1);
}

void loop() {
    vTaskDelay(pdMS_TO_TICKS(1000));
}

// Convertit (v, w) -> vitesses roue gauche/droite, puis envoie à ClassMotors
static void applyVW(float v, float w) {
    // Diff drive
    float vL = v - (WHEEL_BASE / 2.0f) * w;
    float vR = v + (WHEEL_BASE / 2.0f) * w;

    TaskParams p;
    p.vitesseGauche = vL;
    p.vitesseDroite = vR;
    motors.EnvoyerVitesse(&p);
}

// Tâche de contrôle : pure pursuit + commande moteurs
void taskControl(void* arg) {
    TickType_t lastWake = xTaskGetTickCount();
    uint32_t lastMicros = micros();

    while (true) {
        uint32_t now = micros();
        float dt = (now - lastMicros) / 1e6f;
        if (dt <= 0.0f) dt = 0.001f;
        lastMicros = now;

        // Récupère odom interne
        float x, y, th;
        motors.GetPosition(x, y, th);
        Pose2D odomPose { x, y, th };

        float v, w;
        SERIAL_PI.print("[");
        SERIAL_PI.print(odomPose.x);
        SERIAL_PI.print(", ");
        SERIAL_PI.print(odomPose.y);
        SERIAL_PI.print(", ");
        SERIAL_PI.print(odomPose.theta);
        SERIAL_PI.println("]");
        follower.computeCommand(odomPose, dt, v, w);

        applyVW(v, w);

        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(200)); // 50 Hz
    }
}

// Réception série depuis la Rasp
void taskSerialRx(void* arg) {
    String line;

    while (true) {
        while (SERIAL_PI.available()) {
            char c = SERIAL_PI.read();
            if (c == '\n') {
                line.trim();
                if (line.length() > 0) {
                    // 1) JSON trajectoire (commence normalement par '[')
                    if (line[0] == '[') {
                        if (follower.loadFromJson(line.c_str())) {
                            SERIAL_PI.println("BEZ OK");
                        } else {
                            SERIAL_PI.println("BEZ ERR");
                        }
                    }
                    // 2) Pose corrigée: "POSE x y theta" (x,y en mm)
                    else if (line.startsWith("POSE")) {
                        float x_mm, y_mm, th;
                        if (sscanf(line.c_str(), "POSE %f %f %f", &x_mm, &y_mm, &th) == 3) {
                            Pose2D p;
                            p.x = x_mm / 1000.0f;
                            p.y = y_mm / 1000.0f;
                            p.theta = th;
                            follower.setCorrectedPose(p);
                        }
                    }
                    else if (line.startsWith("SET POSE")){
                        float x_mm, y_mm, th;
                        if (sscanf(line.c_str(), "SET POSE %f %f %f", &x_mm, &y_mm, &th) == 3) {
                            SERIAL_PI.print("SET POSE ");
                            SERIAL_PI.print(x_mm);
                            SERIAL_PI.print(" ");
                            SERIAL_PI.print(y_mm);
                            SERIAL_PI.print(" ");
                            SERIAL_PI.println(th);
                            motors.ResetPosition(x_mm/ 1000.0f, y_mm/ 1000.0f, th);
                        }
                    }
                    // 3) STOP
                    else if (line.startsWith("STOP")) {
                        follower.reset();
                        motors.Stop();
                    }
                }
                line = "";
            } else if (c != '\r') {
                line += c;
            }
        }
        vTaskDelay(pdMS_TO_TICKS(2));
    }
}

// Envoi de l’odom brute à la Rasp
void taskSerialTx(void* arg) {
    TickType_t lastWake = xTaskGetTickCount();

    while (true) {
        float x, y, th;
        motors.GetPosition(x, y, th);

        // En mm pour coller à ton EKF
        float x_mm = x * 1000.0f;
        float y_mm = y * 1000.0f;

        // SERIAL_PI.printf("ODOM %.1f %.1f %.5f\n", x_mm, y_mm, th);

        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(20)); // 50 Hz
    }
}
