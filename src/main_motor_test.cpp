#include <Arduino.h>
#include <AccelStepper.h>

// ===== PINS =====
#define STEP_PIN 16
#define DIR_PIN  17

// ===== MOTOR CONFIG =====
// Change according to your motor & microstepping
#define STEPS_PER_REV 8*200   // 200 = 1.8° stepper (full step)

AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("=== 5 Turns CW / CCW Test ===");

    stepper.setMaxSpeed(2000);     // steps/sec
    stepper.setAcceleration(800);  // steps/sec^2
}

void loop() {

    // ---- 5 turns clockwise ----
    Serial.println("5 turns CW");
    stepper.move(5*STEPS_PER_REV);
    while (stepper.distanceToGo() != 0) {
        stepper.run();
    }


    delay(1000);

    // ---- 5 turns counter-clockwise ----
    Serial.println("5 turns CCW");
    stepper.move(-5*STEPS_PER_REV);
    while (stepper.distanceToGo() != 0) {
        stepper.run();
    }

    delay(1000);
}
