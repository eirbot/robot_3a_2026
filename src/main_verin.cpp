#include "ClassVerin.hpp"

Verin verin1(MCPWM_UNIT_0, MCPWM0A, MCPWM_TIMER_0, MCPWM_OPR_A, 14, 12, 13);

void setup(){
    Serial.begin(115200);
    delay(1000); // Wait for serial to initialize
    Serial.println("Verin Test Starting...");

}

void loop(){
    verin1.extend();
    delay(4000);
    // verin1.retract();
    // delay(4000);
}