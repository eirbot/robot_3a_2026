#ifndef CLASS_ACTIONNEUR_HPP
#define CLASS_ACTIONNEUR_HPP

#include "ClassServo.hpp"
#include "ClassVerin.hpp"

class Actionneur {
private:
    Verin verin1;
    Servo servo1;
    Servo servo2;

public:
    Actionneur(
        // Verin
        mcpwm_unit_t unit1, mcpwm_io_signals_t signal1,
        mcpwm_timer_t timer1, mcpwm_generator_t opr1,
        int pin1_verin1, int pin2_verin1, int pin_pwm1,

        // Servo1
        mcpwm_unit_t unit2, mcpwm_io_signals_t signal2,
        mcpwm_timer_t timer2, mcpwm_generator_t opr2,
        int pin_pwm2,

        // Servo2
        mcpwm_unit_t unit3, mcpwm_io_signals_t signal3,
        mcpwm_timer_t timer3, mcpwm_generator_t opr3,
        int pin_pwm3
    );

    void runSequence();
};

#endif