#pragma once
#include <Arduino.h>
#include <AccelStepper.h>
#include "utilities.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"

class ClassMotors {
public:
    ClassMotors();
    void StartMotors();

    // Envoi d'une nouvelle commande
    void EnvoyerVitesse(TaskParams* params);

    // STOP immédiat
    void Stop();

    // Odométrie
    void GetPosition(float &x, float &y, float &angle);

    // Remise à zéro de la position
    void ResetPosition(float x = 0, float y = 0, float angle = 0);

private:
    static void vMotors(void* pvParameters);
    void UpdateOdometry();

    static ClassMotors* instancePtr;
    static void IRAM_ATTR onTimer();
    hw_timer_t* timer = nullptr;

private:
    // Les deux moteurs
    AccelStepper moteurGauche;
    AccelStepper moteurDroit;

    // File FreeRTOS
    QueueHandle_t xQueue;

    // Task handle
    TaskHandle_t vMotorsHandle;

    // Mutex position
    SemaphoreHandle_t posMutex;

    // Odométrie
    float x_pos;
    float y_pos;
    float orientation;

    long lastStepGauche;
    long lastStepDroit;

    // Constantes robot
    const float dRoues = 0.0723f;      // diamètre roue (m)
    const float ecartRoues = 0.343f;   // entraxe (m)
    const float stepPerRev = 3200.0f;  // steps par tour moteur (sans microstepping)
};
