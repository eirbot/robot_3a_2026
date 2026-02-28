#include "ClassAscenseur.hpp"

ClassAscenseur::ClassAscenseur(uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation)
    : moteur(STEPS_PER_REV, dirPin, stepPin),  // INIT MOTEUR
      _dir_sig(invertRotation ? -1 : 1), // INVERSION DU SENS DE ROTATION
      _name(name) //POUR DEBUG UNIQUEMENT
{}

void ClassAscenseur::Init(uint8_t pinCapteur) { 
    capteurPin = pinCapteur;
    pinMode(capteurPin, INPUT);
    moteur.setRPM(RPM_ASC);
    moteur.setSpeedProfile(moteur.LINEAR_SPEED,ACCEL_ASC, ACCEL_ASC);
    Homing();
    Serial.println("[INIT] ClassAscenseur initialisé");
}

// homing routine function
void ClassAscenseur::Homing(){
    moteur.begin(RPM_HOMING);
    moteur.enable();

    Serial.println("[INFO] Démarrage homing...");

    moteur.setRPM(RPM_HOMING);
    moteur.setSpeedProfile(moteur.LINEAR_SPEED,
        ACCEL_ASC, 
        ACCEL_ASC
        );
  
        // Si déjà sur le capteur → remonte un peu avant de descendre
    if (digitalRead(capteurPin) == HIGH) {
        Serial.println("[INFO] Capteur déjà actif, on remonte un peu...");
        moteur.startMove(_dir_sig*(HOMING_BACKOFF_MM * 2 / MM_PER_REV) * STEPS_PER_REV);
        while (moteur.getStepsRemaining() != 0) {
            moteur.nextAction();
            vTaskDelay(1);
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    // Descente lente jusqu’à détection du capteur
    moteur.startMove(_dir_sig*-100000);
    while (digitalRead(capteurPin) == LOW) {
        moteur.nextAction();
        taskYIELD();   // allow RTOS scheduling without killing step timing
    }


    
    moteur.stop();
    vTaskDelay(pdMS_TO_TICKS(100));
    
    // Position                                                                                                                                                                                                                                                                                                                                                                                                                                          n zéro
    SetZero();
    
    //---------------DEMANDER A GUILLAUME-----------------//
    // Petit recul pour libérer le capteur
    moteur.startMove(_dir_sig*(HOMING_BACKOFF_MM / MM_PER_REV) * STEPS_PER_REV);
    while (moteur.getStepsRemaining() != 0) {
        moteur.nextAction();
        vTaskDelay(1);
    }

    currentHeight = HOMING_BACKOFF_MM;

    moteur.setRPM(RPM_ASC);
    Serial.println("[OK] Homing terminé !");
}

bool ClassAscenseur::MoveToHeightShortcut(float target_mm){
    // Serial.println("[DEBUG] in shortcut");
    if (target_mm <= 0)
    {
        target_mm = 0;
    }
    else if (target_mm > maxHeight)
    {
        target_mm = maxHeight;
    }

    long target_steps = lround(((target_mm - currentHeight) / MM_PER_REV) * STEPS_PER_REV); // convert mm to steps
    // Serial.println("[DEBUG] steps : " + String(target_steps));
    if (target_steps == 0)return 1;
    // Serial.println("[DEBUG] enabling");
    moteur.begin(RPM_HOMING);
    moteur.enable();
    // Serial.println("[DEBUG] moving");
    moteur.move(_dir_sig*target_steps);
    // Serial.println("[DEBUG] Motor finished");
    currentHeight = target_mm; // update current height estimation
    return 0;

}

void ClassAscenseur::SetZero() {
    _currentSteps = 0;
    currentHeight = 0;
    homed = true;
}

float ClassAscenseur::GetCurrentHeight() {
    return currentHeight;
}

bool ClassAscenseur::IsBusy() {
    return (moteur.getStepsRemaining() != 0);
}

bool ClassAscenseur::IsHomed() {
    return homed;
}
