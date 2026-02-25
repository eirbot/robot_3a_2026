#include "ClassActionneur.hpp"

//VERIN
#define UNIT_PWM_1 MCPWM_UNIT_0
#define TIMER_PWM_1 MCPWM_TIMER_0
#define OPR_PWM_1 MCPWM_OPR_A
#define SIGNAL_PWM_1 MCPWM0A
#define PIN_PW_1 13

#define PIN_VERIN_1 14
#define PIN_VERIN_2 12
//SERVO1
#define UNIT_PWM_2 MCPWM_UNIT_0
#define TIMER_PWM_2 MCPWM_TIMER_1
#define OPR_PWM_2 MCPWM_OPR_A
#define SIGNAL_PWM_2 MCPWM1A
#define PIN_PW_2 18
//SERVO2
#define UNIT_PWM_3 MCPWM_UNIT_0
#define TIMER_PWM_3 MCPWM_TIMER_2
#define OPR_PWM_3 MCPWM_OPR_A
#define SIGNAL_PWM_3 MCPWM2A
#define PIN_PW_3 19



Actionneur actionneur(
    UNIT_PWM_1, SIGNAL_PWM_1, TIMER_PWM_1, OPR_PWM_1,
    PIN_VERIN_1, PIN_VERIN_2, PIN_PW_1,
    
    UNIT_PWM_2, SIGNAL_PWM_2, TIMER_PWM_2, OPR_PWM_2,
    PIN_PW_2,
    
    UNIT_PWM_3, SIGNAL_PWM_3, TIMER_PWM_3, OPR_PWM_3,
    PIN_PW_3
);

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("Servo Test Starting...");
}

void loop() {
    actionneur.runSequence();
}
    // Verin verin1(UNIT_PWM_1, SIGNAL_PWM_1, TIMER_PWM_1, OPR_PWM_1, PIN_VERIN_1, PIN_VERIN_2, PIN_PW_1);
    // Servo servo1(UNIT_PWM_2, SIGNAL_PWM_2, TIMER_PWM_2, OPR_PWM_2, PIN_PW_2);
    // Servo servo2(UNIT_PWM_3, SIGNAL_PWM_3, TIMER_PWM_3, OPR_PWM_3, PIN_PW_3);
    
    // void setup() {
    //     Serial.begin(115200);
    //     delay(1000); // Wait for serial to initialize
    //     Serial.println("Servo Test Starting...");
    // }
    
    // void loop(){
    //     verin1.retract();
    //     servo1.setAngle(0);
    //     servo2.setAngle(0);
    //     delay(4000);
    //     verin1.extend();
    //     delay(4000);
    //     verin1.retract();
    //     delay(4000);
    //     servo1.setAngle(180);
    //     servo2.setAngle(180);
    //     delay(4000);
    //     verin1.extend();
    //     delay(4000);
    // }
