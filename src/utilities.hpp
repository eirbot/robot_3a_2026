#ifndef UTILITIES_HPP
#define UTILITIES_HPP

// Include necessary libraries

#include <Arduino.h>
#include "TMC2100.h"
// #include "AccelStepper.h"


// Define constants 

#define STEP_PER_REV 1600//6400//3200
#define MAX_SPEED_MM_S 200.0f//50.0f
#define ACCEL_MM_S2   400.0f//200.0f
#define HOMING_SPEED_MM_S 10.0f
#define HOMING_BACKOFF_MM 5.0f
#define MM_PAR_TOUR 8.0f
#define WHEEL_BASE 0.345f // m

// extern declarations

extern TMC2100 asc;
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

// pour ascenseur (stepper & sensor)
#define MM_PER_REV 8.0

#define ASC_1_STP 15
#define ASC_1_DIR 2
#define ASC_1_SNS 13
#define ASC_1_INV false

#define ASC_2_STP 4
#define ASC_2_DIR 16
#define ASC_2_SNS 12
#define ASC_2_INV false

#define ASC_3_STP 17
#define ASC_3_DIR 5
#define ASC_3_SNS 14
#define ASC_3_INV false

#define ASC_4_STP 18
#define ASC_4_DIR 19
#define ASC_4_SNS 27
#define ASC_4_INV false

#endif