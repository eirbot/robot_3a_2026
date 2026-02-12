#include "ClassAscenseur.hpp"

ClassAscenseur::ClassAscenseur() {
    homingHandle = NULL; // <-- initialisation
}

void ClassAscenseur::Init(int stepPin, int dirPin, int pinCapteur, float mmPerRev, bool InvertRotation) { 

    mmParRev = mmPerRev;
    capteurPin = pinCapteur;
    moteur = AccelStepper(AccelStepper::DRIVER, stepPin, dirPin);

    xQueue = xQueueCreate(10, sizeof(float));
    pinMode(capteurPin, INPUT);

    moteur.setMaxSpeed((MAX_SPEED_MM_S / mmParRev) * STEP_PER_REV);
    moteur.setAcceleration((ACCEL_MM_S2 / mmParRev) * STEP_PER_REV);
    moteur.setPinsInverted(InvertRotation == 1 ? true : false, false, false); // inversion du step si sensRotation = -1);


    homingHandle = NULL; // initialisation

    // équilibrage des tâches entre les 2 cœurs
    xTaskCreatePinnedToCore(vAscenseur, "vAscenseur", 10000, this, 1, &vAscenseurHandle, 1);

    Serial.println("[INIT] ClassAscenseur initialisé");
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


void ClassAscenseur::StartHoming(){

    if (homed) return; // ne rien faire si déjà homé
    
    if (homingHandle != NULL) return; // si une task de homing est déjà en cours, on ne relance pas

    // créer la task (ajuste stack/prio/core si nécessaire)
    BaseType_t res = xTaskCreatePinnedToCore(vHomingTask, "AscHoming", 6000, this, 2, &homingHandle, 1);

    if (res != pdPASS) {
        homingHandle = NULL; // échec de création : remettre homingHandle à NULL
    }
}


// main task
void ClassAscenseur::vAscenseur(void* pvParams){

    ClassAscenseur* self = static_cast<ClassAscenseur*>(pvParams);
    float target_mm = 0.0f;

    while (true) {
        // Attente d'une commande
        if (xQueueReceive(self->xQueue, &target_mm, pdMS_TO_TICKS(10)) == pdPASS) {
            if (!self->homed) {
                Serial.println("[WARN] Ascenseur non calibré !");
                continue;
            }

            long targetSteps = (target_mm / self->mmParRev) * STEP_PER_REV;
            self->moteur.moveTo(targetSteps);

            while (self->moteur.distanceToGo() != 0) {
                self->moteur.run();
            }

            self->currentHeight = target_mm;
        }

        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

// homing routine
void ClassAscenseur::Homing(){

    Serial.println("[INFO] Démarrage homing...");

    moteur.setMaxSpeed((HOMING_SPEED_MM_S / mmParRev) * STEP_PER_REV);
    moteur.setAcceleration((ACCEL_MM_S2 / mmParRev) * STEP_PER_REV);

    // Si déjà sur le capteur → remonte un peu avant de descendre
    if (digitalRead(capteurPin) == HIGH) {
        Serial.println("[INFO] Capteur déjà actif, on remonte un peu...");
        moteur.move((HOMING_BACKOFF_MM * 2 / mmParRev) * STEP_PER_REV);
        while (moteur.distanceToGo() != 0) {
            moteur.run();
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    // Descente lente jusqu’à détection du capteur
    moteur.moveTo(-100000);
    while (digitalRead(capteurPin) == LOW) { // capteur en logique directe (low = pas d'obstacle detecté)
        moteur.run();
    }
    
    moteur.stop();
    vTaskDelay(pdMS_TO_TICKS(100));
    
    // Position zéro
    SetZero();
    
    //---------------DEMANDER A GUILLAUME-----------------//
    // Petit recul pour libérer le capteur
    moteur.move((HOMING_BACKOFF_MM / mmParRev) * STEP_PER_REV);
    while (moteur.distanceToGo() != 0) {
        moteur.run();
    }

    moteur.setMaxSpeed((MAX_SPEED_MM_S / mmParRev) * STEP_PER_REV);
    Serial.println("[OK] Homing terminé !");
}

void ClassAscenseur::SetZero() {
    moteur.setCurrentPosition(0);
    currentHeight = 0;
    homed = true;
}

float ClassAscenseur::GetCurrentHeight() {
    long steps = moteur.currentPosition();
    return (steps / (float)STEP_PER_REV) * mmParRev;
}

void ClassAscenseur::MoveToHeight(float target_mm) {
    xQueueSend(xQueue, &target_mm, portMAX_DELAY);
}

bool ClassAscenseur::IsBusy() {
    return (moteur.distanceToGo() != 0);
}

bool ClassAscenseur::IsHomed() {
    return homed;
}
