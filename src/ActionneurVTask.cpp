#include "ActionneurVTask.hpp"
#include <cstdint>

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
            if(this->_act.p9G_status == 0){
              this->_act.servo_9G(180);
              this->_act.p9G_status = 180;
            } else {
              this->_act.servo_9G(0);
              this->_act.p9G_status = 0;
            };
            break;
        case 'P':
            this->_act.soft_servo(params._P_angleFlag ? this->pAngle0 : 90);
            break;
        case 'A':
            Serial.println("SetPos");
            int mmToStep = 80;
            int asked_height = params._A_param1* mmToStep;
            if(asked_height - this->_act.asc_height >=0){
              this->_act.goUp(asked_height - this->_act.asc_height);
            } else {
              this->_act.goDown(this->_act.asc_height - asked_height);
            };
            this->_act.asc_height = asked_height;
            break;
        case 'I':
            this->_act.homming();
        default:
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

const uint16_t pangles0[4] = {40, 60, 120, 140};

ActionneurVTask::ActionneurVTask(Actionneur &act, uint8_t actId): _act(act) {
    // assign possible p angles
    if (actId < 4)
      this->pAngle0 = pangles0[actId];
}
