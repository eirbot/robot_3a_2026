#include "ClassServo.hpp"
#include <Arduino.h>

#define UNIT_PWM_1 MCPWM_UNIT_0
#define TIMER_PWM_1 MCPWM_TIMER_0
#define OPR_PWM_1 MCPWM_OPR_A
#define SIGNAL_PWM_1 MCPWM0A
#define PIN_PW_1 16

#define UNIT_PWM_2 MCPWM_UNIT_0
#define TIMER_PWM_2 MCPWM_TIMER_1
#define OPR_PWM_2 MCPWM_OPR_A
#define SIGNAL_PWM_2 MCPWM1A
#define PIN_PW_2 17

Servo SERVO_ORIENT(UNIT_PWM_1, SIGNAL_PWM_1, TIMER_PWM_1, OPR_PWM_1, PIN_PW_1); // !!!!!!!!!!!! small amplitude
Servo SERVO_FLIP(UNIT_PWM_2, SIGNAL_PWM_2, TIMER_PWM_2, OPR_PWM_2, PIN_PW_2);
void setup() {
    Serial.begin(115200);
    delay(1000); // Wait for serial to initialize
    Serial.println("Servo Test Starting...");
}

void loop(){
    SERVO_ORIENT.setAngle(0);
    SERVO_FLIP.setAngle(0);
    delay(1000);
    SERVO_ORIENT.setAngle(90);
    SERVO_FLIP.setAngle(0);
    delay(1000);

}