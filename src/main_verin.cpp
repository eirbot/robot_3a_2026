#include "ClassVerin.hpp"

Verin verin1(5, 18, 19);

void setup(){
    Serial.begin(115200);
    delay(1000); // Wait for serial to initialize
    Serial.println("Verin Test Starting...");

}

void loop(){
    verin1.extend();
    delay(4000);
    verin1.retract();
    delay(4000);
}