#include "ClassMotor.hpp"

#define RPM_MOTOR 10
#define ACCEL_MOTOR 10

ClassMotor::ClassMotor(uint8_t stepPin, uint8_t dirPin, BasicStepperDriver& motor):
_motor(motor),_stpPin(stepPin), _dirPin(dirPin)
{
    pinMode(_dirPin, OUTPUT);
    pinMode(_stpPin, OUTPUT);
}

bool ClassMotor::init(){
    _motor.setRPM(RPM_MOTOR);
    _motor.setSpeedProfile(_motor.LINEAR_SPEED,ACCEL_MOTOR, ACCEL_MOTOR);
    _motor.begin(RPM_MOTOR);
    _motor.enable();

    return 0;
}

bool ClassMotor::setZero(){
    _steps = 0;
    return 0;
}

bool ClassMotor::setPositionOrder(int steps){
    _motor.move(steps);
    return 0;
}

bool ClassMotor::stop(){
    _motor.disable();
    _motor.stop();
    return 0;
}

long ClassMotor::getCurrentStep(){
    return _steps;
}



    // this->pin = pin;
    // this->mcpwm_num = unit;
    // this->timer_num = timer;
    // this->signal = signal;
    // this -> opr = opr;
    // mcpwm_gpio_init(unit, signal, pin);
    // mcpwm_config_t pwm_config;
    // pwm_config.frequency = 50;        // 50 Hz
    // pwm_config.cmpr_a = 0;            // duty (we’ll set later)
    // pwm_config.cmpr_b = 0;
    // pwm_config.counter_mode = MCPWM_UP_COUNTER;
    // pwm_config.duty_mode = MCPWM_DUTY_MODE_0;

    // mcpwm_init(unit, timer, &pwm_config);