#include "ClassVerin.hpp"

Verin::Verin(
    uint8_t pin_1,
    uint8_t pin_2,
    uint8_t pin_pwm){

    this->pin_1 = pin_1;
    this->pin_2 = pin_2;
    this->pin_pwm = pin_pwm;

    pinMode(pin_1, OUTPUT);
    pinMode(pin_2, OUTPUT);
    pinMode(pin_pwm, OUTPUT);
}

void Verin::extend(){
    digitalWrite(pin_1, HIGH);
    digitalWrite(pin_2, LOW);

    digitalWrite(pin_pwm, HIGH);
}

void Verin::init(){
    retract();
}

void Verin::retract(){
    digitalWrite(pin_1, LOW);
    digitalWrite(pin_2, HIGH);
    digitalWrite(pin_pwm, HIGH);
}

void Verin::stop(){
    digitalWrite(pin_1, LOW);
    digitalWrite(pin_2, LOW);
    digitalWrite(pin_pwm, LOW);
}