#include "ClassAscenseur.hpp"

ClassAscenseur::ClassAscenseur(uint8_t stepPin, uint8_t dirPin, bool invertRotation)
    : moteur(STEP_PER_REV, dirPin, stepPin),  // initialize properly
      _dir_sig(invertRotation ? -1 : 1),
      homingHandle(NULL)
{}

void ClassAscenseur::Init(uint8_t pinCapteur, float mmPerRev) { 
    mmParRev = mmPerRev;
    capteurPin = pinCapteur;
    pinMode(capteurPin, INPUT);
    moteur.setRPM(RPM_ASC);
    moteur.setSpeedProfile(moteur.LINEAR_SPEED,ACCEL_ASC, ACCEL_ASC);
    Serial.println("[INIT] ClassAscenseur initialisé");
}
// function to be called by main fir init
void ClassAscenseur::StartHoming(float value){
    if (homed) return; // ne rien faire si déjà homé
    if (homingHandle != NULL) return; // si une task de homing est déjà en cours, on ne relance pas
    // créer la task (ajuste stack/prio/core si nécessaire)
    BaseType_t res = xTaskCreatePinnedToCore(vHomingTask, "AscHoming", 6000, this, 2, &homingHandle, 1);
    if (res != pdPASS) {
        homingHandle = NULL; // échec de création : remettre homingHandle à NULL
    }
}

// homing task
void ClassAscenseur::vHomingTask(void* pvParams){

    ClassAscenseur* self = static_cast<ClassAscenseur*>(pvParams);
    if (!self) {
        vTaskDelete(NULL);
        return;
    }

    // appelle la routine bloquante de homing déjà présente
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
        moteur.startMove((HOMING_BACKOFF_MM * 2 / mmParRev) * STEP_PER_REV);
        while (moteur.getStepsRemaining() != 0) {
            moteur.nextAction();
            vTaskDelay(1);
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    // Descente lente jusqu’à détection du capteur
    moteur.startMove(-100000);
    Serial.println(moteur.getStepsRemaining());
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
    moteur.startMove((HOMING_BACKOFF_MM / mmParRev) * STEP_PER_REV);
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
    BaseType_t res = xTaskCreate(
        vAscenseur,          // Task function
        "vAscenseur",     // Name
        stackSize,           // Stack size
        this,                // Parameter passed to task
        priority,            // Priority
        &vAscenseurHandle    // Task handle
    );
    if (res != pdPASS) {
        Serial.println("[ERROR] Failed to create Ascenseur task");
    } else {
        Serial.println("[OK] Ascenseur task started");
    }
}

// queueing command function
bool ClassAscenseur::moveToHeight(float target_mm) {
    if (xQueue == NULL) return false; // no queue case
    if (xQueueSend(xQueue, &target_mm, portMAX_DELAY) == pdPASS) { // standard case
        Serial.println("[INFO] Recieved command");
        return true;
    } else { // queue full case
        Serial.println("[WARN] Queue full, move command dropped");
        return false;
    }
}

// main task
void ClassAscenseur::vAscenseur(void* pvParams) {
    ClassAscenseur* self = static_cast<ClassAscenseur*>(pvParams);
    float target_mm = 0.0f;
    while (true) {
        if (self->xQueue && xQueueReceive(self->xQueue, &target_mm, portMAX_DELAY) == pdPASS) {
            if (!self->homed) {
                Serial.println("[WARN] Ascenseur non calibré !");
                continue;
            }
            Serial.println("[to be deleted] target_mm " + String(target_mm)); 
            long targetSteps = (target_mm / self->mmParRev) * STEP_PER_REV;
            Serial.println("[to be deleted] target_stps " + String(targetSteps)); 
            self->moteur.startMove(targetSteps * self->_dir_sig);
            while (self->moteur.getStepsRemaining() != 0) {
                self->moteur.nextAction();
                vTaskDelay(1);
            }
            self->currentHeight = target_mm;
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
