#include "ClassServo.hpp"
#include <Arduino.h>



Servo servo1(MCPWM_UNIT_0, MCPWM0A, MCPWM_TIMER_0, MCPWM_OPR_A, 18);
Servo servo2(MCPWM_UNIT_0, MCPWM0B, MCPWM_TIMER_0, MCPWM_OPR_B, 19);
void setup() {
    Serial.begin(115200);
    delay(1000); // Wait for serial to initialize
    Serial.println("Servo Test Starting...");
}

void loop(){
    servo1.setAngle(0);
    servo2.setAngle(90);
    delay(1000);
    servo1.setAngle(180);
    servo2.setAngle(0);
    delay(1000);

}