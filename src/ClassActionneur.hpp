#ifndef CLASS_ACTIONNEUR_HPP
#define CLASS_ACTIONNEUR_HPP

#include "ClassServo.hpp"
#include "ClassVerin.hpp"
#include "ClassAscenseur.hpp"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

class Actionneur {
    
    public:
        Actionneur(

        // Sensor
        uint8_t snsPin,

        // servoFlip
        mcpwm_unit_t unit1, mcpwm_io_signals_t signal1,
        mcpwm_timer_t timer1, mcpwm_generator_t opr1,
        uint8_t pin_pwm1,

        // servoOrient
        mcpwm_unit_t unit2, mcpwm_io_signals_t signal2,
        mcpwm_timer_t timer2, mcpwm_generator_t opr2,
        uint8_t pin_pwm2,

        // Verin
        uint8_t pin_verin1, uint8_t pin_verin2, uint8_t pin_verin3,

        // Ascenseur
        uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation,

        // Positions
        float orientAngle, float initAngle, float initHeight, float resetAngle, float resetHeight
        );

        void runSequenceDEBUG();
        
        void init(uint8_t queueLength, uint16_t stackSize, UBaseType_t priority);
        
        bool queue_command(const char* command);
        
        bool runSequenceFlip();
        bool runSequenceNoFlip();
        bool release();
        bool init();
        bool reset();
        
    private:
        Verin verin;
        Servo servoFlip;
        Servo servoOrient;
        ClassAscenseur ascenseur; 
    
        TaskHandle_t taskHandle;
        QueueHandle_t commandQueue;


        float _orientAngle; // makes place tout flip all kaplas
        float _initAngle; // makes actionneur look forward
        float _initHeight; // init height
        float _resetAngle; // makes actionneur fit inside perimeter
        float _resetHeight;

    
        static void taskFunction(void* pvParameters);
    
        void take();
        void flip();
};

#endif