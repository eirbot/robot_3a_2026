#include "ActionneurVTask.hpp"

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
            break;
    }
}

void ActionneurVTask::vTaskRun(void *pvParameters) {
    // Queue* queue = (Queue*) pvParameters; // TODO
    // for (;;) {
    //     TaskParams params = (TaskParams) queue.getLastBlocking(); // TODO
    //     this->processCommand(params);
    // }

}

ActionneurVTask::ActionneurVTask(Actionneur &act, uint8_t actId): _act(act) {
    // assign possible p angles
    if (actId == 1) {
        this->pAngle0;
    }
    {

    }
}
