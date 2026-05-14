#include "ActionneurVTask.hpp"

#define TASK_QUEUE_SIZE 25

QueueHandle_t 
    qActVtask1 = xQueueCreate(TASK_QUEUE_SIZE, sizeof(TaskParams)),
    qActVtask2 = xQueueCreate(TASK_QUEUE_SIZE, sizeof(TaskParams)),
    qActVtask3 = xQueueCreate(TASK_QUEUE_SIZE, sizeof(TaskParams)),
    qActVtask4 = xQueueCreate(TASK_QUEUE_SIZE, sizeof(TaskParams));

ActionneurVTask actVTask1 = ActionneurVTask(act1, 1);
ActionneurVTask actVTask2 = ActionneurVTask(act2, 2);
ActionneurVTask actVTask3 = ActionneurVTask(act3, 3);
ActionneurVTask actVTask4 = ActionneurVTask(act4, 4);

void ActionneurVTask::processCommand(TaskParams params) {
    switch (params._cmd) {
        case 'G':
            this->_act.closePiston();
            break;
        case 'R':
            this->_act.openPiston();
            break;
        case 'T':
            break;        
        case 'P':
            int angle = params._P_angleFlag ? this->pAngle1 : this->pAngle0;
            this->_act.servo_9G(angle);
            this->_act.p9G_status = angle;
            break;
            
        case 'A':
            Serial.println("SetPos");
            int mmToStep =80;
            int asked_height = params._A_param1 * mmToStep;
            break;
        
        case 'I':
            this->_act.homming();
            break;
    }
}

ActionneurVTask::ActionneurVTask(Actionneur &act, uint8_t actId, QueueHandle_t &queue): _act(act), _queue(queue) {
    this->flagInit = false;
    // assign possible p angles
    if (actId == 1) {
        this->pAngle0;
    }
    {

    }
}
