#ifndef UTILITIES_HPP
#define UTILITIES_HPP

// Include necessary libraries

#include <Arduino.h>
#include "TMC2100.h" // RTOS FRIENDLY A PRIVILGIER


// Define constants 

#define STEPS_PER_REV 3200 // pour asceseur ATTENTION CELA PREND EN COMPTE LES MICROSTEPS
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

// pour servo 

#define MIN_ANGLE 0
#define MAX_ANGLE 135

// pour ascenseur (stepper & sensor)
#define RPM_ASC 200
#define RPM_HOMING 120
#define ACCEL_ASC 800
#define MM_PER_REV 79.0 // MESURE OK NE PAS TOUCHER

#define PIN_ASC_STP_ACT1 15
#define PIN_ASC_DIR_ACT1 2
#define PIN_ASC_SNS_1 13
#define ASC_1_INV false

#define PIN_ASC_STP_ACT2 4
#define PIN_ASC_DIR_ACT2 16
#define PIN_ASC_SNS_2 12
#define ASC_2_INV false

#define PIN_ASC_STP_ACT3 17
#define PIN_ASC_DIR_ACT3 5
#define PIN_ASC_SNS_3 14
#define ASC_3_INV false

#define PIN_ASC_STP_ACT4 18
#define PIN_ASC_DIR_ACT4 19
#define PIN_ASC_SNS_4 27
#define ASC_4_INV false

// pour actionneur (hors ascenseur)
//////////////// ACT1 //////////////////

#define PIN_PW_1_ACT1 3
#define PIN_PW_2_ACT1 4
#define PIN_VERIN_1_ACT1 5
#define PIN_VERIN_2_ACT1 6
#define PIN_VERIN_3_PWM_ACT1 7

#define UNIT_PWM_1   MCPWM_UNIT_0
#define SIGNAL_PWM_1 MCPWM0A
#define TIMER_PWM_1  MCPWM_TIMER_0
#define OPR_PWM_1    MCPWM_OPR_A

#define UNIT_PWM_2   MCPWM_UNIT_0
#define SIGNAL_PWM_2 MCPWM0B
#define TIMER_PWM_2  MCPWM_TIMER_0
#define OPR_PWM_2    MCPWM_OPR_B

//////////////// ACT2 //////////////////

#define PIN_PW_1_ACT2 11
#define PIN_PW_2_ACT2 12
#define PIN_VERIN_1_ACT2 13
#define PIN_VERIN_2_ACT2 14
#define PIN_VERIN_3_PWM_ACT2 15

#define UNIT_PWM_3   MCPWM_UNIT_0
#define SIGNAL_PWM_3 MCPWM1A
#define TIMER_PWM_3  MCPWM_TIMER_1
#define OPR_PWM_3    MCPWM_OPR_A

#define UNIT_PWM_4   MCPWM_UNIT_0
#define SIGNAL_PWM_4 MCPWM1B
#define TIMER_PWM_4  MCPWM_TIMER_1
#define OPR_PWM_4    MCPWM_OPR_B

//////////////// ACT3 //////////////////

#define PIN_PW_1_ACT3 19
#define PIN_PW_2_ACT3 20
#define PIN_VERIN_1_ACT3 21
#define PIN_VERIN_2_ACT3 22
#define PIN_VERIN_3_PWM_ACT3 23

#define UNIT_PWM_5   MCPWM_UNIT_0
#define SIGNAL_PWM_5 MCPWM2A
#define TIMER_PWM_5  MCPWM_TIMER_2
#define OPR_PWM_5    MCPWM_OPR_A

#define UNIT_PWM_6   MCPWM_UNIT_0
#define SIGNAL_PWM_6 MCPWM2B
#define TIMER_PWM_6  MCPWM_TIMER_2
#define OPR_PWM_6    MCPWM_OPR_B

//////////////// ACT4 //////////////////

#define PIN_PW_1_ACT4 27
#define PIN_PW_2_ACT4 28
#define PIN_VERIN_1_ACT4 29
#define PIN_VERIN_2_ACT4 30
#define PIN_VERIN_3_PWM_ACT4 31

#define UNIT_PWM_7   MCPWM_UNIT_1
#define SIGNAL_PWM_7 MCPWM0A
#define TIMER_PWM_7  MCPWM_TIMER_0
#define OPR_PWM_7    MCPWM_OPR_A

#define UNIT_PWM_8   MCPWM_UNIT_1
#define SIGNAL_PWM_8 MCPWM0B
#define TIMER_PWM_8  MCPWM_TIMER_0
#define OPR_PWM_8    MCPWM_OPR_B

#endif