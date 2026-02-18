#include "ClassAscenseur.hpp"

ClassAscenseur::ClassAscenseur(uint8_t stepPin, uint8_t dirPin, bool invertRotation)
    : moteur(STEP_PER_REV, dirPin, stepPin),  // initialize properly
      _dir_sig(invertRotation ? -1 : 1),
      homingHandle(NULL)
{
}

void ClassAscenseur::Init(uint8_t pinCapteur, float mmPerRev) { 
    
    mmParRev = mmPerRev;
    capteurPin = pinCapteur;
    
    pinMode(capteurPin, INPUT);
    
    moteur.setRPM((MAX_SPEED_MM_S / mmParRev) * STEP_PER_REV);
    moteur.setSpeedProfile(moteur.LINEAR_SPEED,
        (ACCEL_MM_S2 / mmParRev) * STEP_PER_REV, 
        (ACCEL_MM_S2 / mmParRev) * STEP_PER_REV
    );
    
    Serial.println("[INIT] ClassAscenseur initialisé");
}

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

// homing routine
void ClassAscenseur::Homing(){

    Serial.println("[INFO] Démarrage homing...");

    moteur.setRPM((HOMING_SPEED_MM_S / mmParRev) * STEP_PER_REV);
    moteur.setSpeedProfile(moteur.LINEAR_SPEED,
        (ACCEL_MM_S2 / mmParRev) * STEP_PER_REV, 
        (ACCEL_MM_S2 / mmParRev) * STEP_PER_REV
        );
  
        // Si déjà sur le capteur → remonte un peu avant de descendre
    if (digitalRead(capteurPin) == HIGH) {
        Serial.println("[INFO] Capteur déjà actif, on remonte un peu...");
        moteur.startMove((HOMING_BACKOFF_MM * 2 / mmParRev) * STEP_PER_REV);
        while (moteur.getStepsRemaining() != 0) {
            moteur.nextAction();
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    // Descente lente jusqu’à détection du capteur
    moteur.startMove(-100000);
    while (digitalRead(capteurPin) == LOW) { // capteur en logique directe (low = pas d'obstacle detecté)
        moteur.nextAction();
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
    }

    moteur.setRPM((MAX_SPEED_MM_S / mmParRev) * STEP_PER_REV);
    Serial.println("[OK] Homing terminé !");

}

void ClassAscenseur::StandardOp(uint8_t queueLength, uint16_t stackSize, UBaseType_t priority)
{
    // Create queue capable of holding `queueLength` floats
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


// main task
void ClassAscenseur::vAscenseur(void* pvParams) {
    
    ClassAscenseur* self = static_cast<ClassAscenseur*>(pvParams);
    float target_mm = 0.0f;
    Serial.println((bool)xQueueReceive(self->xQueue, &target_mm, portMAX_DELAY));
    
    while (true) {
        Serial.println("entered the while");
        Serial.println((bool)self->xQueue);
        // ---------- CHANGE 1: Use blocking on queue instead of polling ----------
        // Wait indefinitely for a new command
        if (self->xQueue && xQueueReceive(self->xQueue, &target_mm, portMAX_DELAY) == pdPASS) {
            Serial.println("entered the if");
            if (!self->homed) {
                Serial.println("[WARN] Ascenseur non calibré !");
                continue;
            }

            long targetSteps = (target_mm / self->mmParRev) * STEP_PER_REV;

            // Start move (non-blocking)
            self->moteur.startMove(targetSteps * self->_dir_sig);

            // ---------- CHANGE 2: Add timeout to prevent infinite loop ----------
            const TickType_t maxWaitTicks = pdMS_TO_TICKS(5000); // max 5 seconds per move
            TickType_t startTick = xTaskGetTickCount();

            while (self->moteur.getStepsRemaining() != 0) {
                Serial.println("entered the while 2");
                self->moteur.nextAction();   // non-blocking stepping
                vTaskDelay(pdMS_TO_TICKS(1)); // yield to other tasks

                if ((xTaskGetTickCount() - startTick) > maxWaitTicks) {
                    Serial.println("[ERROR] Motor move timeout!");
                    break;
                }
            }

            self->currentHeight = target_mm;
        }

        // ---------- CHANGE 3: Removed vTaskDelay(100) ----------
        // No longer needed because xQueueReceive blocks indefinitely
    }
}

void ClassAscenseur::SetZero() {
    _currentSteps = 0;
    currentHeight = 0;
    homed = true;
}

// float ClassAscenseur::GetCurrentHeight() {
//     long steps = moteur.currentPosition();
//     return (steps / (float)STEP_PER_REV) * mmParRev;
// }

bool ClassAscenseur::moveToHeight(float target_mm)
{
    if (xQueue == NULL) return false;

    // Send value to queue (blocks up to timeout if queue full)
    if (xQueueSend(xQueue, &target_mm, portMAX_DELAY) == pdPASS) {
        Serial.println("[INFO] Recieved command");
        return true;
    } else {
        Serial.println("[WARN] Queue full, move command dropped");
        return false;
    }
}


bool ClassAscenseur::IsBusy() {
    return (moteur.getStepsRemaining() != 0);
}

bool ClassAscenseur::IsHomed() {
    return homed;
}
