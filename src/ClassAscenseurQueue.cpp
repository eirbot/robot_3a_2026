#include "ClassAscenseurQueue.hpp"

AscenseurQueue::AscenseurQueue(

        // Sensor
        uint8_t snsPin,

        // Ascenseur
        uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation,

        // Positions
        float initHeight, float resetHeight, float midHeight, float highHeight

):
ascenseur(stepPin, dirPin, snsPin, name, invertRotation),
_initHeight(initHeight), _resetHeight(resetHeight), _midHeight(midHeight), _highHeight(highHeight)
{}

enum AscenseurCommand {
    CMD_INIT,
    CMD_RESET,
    CMD_LOW,
    CMD_MID,
    CMD_HIGH
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

    if (strcmp(cmd, "high") == 0) {
        command = CMD_HIGH;
    } 
    else if (strcmp(cmd, "hmid") == 0) {
        command = CMD_MID;
    }
    else if (strcmp(cmd, "hlow") == 0) {
        command = CMD_LOW;
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
                case CMD_HIGH:
                    self->goToHeightInit();
                    break;
                case CMD_MID:
                    self->gotToHeightIntermediaire();
                    break;
                case CMD_LOW:
                    self->goToHeightInit();
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
    ascenseur.MoveToHeightShortcut(_initHeight);
    return 0;
}
bool AscenseurQueue::gotToHeightIntermediaire(){
    ascenseur.MoveToHeightShortcut(_midHeight);
    return 0;
    
}
bool AscenseurQueue::gotoHeightRelease(){
    ascenseur.MoveToHeightShortcut(_initHeight);
    return 0;
}

bool AscenseurQueue::init(){ // standby position
    ascenseur.init();
    return 0;
}

bool AscenseurQueue::reset(){ // position to fit inside undeployed perimeter
    ascenseur.MoveToHeightShortcut(_resetHeight);
return 0;
}