#include "utilities.hpp"

TaskHandle_t vMotorsHandle;


AccelStepper moteurGauche(AccelStepper::DRIVER, STEPG, DIRG); // STEP, DIR
AccelStepper moteurDroit(AccelStepper::DRIVER, STEPD, DIRD);  // STEP, DIR

volatile bool* FLAG_CLEAR = NULL; // Valeur initiale (1 = continue, 0 = stop)
bool FLAG_STOP = false; // Valeur initiale (1 = stop, 0 = continue)
bool FLAG_TIRETTE = false;
bool FLAG_DEBUG = true; // Valeur initiale (1 = debug, 0 = normal)
bool FLAG_TOF = false; // Valeur initiale (1 = TOF actif, 0 = inactif)

SemaphoreHandle_t xPositionMutex;

//position bleu par default
float X_POS_INIT= 1775;
float Y_POS_INIT= 220;
float ANGLE_INIT= 0;