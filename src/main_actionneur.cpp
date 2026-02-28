#include "ClassActionneur.hpp"

//SERVO1
#define UNIT_PWM_1 MCPWM_UNIT_0
#define TIMER_PWM_1 MCPWM_TIMER_0
#define OPR_PWM_1 MCPWM_OPR_A
#define SIGNAL_PWM_1 MCPWM0A
#define PIN_PW_1 16

//SERVO2
#define UNIT_PWM_2 MCPWM_UNIT_0
#define TIMER_PWM_2 MCPWM_TIMER_1
#define OPR_PWM_2 MCPWM_OPR_A
#define SIGNAL_PWM_2 MCPWM1A
#define PIN_PW_2 17

//VERIN
#define PIN_VERIN_1 5
#define PIN_VERIN_2 18
#define PIN_VERIN_3_PWM 19

//ASCENSEUR
#define PIN_ASC_STP 2
#define PIN_ASC_DIR 4
#define PIN_ASC_SNS 22




Actionneur actionneur(
    UNIT_PWM_1, SIGNAL_PWM_1, TIMER_PWM_1, OPR_PWM_1,
    PIN_PW_1,
    
    UNIT_PWM_2, SIGNAL_PWM_2, TIMER_PWM_2, OPR_PWM_2,
    PIN_PW_2,
    
    PIN_VERIN_1, PIN_VERIN_2, PIN_VERIN_3_PWM,

    PIN_ASC_STP, PIN_ASC_DIR, "asc", true
);
void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("init");
    actionneur.init(PIN_ASC_SNS,3,4096, 1);
    Serial.println("done");
}

void loop() {
    Serial.println("commanding");
    actionneur.receive_command("flip");
    delay(20000);
}