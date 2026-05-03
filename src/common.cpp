#include "common.h"

TaskHandle_t vMotorsHandle;
TaskHandle_t handleDoStrat = NULL;

AccelStepper moteurGauche(AccelStepper::DRIVER, STEPG, DIRG); // STEP, DIR
AccelStepper moteurDroit(AccelStepper::DRIVER, STEPD, DIRD);  // STEP, DIR

ClassMotors mot;

bool FLAG_STOP = false; // Valeur initiale (1 = stop, 0 = continue)

SemaphoreHandle_t xPositionMutex;

bool jaune = true;
volatile int LiDAR_state = 0; // 0: Libre, 1: Stop, 2: Front, 3: Back

// position bleu par default
float X_POS_INIT = 1775;
float Y_POS_INIT = 220;
float ANGLE_INIT = 0;
