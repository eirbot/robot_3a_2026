#ifndef CLASS_ACTIONNEUR_HPP
#define CLASS_ACTIONNEUR_HPP

#include "ClassServo.hpp"
#include "ClassVerin.hpp"
#include "ClassAscenseur.hpp"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

class Actionneur {
private:
    Verin verin;
    Servo servo1;
    Servo servo2;
    ClassAscenseur ascenseur; 

    TaskHandle_t taskHandle;
    QueueHandle_t commandQueue;

    static void taskFunction(void* pvParameters);

public:
    Actionneur(
        // Servo1
        mcpwm_unit_t unit1, mcpwm_io_signals_t signal1,
        mcpwm_timer_t timer1, mcpwm_generator_t opr1,
        uint8_t pin_pwm1,

        // Servo2
        mcpwm_unit_t unit2, mcpwm_io_signals_t signal2,
        mcpwm_timer_t timer2, mcpwm_generator_t opr2,
        uint8_t pin_pwm2,

        // Verin
        uint8_t pin_verin1, uint8_t pin_verin2, uint8_t pin_verin3,

        // Ascenseur
        uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation = false
    );

    void runSequenceDEBUG();

    void init(uint8_t pin_sns, uint8_t queueLength, uint16_t stackSize, UBaseType_t priority);

    bool receive_command(char * command);

    void runSequence();
};

#endif