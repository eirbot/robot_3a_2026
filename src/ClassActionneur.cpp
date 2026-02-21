#include "ClassActionneur.hpp"

Actionneur::Actionneur( uint8_t asc_stp,
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
                        uint8_t pin_pwm_verin) :
    ascenseur(asc_stp, asc_dir, asc_name, asc_inv),
    pince(unit_verin, signal_verin, timer_verin, opr_verin, pin_1_verin, pin_2_verin, pin_pwm_verin),
    flip_kapla(unit_1, signal_1, timer_1, opr_1, pin_1),
    orient_actionneur(unit_2, signal_2, timer_2, opr_2, pin_2) {
}

