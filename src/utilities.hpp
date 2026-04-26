#ifndef UTILITIES_HPP
#define UTILITIES_HPP

// Include necessary libraries

#include <Arduino.h>
#include "AccelStepper.h"


// Define constants 

#define STEP_PER_REV 3200
#define MAX_SPEED_MM_S 1000.0f // 1 m/s max (ajustable selon les capacités de ton robot)
#define ACCEL_MM_S2   1500.0f // 1.5 m/s² d'accélération max pour éviter les glissements
#define HOMING_SPEED_MM_S 10.0f
#define HOMING_BACKOFF_MM 5.0f
#define MM_PAR_TOUR 8.0f
#define WHEEL_BASE 0.345f // m

// extern declarations

extern AccelStepper asc;
extern TaskHandle_t vAscHandle;


// pour ClassMotors

#define MOTOR_LEFT_STEP_PIN   27
#define MOTOR_LEFT_DIR_PIN    14

#define MOTOR_RIGHT_STEP_PIN  22
#define MOTOR_RIGHT_DIR_PIN   13

// Structure d'une commande de vitesse
typedef struct {
    float vitesseGauche;  // m/s
    float vitesseDroite;  // m/s
} TaskParams;

float absMax(float a, float b);



#endif