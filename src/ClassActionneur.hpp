#ifndef CLASS_ACTIONNEUR_HPP
#define CLASS_ACTIONNEUR_HPP


#include "ClassAscenseur.hpp"
#include "ClassServo.hpp"
#include "ClassVerin.hpp"

class Actionneur{
    public:
        Actionneur( uint8_t asc_stp,
                        uint8_t asc_dir,
                        String asc_name,
                        bool asc_inv,
                        mcpwm_unit_t unit_1,
                        mcpwm_io_signals_t signal_1,
                        mcpwm_timer_t timer_1,
                        mcpwm_generator_t opr_1,
                        uint8_t pin_1,
                        mcpwm_unit_t unit_2,
                        mcpwm_io_signals_t signal_2,
                        mcpwm_timer_t timer_2,
                        mcpwm_generator_t opr_2,
                        uint8_t pin_2,
                        mcpwm_unit_t unit_verin,
                        mcpwm_io_signals_t signal_verin,
                        mcpwm_timer_t timer_verin,
                        mcpwm_generator_t opr_verin,
                        uint8_t pin_1_verin,
                        uint8_t pin_2_verin,
                        uint8_t pin_pwm_verin
                );  

        void sequence();

    private:
        ClassAscenseur ascenseur;
        Verin pince;
        Servo flip_kapla;
        Servo orient_actionneur;

};

#endif
