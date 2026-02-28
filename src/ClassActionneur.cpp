#include "ClassActionneur.hpp"

Actionneur::Actionneur(
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
        uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation
):
servo1(unit1, signal1, timer1, opr1, pin_pwm1),
servo2(unit2, signal2, timer2, opr2, pin_pwm2),
verin(pin_verin1,pin_verin2,pin_verin3),
ascenseur(stepPin, dirPin, name, invertRotation)
{}

enum ActionneurCommand {
    CMD_FLIP,
    CMD_UNFLIP
};

void Actionneur::init(uint8_t pin_sns, uint8_t queueLength, uint16_t stackSize, UBaseType_t priority){
    commandQueue = xQueueCreate(queueLength, sizeof(ActionneurCommand));

    verin.init();
    servo1.init();
    servo2.init();
    ascenseur.Init(pin_sns);
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

bool Actionneur::receive_command(char * cmd) {
    ActionneurCommand command;

    if (strcmp(cmd, "flip") == 0) {
        command = CMD_FLIP;
    } 
    else if (strcmp(cmd, "unflip") == 0) {
        command = CMD_UNFLIP;
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
                    self->runSequence();
                    break;

                case CMD_UNFLIP:
                    self->runSequence();
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
void Actionneur::runSequence() {
    // Serial.println("[SEQUENCE] init");
    verin.retract();
    servo1.setAngle(0);
    servo2.setAngle(0);
    ascenseur.MoveToHeightShortcut(100);
    vTaskDelay(pdMS_TO_TICKS(4000));
    // Serial.println("[SEQUENCE] 1 verin extend ");
    verin.extend();

    // Serial.println("[SEQUENCE] 2 asc descend");
    ascenseur.MoveToHeightShortcut(0);
    vTaskDelay(pdMS_TO_TICKS(4000));

    // Serial.println("[SEQUENCE] 3 verin retract");
    verin.retract();
    vTaskDelay(pdMS_TO_TICKS(4000));

    // Serial.println("[SEQUENCE] 4 asc monte");
    ascenseur.MoveToHeightShortcut(50);
    vTaskDelay(pdMS_TO_TICKS(1000));

    // Serial.println("[SEQUENCE] 5 servo turn");
    servo1.setAngle(180);
    servo2.setAngle(180);
    vTaskDelay(pdMS_TO_TICKS(1000));

    // Serial.println("[SEQUENCE] 6 asc descend");
    ascenseur.MoveToHeightShortcut(0);
    vTaskDelay(pdMS_TO_TICKS(1000));

    // Serial.println("[SEQUENCE] 7 verin extend");
    verin.extend();
    vTaskDelay(pdMS_TO_TICKS(1000));

    // Serial.println("[SEQUENCE] 8 asc monte reset");
    ascenseur.MoveToHeightShortcut(100);
    vTaskDelay(pdMS_TO_TICKS(4000));
}