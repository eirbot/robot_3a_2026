#include "ClassAscenseurQueue.hpp"

AscenseurQueue::AscenseurQueue(

        // Sensor
        uint8_t snsPin,

        // Ascenseur
        uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation,

        // Positions
        float initHeight, float resetHeight

):
ascenseur(stepPin, dirPin, snsPin, name, invertRotation),
_initHeight(initHeight), _resetHeight(resetHeight)
{}

enum AscenseurCommand {
    CMD_INIT,
    CMD_RESET,
    CMD_FLIP,
    CMD_nFLIP,
    CMD_DOWN
};

void AscenseurQueue::init(uint8_t queueLength, uint16_t stackSize, UBaseType_t priority){
    commandQueue = xQueueCreate(queueLength, sizeof(AscenseurCommand));

    ascenseur.init();
    //ascenseur.StandardOp(queueLength, stackSize, priority);
    xTaskCreate(
        taskFunction,        // function
        "AscenseurTask",    // name
        stackSize,           // stack
        this,                // parameter → pointer to your object
        priority,            // priority
        &taskHandle          // handle
    );
}

bool AscenseurQueue::queue_command(const char* cmd) {
    AscenseurCommand command;

    if (strcmp(cmd, "flip") == 0) {
        command = CMD_FLIP;
    } 
    else if (strcmp(cmd, "nflp") == 0) {
        command = CMD_nFLIP;
    }
    else if (strcmp(cmd, "down") == 0) {
        command = CMD_DOWN;
    }
    else if (strcmp(cmd, "init") == 0) {
        command = CMD_INIT;
    }
    else if (strcmp(cmd, "rset") == 0) {
        command = CMD_RESET;
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


void AscenseurQueue::taskFunction(void* pvParameters) {
    AscenseurQueue* self = static_cast<AscenseurQueue*>(pvParameters);
    AscenseurCommand cmd;

    while (true) {
        if (xQueueReceive(self->commandQueue, &cmd, portMAX_DELAY) == pdTRUE) {
            // Serial.println("[DEBUG] recieved");
            switch (cmd) {
                case CMD_FLIP:
                    self->goToHeightInit();
                    break;
                case CMD_nFLIP:
                    self->gotToHeightIntermediaire();
                    break;
                case CMD_DOWN:
                    self->gotoHeightRelease();
                    break;
                case CMD_INIT:
                    self->init();
                    break;
                case CMD_RESET:
                    self->reset();
                    break;
            }
        }
    }
}


/*--------------------------------------------TO  BE OPTIMIZED---------------------------------------------------*/

bool AscenseurQueue::goToHeightInit(){
    return 0;
}
bool AscenseurQueue::gotToHeightIntermediaire(){
    return 0;
    
}
bool AscenseurQueue::gotoHeightRelease(){
    return 0;
}

bool AscenseurQueue::init(){ // standby position
    return 0;
}

bool AscenseurQueue::reset(){ // position to fit inside undeployed perimeter

return 0;
}