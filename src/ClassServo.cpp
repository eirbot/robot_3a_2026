#include "ClassServo.hpp"

Servo::Servo(mcpwm_unit_t unit, mcpwm_io_signals_t signal, mcpwm_timer_t timer, mcpwm_generator_t opr, uint8_t pin){

    this->pin = pin;
    this->mcpwm_num = unit;
    this->timer_num = timer;
    this->signal = signal;
    this -> opr = opr;
    mcpwm_gpio_init(unit, signal, pin);
    mcpwm_config_t pwm_config;
    pwm_config.frequency = 50;        // 50 Hz
    pwm_config.cmpr_a = 0;            // duty (we’ll set later)
    pwm_config.cmpr_b = 0;
    pwm_config.counter_mode = MCPWM_UP_COUNTER;
    pwm_config.duty_mode = MCPWM_DUTY_MODE_0;

    mcpwm_init(unit, timer, &pwm_config);
}

void Servo::init(){
    setAngle(0);
}

void Servo::setAngle(float angle) {
    // Clamp
    if (angle < MIN_ANGLE) angle = MIN_ANGLE;
    if (angle > MAX_ANGLE) angle = MAX_ANGLE;

    // Convert angle to pulse width (µs)
    float pulse_width = 500 + (angle / 180.0f) * 2000; // 500–2500 µs

    mcpwm_set_duty_in_us(
        mcpwm_num,
        timer_num,
        opr, //  opr must match 
        pulse_width
    );
}