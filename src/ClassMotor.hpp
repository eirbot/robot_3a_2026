#ifndef CLASS_MOTOR_HPP
#define CLASS_MOTOR_HPP

#include <Arduino.h>
#include "BasicStepperDriver.h"
#include "utilities.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"


class ClassMotor {
    public:
        ClassMotor(uint8_t stepPin, uint8_t dirPin, BasicStepperDriver& motor);
        bool init();
        bool setZero();
        bool setPositionOrder(int steps);

        long getCurrentStep();
        bool stop();

    private:
        long _steps;

        uint8_t _stpPin;
        uint8_t _dirPin;

        BasicStepperDriver& _motor;


};

#endif

// Servo(mcpwm_unit_t unit, mcpwm_io_signals_t signal, mcpwm_timer_t timer, mcpwm_generator_t opr, uint8_t pin);
// #include "driver/mcpwm.h" // for servo
// #include "soc/mcpwm_periph.h"