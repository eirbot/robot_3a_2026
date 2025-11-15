#ifndef UTILITIES_HPP
#define UTILITIES_HPP

// Include necessary libraries

#include <Arduino.h>
#include "AccelStepper.h"


// Define constants 

#define STEP_PER_REV 3200
#define MAX_SPEED_MM_S 50.0f
#define ACCEL_MM_S2   200.0f
#define HOMING_SPEED_MM_S 10.0f
#define HOMING_BACKOFF_MM 5.0f
#define MM_PAR_TOUR 8.0f

// extern declarations

extern AccelStepper asc;
extern TaskHandle_t vAscHandle;


// pour ClassMotors
extern float X_POS_INIT;
extern float Y_POS_INIT;
extern float ANGLE_INIT;
typedef struct {
    int distance;
    int angle;
    int direction;
    int vitesse;
} TaskParams;
#define dRoues 100.0
#define stepPerRev 3200
#define ecartRoues 253.0
#define STEPD 17
#define DIRD 16 
#define STEPG 4
#define DIRG 2
extern AccelStepper moteurGauche; 
extern AccelStepper moteurDroit; 
extern volatile bool* FLAG_CLEAR;
extern bool FLAG_STOP;
extern bool FLAG_TIRETTE;
extern bool FLAG_DEBUG;
extern bool FLAG_TOF;
extern TaskHandle_t vMotorsHandle;
extern SemaphoreHandle_t xPositionMutex;
#define SPEEDMAX 650

#endif