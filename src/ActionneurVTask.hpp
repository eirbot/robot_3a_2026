#pragma once
#include "Actionneurs.hpp"
#include <stdint.h>

 /**
 * G: None
 * R: None
 * T: Inversion of current state, no param needed
 * P: Angle flag, one value or the other
 * A: PID controller factor ??? TODO: CHECK
 * I: None
 */
class TaskParams {
    public:
        TaskParams(char cmd, uint8_t P_angleFlag, int A_param1): _cmd(cmd), _P_angleFlag(P_angleFlag) {}
        const char _cmd;
        const uint8_t _P_angleFlag;
        const int _A_param1;
    private:

}

class ActionneurVTask {
public:
    ActionneurVTask(Actionneur& act, uint8_t actId);
    void vTaskRun(void *pvParameters);
    void processCommand(TaskParams params);
private:
    Actionneur& _act;
    uint16_t pAngle0, pAngle1;
}

extern ActionneurVTask actVtask1;
extern ActionneurVTask actVtask2;
extern ActionneurVTask actVtask3;
extern ActionneurVTask actVtask4;