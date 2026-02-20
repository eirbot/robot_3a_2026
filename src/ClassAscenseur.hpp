#ifndef CLASS_ASCENSEUR_HPP
#define CLASS_ASCENSEUR_HPP

#include <Arduino.h>
#include <TMC2100.h>
#include "utilities.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"


class ClassAscenseur {
public:
    ClassAscenseur(uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation = false);
    
    void Init(uint8_t pinCapteur, float mmParRev);

    bool MoveToHeight(float target_mm);
    bool StartHoming(float value = 0); // FLOAT INUTILISÉ UNIQUEMENT POUR DES RAISON D'INTERFACAGE AVEC COMMAND MANAGER
    void SetZero();
    float GetCurrentHeight();
    void StandardOp(uint8_t queueLength, uint16_t stackSize, UBaseType_t priority);
    bool IsBusy();  // indique si le moteur est encore en mouvement
    bool IsHomed();  // indique si l'ascenseur est calibré

    static void vAscenseur(void* pvParams);

private:
    uint8_t capteurPin;
    TMC2100 moteur;
    QueueHandle_t xQueue;
    TaskHandle_t vAscenseurHandle;
    TaskHandle_t homingHandle = NULL;

    String _name; //UTILISER POUR LES LOGS DE DEBUG UNIQUEMENT

    int _dir_sig; // 1 ou -1 selon le sens de rotation du moteur pour que les commandes soient cohérentes avec la réalité
    long _currentSteps = 0;

    float mmParRev;
    float currentHeight = 0;
    bool homed = false;

    void Homing();                   // interne
    static void vHomingTask(void* pvParams);

};

#endif
