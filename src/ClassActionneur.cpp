#include "ClassActionneur.hpp"

ClassActionneur::ClassActionneur() {
    ascenseur = ClassAscenseur();
    cmdQueue = NULL;
    taskHandle = NULL;
}

void ClassActionneur::StartTask() {
    if (taskHandle != NULL) return;
    if (cmdQueue == NULL) {
        cmdQueue = xQueueCreate(10, sizeof(ActionneurCommand));
    }
    BaseType_t res = xTaskCreatePinnedToCore(vActionneurTask, "ActTask", 8000, this, 1, &taskHandle, 1);
    if (res != pdPASS) {
        taskHandle = NULL;
    }
}

void ClassActionneur::StopTask() {
    if (taskHandle) {
        vTaskDelete(taskHandle);
        taskHandle = NULL;
    }
    if (cmdQueue) {
        vQueueDelete(cmdQueue);
        cmdQueue = NULL;
    }
}

void ClassActionneur::Init(int stepPin, int dirPin, int pinCapteur,
                           int servoRotatePin, int servoOrientPin,
                           int verinDirPin, int verinPWMPin){

    this->verinDirPin = verinDirPin;
    this->verinPWMPin = verinPWMPin;

    ascenseur.Init(stepPin, dirPin, pinCapteur, MM_PAR_TOUR); // 8mm par révolution
    servoRotate.attach(servoRotatePin, SERVO_MIN_US, SERVO_MAX_US);
    servoOrient.attach(servoOrientPin, SERVO_MIN_US, SERVO_MAX_US);
    pinMode(verinDirPin, OUTPUT);
    pinMode(verinPWMPin, OUTPUT);
}

bool ClassActionneur::PostCommand(const ActionneurCommand& cmd) {
    if (cmdQueue == NULL) return false;
    return xQueueSend(cmdQueue, &cmd, 0) == pdTRUE;
}

void ClassActionneur::StartHomingNonBlocking() {
    ActionneurCommand cmd{};
    cmd.type = ActionneurCmdType::CMD_HOMING;
    cmd.value = 0;
    cmd.channel = 0;
    PostCommand(cmd);
}

void ClassActionneur::vActionneurTask(void* pvParams) {
    ClassActionneur* self = static_cast<ClassActionneur*>(pvParams);
    ActionneurCommand cmd;
    while (1) {
        if (self->cmdQueue && xQueueReceive(self->cmdQueue, &cmd, portMAX_DELAY) == pdTRUE) {
            switch (cmd.type) {
            case ActionneurCmdType::CMD_HOMING:
                if (!self->ascenseur.IsHomed()) {
                    self->ascenseur.StartHoming();
                }
                break;

            case ActionneurCmdType::CMD_MOVE_ASC:
                if (self->ascenseur.IsHomed()) {
                    self->ascenseur.MoveToHeight(cmd.value);
                }
                break;

            case ActionneurCmdType::CMD_SERVO_POS:
                if(cmd.channel == 0)
                    self->servoOrient.write(constrain(cmd.value, 0, 180));
                else if (cmd.channel == 1)
                    self->servoRotate.write(constrain(cmd.value, 0, 180));
                break;

            case ActionneurCmdType::CMD_VERIN_EXT:
                float speed_mm_s = constrain(cmd.value, -VERIN_SPEED_MAX_MM_S, VERIN_SPEED_MAX_MM_S);
                if(speed_mm_s > 0)
                    digitalWrite(self->verinDirPin, HIGH);
                else
                    digitalWrite(self->verinDirPin, LOW);
                
                int pwmValue = map(abs(speed_mm_s), 0, VERIN_SPEED_MAX_MM_S, 0, VERIN_SPEED_MAX_PWM);
                analogWrite(self->verinPWMPin, pwmValue);
                break;
            }
        }
    }
}

// === États ===
bool ClassActionneur::IsReady() {
    return ascenseur.IsHomed() && !ascenseur.IsBusy();
}

bool ClassActionneur::IsHomed() {
    return ascenseur.IsHomed();
}

bool ClassActionneur::IsElevatorBusy() {
    return ascenseur.IsBusy();
}

float ClassActionneur::GetHeight() {
    return ascenseur.GetCurrentHeight();
}
