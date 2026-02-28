#include <Arduino.h>
#include "utilities.hpp"

// ===== PINS =====
#define STEP_PIN_1 26
#define DIR_PIN_1  27

// #define STEP_PIN_2 4
// #define DIR_PIN_2 16

// #define STEP_PIN_4 18
// #define DIR_PIN_4 19


TMC2100 stepper_1(STEPS_PER_REV, DIR_PIN_1 , STEP_PIN_1);
// TMC2100 stepper_2(STEPS_PER_REV, DIR_PIN_2 , STEP_PIN_2);
// TMC2100 stepper_4(STEPS_PER_REV, DIR_PIN_4 , STEP_PIN_4);
// 
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("=== 2 Turns CW / CCW Test ===");

    stepper_1.setRPM(2000);     // steps/sec
    stepper_1.setSpeedProfile(stepper_1.LINEAR_SPEED,
        8000, 
        8000
    );
    // stepper_2.setRPM(2000);     // steps/sec
    // stepper_2.setSpeedProfile(stepper_2.LINEAR_SPEED,
        // 8000, 
        // 8000
    // );
    // stepper_4.setRPM(2000);     // steps/sec
    // stepper_4.setSpeedProfile(stepper_4.LINEAR_SPEED,
        // 8000, 
        // 8000
    // );
    Serial.println("1 turn CW");
    // stepper_4.rotate(2*360);
}

void loop() {
    stepper_1.move(2*360);
    delay(1000);
    stepper_1.move(-2*360);

}
