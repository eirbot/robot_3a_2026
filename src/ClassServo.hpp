#ifndef CLASS_SERVO_HPP
#define CLASS_SERVO_HPP

#include "driver/mcpwm.h" // for servo
#include "soc/mcpwm_periph.h"

class Servo{
    public:
        Servo(mcpwm_unit_t unit, mcpwm_io_signals_t signal, mcpwm_timer_t timer, mcpwm_generator_t opr, uint8_t pin);
        void setAngle(float angle);

    private:
        uint8_t pin;
        mcpwm_unit_t mcpwm_num;
        mcpwm_timer_t timer_num;
        mcpwm_io_signals_t signal;
        mcpwm_generator_t opr;
};


#endif