#ifndef CLASS_ASCENSEUR_HPP
#define CLASS_ASCENSEUR_HPP

#include <Arduino.h>
#include <AccelStepper.h>
#include "utilities.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

class ClassAscenseur {
public:
    ClassAscenseur();

    void Init(int stepPin, int dirPin, int pinCapteur, float mmParRev);
    void MoveToHeight(float target_mm);
    void SetZero();
    float GetCurrentHeight();
    void StartHoming();              // homing manuel si besoin
    bool IsBusy();  // indique si le moteur est encore en mouvement
    bool IsHomed();  // indique si l'ascenseur est calibré

    static void vAscenseur(void* pvParams);

private:
    AccelStepper moteur;
    QueueHandle_t xQueue;
    TaskHandle_t vAscenseurHandle;
    TaskHandle_t homingHandle = NULL; // <-- ajouté
    int capteurPin;
    float mmParRev;
    float currentHeight = 0;
    bool homed = false;

    void Homing();                   // interne
    static void vHomingTask(void* pvParams); // <-- ajouté
};

#endif
