#ifndef CLASS_VERIN_HPP
#define CLASS_VERIN_HPP

#include <Arduino.h>
#include "driver/mcpwm.h" // for verin

class Verin{
    public:
        Verin(//mcpwm_unit_t unit,
            //mcpwm_io_signals_t signal,
            //mcpwm_timer_t timer,
            //mcpwm_generator_t opr,
            uint8_t pin_1,
            uint8_t pin_2,
            uint8_t pin_pwm);
        
        void init();
        void extend();
        void retract();
        
    private:
        void stop();

        uint8_t pin_1;
        uint8_t pin_2;
        uint8_t pin_pwm;

        // mcpwm_unit_t mcpwm_num;
        // mcpwm_timer_t timer_num;
        // mcpwm_io_signals_t signal;
        // mcpwm_generator_t opr;
};


#endif