#include "ClassActionneur.hpp"

Actionneur::Actionneur(

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
        uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation
):
servoFlip(unit1, signal1, timer1, opr1, pin_pwm1),
servoOrient(unit2, signal2, timer2, opr2, pin_pwm2),
verin(pin_verin1,pin_verin2,pin_verin3),
ascenseur(stepPin, dirPin, snsPin, name, invertRotation)
{}

enum ActionneurCommand {
    CMD_FLIP,
    CMD_nFLIP,
    CMD_DOWN
};

void Actionneur::init(uint8_t queueLength, uint16_t stackSize, UBaseType_t priority){
    commandQueue = xQueueCreate(queueLength, sizeof(ActionneurCommand));

    verin.init();
    servoFlip.init();
    servoOrient.init();
    ascenseur.init();
    //ascenseur.StandardOp(queueLength, stackSize, priority);
    xTaskCreate(
        taskFunction,        // function
        "ActionneurTask",    // name
        stackSize,           // stack
        this,                // parameter → pointer to your object
        priority,            // priority
        &taskHandle          // handle
    );
}

bool Actionneur::queue_command(const char* cmd) {
    ActionneurCommand command;

    if (strcmp(cmd, "flip") == 0) {
        command = CMD_FLIP;
    } 
    else if (strcmp(cmd, "nflp") == 0) {
        command = CMD_nFLIP;
    }
    else if (strcmp(cmd, "down") == 0) {
        command = CMD_DOWN;
    }
    else {
        return 1; // unknown command
    }

    if (commandQueue != NULL) {
        // Serial.println("[DEBUG] queuing command");
        xQueueSend(commandQueue, &command, 0);
    }
    return 0;
}


void Actionneur::taskFunction(void* pvParameters) {
    Actionneur* self = static_cast<Actionneur*>(pvParameters);
    ActionneurCommand cmd;

    while (true) {
        if (xQueueReceive(self->commandQueue, &cmd, portMAX_DELAY) == pdTRUE) {
            // Serial.println("[DEBUG] recieved");
            switch (cmd) {
                case CMD_FLIP:
                    self->runSequenceFlip();
                    break;
                case CMD_nFLIP:
                    self->runSequenceNoFlip();
                    break;
                case CMD_DOWN:
                    self->release();
                    break;
            }
        }
    }
}


void Actionneur::runSequenceDEBUG(){
    // Serial.println("[DEBUG] in run sequence debug");
    // ascenseur.MoveToHeightShortcut(100);
    verin.extend();
}

/*--------------------------------------------TO  BE OPTIMIZED---------------------------------------------------*/

bool Actionneur::runSequenceFlip(){
    verin.extend();
    ascenseur.MoveToHeightShortcut(0);
    vTaskDelay(pdMS_TO_TICKS(1000));
    verin.retract();
    vTaskDelay(pdMS_TO_TICKS(1000));
    ascenseur.MoveToHeightShortcut(50);
    servoOrient.setAngle(_orientAngle);
    vTaskDelay(pdMS_TO_TICKS(500));
    servoFlip.setAngle(180);

    return 0;
}
bool Actionneur::runSequenceNoFlip(){
    verin.extend();
    ascenseur.MoveToHeightShortcut(0);
    vTaskDelay(pdMS_TO_TICKS(1000));
    verin.retract();
    vTaskDelay(pdMS_TO_TICKS(1000));
    ascenseur.MoveToHeightShortcut(50);
    vTaskDelay(pdMS_TO_TICKS(500));

    return 0;
    
}
bool Actionneur::release(){
    ascenseur.MoveToHeightShortcut(0);
    vTaskDelay(pdMS_TO_TICKS(1000));
    verin.extend();
    vTaskDelay(pdMS_TO_TICKS(1000));
    ascenseur.MoveToHeightShortcut(100);
    // reset actionneur
    verin.retract();
    servoFlip.setAngle(0);
    servoOrient.setAngle(0);
    ascenseur.MoveToHeightShortcut(100);

    return 0;
}