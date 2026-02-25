#include "ClassVerin.hpp"

Verin::Verin(mcpwm_unit_t unit, 
    mcpwm_io_signals_t signal,
    mcpwm_timer_t timer,
    mcpwm_generator_t opr,
    uint8_t pin_1,
    uint8_t pin_2,
    uint8_t pin_pwm){
    
    this->mcpwm_num = unit;
    this->timer_num = timer;
    this->signal = signal;
    this -> opr = opr;

    this->pin_1 = pin_1;
    this->pin_2 = pin_2;
    this->pin_pwm = pin_pwm;

    mcpwm_gpio_init(unit, signal, pin_pwm);
    mcpwm_config_t pwm_config;
    pwm_config.frequency = 5000;        // 5 kHz
    pwm_config.cmpr_a = 0;            // duty (we’ll set later)
    pwm_config.cmpr_b = 0;
    pwm_config.counter_mode = MCPWM_UP_COUNTER;
    pwm_config.duty_mode = MCPWM_DUTY_MODE_0;
    mcpwm_init(unit, timer, &pwm_config);

    pinMode(pin_1, OUTPUT);
    pinMode(pin_2, OUTPUT);
}

void Verin::extend(){
    digitalWrite(pin_1, HIGH);
    digitalWrite(pin_2, LOW);
    mcpwm_set_duty(mcpwm_num, timer_num, opr, 100);
    mcpwm_set_duty_type(mcpwm_num, timer_num, opr, MCPWM_DUTY_MODE_0);
}

void Verin::init(){
    retract();
}

void Verin::retract(){
    digitalWrite(pin_1, LOW);
    digitalWrite(pin_2, HIGH);
    mcpwm_set_duty(mcpwm_num, timer_num, opr, 100);
    mcpwm_set_duty_type(mcpwm_num, timer_num, opr, MCPWM_DUTY_MODE_0);
}

void Verin::stop(){
    digitalWrite(pin_1, LOW);
    digitalWrite(pin_2, LOW);
    mcpwm_set_duty(mcpwm_num, timer_num, opr, 0);
    mcpwm_set_duty_type(mcpwm_num, timer_num, opr, MCPWM_DUTY_MODE_0);
}