#ifndef COMMON_H
#define COMMON_H

#define STEPD 27
#define DIRD 14
#define STEPG 22
#define DIRG 13

#define SPEEDMAX 650
#define ACCELMAX 3000

#define dRoues 72.0
#define stepPerRev 3200
#define ecartRoues 345.0

#define vitesse_nominale 100
#define STOP_DISTANCE 300

extern float X_POS_INIT;
extern float Y_POS_INIT;
extern float ANGLE_INIT;

#include "AccelStepper.h"
#include "ClassMotors.hpp"
#include "GoToPosition.hpp"
#include "esp_task_wdt.h"

typedef struct {
  int distance;
  int angle;
  int direction;
  int vitesse;
} TaskParams;

// Déclaration des deux moteurs (type DRIVER = step/dir)
extern AccelStepper moteurGauche;
extern AccelStepper moteurDroit;

extern TaskHandle_t vMotorsHandle;
extern TaskHandle_t handleDoStrat;

extern SemaphoreHandle_t xPositionMutex;

extern volatile bool *FLAG_CLEAR; // Valeur initiale (1 = continue, 0 = stop)
extern bool FLAG_STOP;            // Valeur initiale (1 = stop, 0 = continue)
extern bool FLAG_DEBUG;           // Valeur initiale (1 = debug, 0 = normal)

extern volatile bool LiDAR_state; // Valeur initiale (1 = clear, 0 = obstacle)
#endif