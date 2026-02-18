#include <Arduino.h>
#include "utilities.hpp"

// ===== PINS =====
#define STEP_PIN_1 15
#define DIR_PIN_1  2

#define STEP_PIN_2 4
#define DIR_PIN_2 16

#define STEP_PIN_4 18
#define DIR_PIN_4 19

// ===== MOTOR CONFIG =====
// Change according to your motor & microstepping
#define STEPS_PER_REV 1600   // 200 = 1.8° stepper (full step)
#define MM_PER_REV 8.0f      // depends on your lead screw pitch and microstepping

TMC2100 stepper_1(STEPS_PER_REV, STEP_PIN_1, DIR_PIN_1);
TMC2100 stepper_2(STEPS_PER_REV, STEP_PIN_2, DIR_PIN_2);
TMC2100 stepper_4(STEPS_PER_REV, STEP_PIN_4, DIR_PIN_4);

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("=== 2 Turns CW / CCW Test ===");

    stepper_1.setRPM(2000);     // steps/sec
    stepper_1.setSpeedProfile(stepper_1.LINEAR_SPEED,
        (ACCEL_MM_S2 / MM_PER_REV) * STEP_PER_REV, 
        (ACCEL_MM_S2 / MM_PER_REV) * STEP_PER_REV
    );
    stepper_2.setRPM(2000);     // steps/sec
    stepper_2.setSpeedProfile(stepper_2.LINEAR_SPEED,
        (ACCEL_MM_S2 / MM_PER_REV) * STEP_PER_REV, 
        (ACCEL_MM_S2 / MM_PER_REV) * STEP_PER_REV
    );
    stepper_4.setRPM(2000);     // steps/sec
    stepper_4.setSpeedProfile(stepper_4.LINEAR_SPEED,
        (ACCEL_MM_S2 / MM_PER_REV) * STEP_PER_REV, 
        (ACCEL_MM_S2 / MM_PER_REV) * STEP_PER_REV
    );
}

void loop() {

    // ---- 2 turns clockwise ----
    Serial.println("2 turns CW for each motor");
    stepper_1.move(2*STEPS_PER_REV);
    stepper_2.move(2*STEPS_PER_REV);
    stepper_4.move(2*STEPS_PER_REV);
    while (stepper_1.getStepsRemaining() != 0 || stepper_2.getStepsRemaining() != 0 || stepper_4.getStepsRemaining() != 0) {
        stepper_1.nextAction();
        stepper_2.nextAction();
        stepper_4.nextAction();
    }


    delay(1000);

    // ---- 2 turns counter-clockwise ----
    Serial.println("2 turns CCW for each motor");
    stepper_1.move(-2*STEPS_PER_REV);
    stepper_2.move(-2*STEPS_PER_REV);
    stepper_4.move(-2*STEPS_PER_REV);
    while (stepper_1.getStepsRemaining() != 0 || stepper_2.getStepsRemaining() != 0 || stepper_4.getStepsRemaining() != 0) {
        stepper_1.nextAction();
        stepper_2.nextAction();
        stepper_4.nextAction();
    }

    delay(1000);
}
