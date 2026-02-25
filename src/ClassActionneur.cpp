#include "ClassActionneur.hpp"

Actionneur::Actionneur(
    mcpwm_unit_t unit1, mcpwm_io_signals_t signal1,
    mcpwm_timer_t timer1, mcpwm_generator_t opr1,
    int pin1_verin1, int pin2_verin1, int pin_pwm1,

    mcpwm_unit_t unit2, mcpwm_io_signals_t signal2,
    mcpwm_timer_t timer2, mcpwm_generator_t opr2,
    int pin_pwm2,

    mcpwm_unit_t unit3, mcpwm_io_signals_t signal3,
    mcpwm_timer_t timer3, mcpwm_generator_t opr3,
    int pin_pwm3
)
: verin1(unit1, signal1, timer1, opr1, pin1_verin1, pin2_verin1, pin_pwm1),
  servo1(unit2, signal2, timer2, opr2, pin_pwm2),
  servo2(unit3, signal3, timer3, opr3, pin_pwm3)
{}

void Actionneur::runSequence() {
    verin1.retract();
    servo1.setAngle(0);
    servo2.setAngle(0);
    delay(4000);

    verin1.extend();
    delay(4000);

    verin1.retract();
    delay(4000);

    servo1.setAngle(180);
    servo2.setAngle(180);
    delay(4000);

    verin1.extend();
    delay(4000);
}