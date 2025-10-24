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

#endif