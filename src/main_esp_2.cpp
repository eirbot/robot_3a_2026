#include "task_manager_ascenseur.hpp"

#define INIT_HEIGHT_ASC  0.0f
#define RESET_HEIGHT_ASC 100.0f
#define MID_HEIGHT_ASC   50.0f
#define HIGH_HEIGHT_ASC  100.0f

/*-----------------------------------------------------------------------------------------------------*/
AscenseurQueue ASC1(
    34,                     // snsPin
    26, 27, "ASC1", false,  // stepPin, dirPin, name, invertRotation
    INIT_HEIGHT_ASC, RESET_HEIGHT_ASC, MID_HEIGHT_ASC, HIGH_HEIGHT_ASC // initHeight, resetHeight, midHeight, highHeight
);
AscenseurQueue ASC2(
    34,                     // snsPin
    26, 27, "ASC2", false,  // stepPin, dirPin, name, invertRotation
    INIT_HEIGHT_ASC, RESET_HEIGHT_ASC, MID_HEIGHT_ASC, HIGH_HEIGHT_ASC // initHeight, resetHeight, midHeight, highHeight
);
AscenseurQueue ASC3(
    34,                     // snsPin
    26, 27, "ASC3", false,  // stepPin, dirPin, name, invertRotation
    INIT_HEIGHT_ASC, RESET_HEIGHT_ASC, MID_HEIGHT_ASC, HIGH_HEIGHT_ASC // initHeight, resetHeight, midHeight, highHeight
);
AscenseurQueue ASC4(
    34,                     // snsPin
    26, 27, "ASC4", false,  // stepPin, dirPin, name, invertRotation
    INIT_HEIGHT_ASC, RESET_HEIGHT_ASC, MID_HEIGHT_ASC, HIGH_HEIGHT_ASC // initHeight, resetHeight, midHeight, highHeight
);
/*-----------------------------------------------------------------------------------------------------*/

ClassCommandAscenseur task_manager_ascenseur;


void setup(){
    Serial.begin(115200);
    Serial1.begin(115200);
    ASC1.init();
    ASC2.init();
    ASC3.init();
    ASC4.init();
    task_manager_ascenseur.StartCommandTask();
}

void loop(){}