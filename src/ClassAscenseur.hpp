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
    
    void Init(uint8_t pinCapteur);
    bool MoveToHeightShortcut(float target_mm);
    void Homing();
    void SetZero();
    float GetCurrentHeight();
    bool IsBusy();  // indique si le moteur est encore en mouvement
    bool IsHomed();  // indique si l'ascenseur est calibré
    
    private:
    uint8_t capteurPin;
    TMC2100 moteur;

    String _name; //UTILISER POUR LES LOGS DE DEBUG UNIQUEMENT
    
    int _dir_sig; // 1 ou -1 selon le sens de rotation du moteur pour que les commandes soient cohérentes avec la réalité
    long _currentSteps = 0;
    
    //float mmParRev = MM_PER_REV;
    float maxHeight = 100; //mm
    float currentHeight = 0;
    bool homed = false;

};

#endif
