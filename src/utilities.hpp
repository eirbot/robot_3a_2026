#ifndef UTILITIES_HPP
#define UTILITIES_HPP

// Include necessary libraries

#include <Arduino.h>
#include "AccelStepper.h"


// Define constants 

#define STEP_PER_REV 1600//6400//3200
#define MAX_SPEED_MM_S 200.0f//50.0f
#define ACCEL_MM_S2   400.0f//200.0f
#define HOMING_SPEED_MM_S 10.0f
#define HOMING_BACKOFF_MM 5.0f
#define MM_PAR_TOUR 8.0f
#define WHEEL_BASE 0.345f // m

// extern declarations

extern AccelStepper asc;
extern TaskHandle_t vAscHandle;


// pour ClassMotors

#define MOTOR_LEFT_STEP_PIN   4
#define MOTOR_LEFT_DIR_PIN    2

#define MOTOR_RIGHT_STEP_PIN  17
#define MOTOR_RIGHT_DIR_PIN   16

// Structure d'une commande de vitesse
typedef struct {
    float vitesseGauche;  // m/s
    float vitesseDroite;  // m/s
} TaskParams;




#endif