#include "common.h"

TaskHandle_t vMotorsHandle;
TaskHandle_t handleDoStrat = NULL;

AccelStepper moteurGauche(AccelStepper::DRIVER, STEPG, DIRG); // STEP, DIR
AccelStepper moteurDroit(AccelStepper::DRIVER, STEPD, DIRD);  // STEP, DIR

ClassMotors mot;

bool FLAG_STOP = false;           // Valeur initiale (1 = stop, 0 = continue)

SemaphoreHandle_t xPositionMutex;

bool jaune = true;
volatile bool LiDAR_state = true; // Valeur initiale (1 = clear, 0 = obstacle)

// position bleu par default
float X_POS_INIT = 1775;
float Y_POS_INIT = 220;
float ANGLE_INIT = 0;
