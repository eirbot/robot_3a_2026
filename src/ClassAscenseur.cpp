#include "ClassAscenseur.hpp"

ClassAscenseur::ClassAscenseur(uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation)
    : moteur(STEPS_PER_REV, dirPin, stepPin),  // INIT MOTEUR
      _dir_sig(invertRotation ? -1 : 1), // INVERSION DU SENS DE ROTATION
      homingHandle(NULL),
      _name(name) //POUR DEBUG UNIQUEMENT
{}

void ClassAscenseur::Init(uint8_t pinCapteur, float mmPerRev) { 
    mmParRev = mmPerRev;
    capteurPin = pinCapteur;
    pinMode(capteurPin, INPUT);
    moteur.setRPM(RPM_ASC);
    moteur.setSpeedProfile(moteur.LINEAR_SPEED,ACCEL_ASC, ACCEL_ASC);
    Serial.println("[INIT] ClassAscenseur initialisé");
}

// function to be called by main fOr init
bool ClassAscenseur::StartHoming(float value){
    if (homed){
        Serial.println("[INFO] ALREADY HOMED");
        return true; // ne rien faire si déjà homé
    }
    if (homingHandle != NULL) return false; // si une task de homing est déjà en cours, on ne relance pas
    // créer la task (ajuste stack/prio/core si nécessaire)
    BaseType_t res = xTaskCreatePinnedToCore(vHomingTask, "AscHoming", 6000, this, 2, &homingHandle, 1);
    if (res != pdPASS) {
        homingHandle = NULL; // échec de création : remettre homingHandle à NULL
    }
    return res == pdPASS;
}

// homing task
void ClassAscenseur::vHomingTask(void* pvParams){

    ClassAscenseur* self = static_cast<ClassAscenseur*>(pvParams);
    if (!self) {
        vTaskDelete(NULL);
        return;
    }

    // ROUTINE BLOQUANTE (POUR LE THREAD))
    self->Homing();
    self->homed = true;

    self->homingHandle = NULL; // handle NULL avant de tuer la tâche pour que StartHoming puisse relancer si besoin

    vTaskDelete(NULL);
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
        moteur.startMove((HOMING_BACKOFF_MM * 2 / mmParRev) * STEPS_PER_REV);
        while (moteur.getStepsRemaining() != 0) {
            moteur.nextAction();
            vTaskDelay(1);
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    // Descente lente jusqu’à détection du capteur
    moteur.startMove(-100000);
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
    moteur.startMove((HOMING_BACKOFF_MM / mmParRev) * STEPS_PER_REV);
    while (moteur.getStepsRemaining() != 0) {
        moteur.nextAction();
        vTaskDelay(1);
    }


    moteur.setRPM(RPM_ASC);
    Serial.println("[OK] Homing terminé !");
}

// creates queue & main task 
void ClassAscenseur::StandardOp(uint8_t queueLength, uint16_t stackSize, UBaseType_t priority)
{
    // Create queue for target heights
    xQueue = xQueueCreate(queueLength, sizeof(float));
    if (xQueue == NULL) {
        Serial.println("[ERROR] Failed to create Ascenseur queue");
        return;
    }
    // Create the FreeRTOS task
    BaseType_t res = xTaskCreatePinnedToCore(
        vAscenseur,          // Task function
        "vAscenseur",     // Name
        stackSize,           // Stack size
        this,                // Parameter passed to task
        priority,            // Priority
        &vAscenseurHandle,    // Task handle
        1
    );
    if (res != pdPASS) {
        Serial.println("[ERROR] Failed to create Ascenseur task");
    } else {
        Serial.println("[OK] Ascenseur task started");
    }
}

// queueing command function
bool ClassAscenseur::MoveToHeight(float target_mm) {
    long target_steps = lround((target_mm / mmParRev) * STEPS_PER_REV); // convert mm to steps
    if (xQueue == NULL){ // no queue case
        Serial.println("[WARN] NO QUEUE");
        return false;
    }
    Serial.println("[DEBUG] Recieved command sending to queue " + String(_name));
    if (xQueueSend(xQueue, &target_steps, portMAX_DELAY) == pdPASS) { // standard case
        return true;
    } else { // queue full case
        Serial.println("[WARN] Queue full, move command dropped");
        return false;
    }
}

// main task
void ClassAscenseur::vAscenseur(void* pvParams) {
    ClassAscenseur* self = static_cast<ClassAscenseur*>(pvParams);
    int32_t command;

    while (true)
    {
        if (xQueueReceive(self->xQueue, &command, portMAX_DELAY) == pdTRUE)
        {
            Serial.println("[DEBUG] Motor " + self->_name + " recieved task");
            if (command == 0) continue;
            self->moteur.enable();
            self->moteur.move(command);
            Serial.println("[DEBUG] Motor " + self->_name + " finished");
        }
    }
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
