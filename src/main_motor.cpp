#include <Arduino.h>
#include "Servo42C.hpp"

// ========================
// CONFIG PHYSIQUE
// ========================
HardwareSerial MKS_L(1);
HardwareSerial MKS_R(2);
HardwareSerial RPI_UART(0); // UART vers Raspberry Pi

Servo42C motorL("Left",  MKS_L, 0x80);
Servo42C motorR("Right", MKS_R, 0x81);

constexpr float WHEEL_DIAMETER = 0.065; // m
constexpr float WHEEL_BASE = 0.22;      // m
constexpr int   MOTOR_RPM_MAX = 120;

struct Velocity { float v; float w; };
QueueHandle_t qVel;

// ========================
// CINÉMATIQUE
// ========================
void computeWheelSpeeds(const Velocity& vel, float& vL, float& vR) {
    vL = vel.v - (WHEEL_BASE / 2.0f) * vel.w;
    vR = vel.v + (WHEEL_BASE / 2.0f) * vel.w;
}

int velocityToRPM(float v) {
    float wheel_circ = WHEEL_DIAMETER * PI;
    return int((v / wheel_circ) * 60.0f);
}

float rpmToLinear(int rpm) {
    float wheel_circ = WHEEL_DIAMETER * PI;
    return (rpm / 60.0f) * wheel_circ;
}

// ========================
// Tâche réception RPi
// ========================
void taskRpiRx(void* arg) {
    String buffer;
    while (true) {
        while (RPI_UART.available()) {
            char c = RPI_UART.read();
            if (c == '\n') {
                float v, w;
                if (sscanf(buffer.c_str(), "%f %f", &v, &w) == 2) {
                    Velocity vel = {v, w};
                    xQueueOverwrite(qVel, &vel);
                }
                buffer = "";
            } else if (c != '\r') buffer += c;
        }
        vTaskDelay(pdMS_TO_TICKS(2));
    }
}

// ========================
// Tâche envoi moteurs
// ========================
void taskMotors(void* arg) {
    Velocity vel = {0, 0};
    for (;;) {
        if (xQueueReceive(qVel, &vel, pdMS_TO_TICKS(50))) {
            float vL, vR;
            computeWheelSpeeds(vel, vL, vR);
            int rpmL = constrain(velocityToRPM(vL), -MOTOR_RPM_MAX, MOTOR_RPM_MAX);
            int rpmR = constrain(velocityToRPM(vR), -MOTOR_RPM_MAX, MOTOR_RPM_MAX);
            motorL.setSpeedRPM(rpmL);
            motorR.setSpeedRPM(rpmR);
        }
        vTaskDelay(pdMS_TO_TICKS(10)); // 100 Hz
    }
}

// ========================
// Tâche feedback MKS
// ========================
void taskFeedback(void* arg) {
    Servo42C_Status sL{}, sR{};
    for (;;) {
        bool okL = motorL.readStatus(sL);
        bool okR = motorR.readStatus(sR);

        if (okL && okR) {
            // Convertir RPM → m/s pour odométrie
            float vL = rpmToLinear(sL.speed);
            float vR = rpmToLinear(sR.speed);
            float v = (vL + vR) / 2.0f;
            float w = (vR - vL) / WHEEL_BASE;

            // Envoi à la RPi (ex: "FEEDBACK vL vR v w\n")
            RPI_UART.printf("FB %.3f %.3f %.3f %.3f\n", vL, vR, v, w);
        }
        vTaskDelay(pdMS_TO_TICKS(20)); // 50 Hz feedback
    }
}

// ========================
// Setup
// ========================
void setup() {
    // UART Raspberry Pi
    RPI_UART.begin(1000000); // RX, TX

    // UART moteurs
    MKS_L.begin(115200, SERIAL_8N1, 16, 17);
    MKS_R.begin(115200, SERIAL_8N1, 4, 5);

    motorL.begin();
    motorR.begin();
    motorL.enable(true);
    motorR.enable(true);

    qVel = xQueueCreate(1, sizeof(Velocity));

    xTaskCreatePinnedToCore(taskRpiRx,  "RxPi",   4096, nullptr, 2, nullptr, 1);
    xTaskCreatePinnedToCore(taskMotors, "Motors", 4096, nullptr, 3, nullptr, 1);
    xTaskCreatePinnedToCore(taskFeedback, "Feedback", 4096, nullptr, 1, nullptr, 1);
}

void loop() {
    vTaskDelay(pdMS_TO_TICKS(1000));
}
