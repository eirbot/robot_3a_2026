#include "ClassMotors.hpp"

ClassMotors::ClassMotors()
: moteurGauche(AccelStepper::DRIVER, MOTOR_LEFT_STEP_PIN, MOTOR_LEFT_DIR_PIN),
  moteurDroit(AccelStepper::DRIVER, MOTOR_RIGHT_STEP_PIN, MOTOR_RIGHT_DIR_PIN)
{
    // Setup queue (1 slot = overwrite)
    xQueue = xQueueCreate(1, sizeof(TaskParams));

    // Odométrie
    posMutex = xSemaphoreCreateMutex();
    x_pos = 0; y_pos = 0; orientation = 0;
    lastStepGauche = 0;
    lastStepDroit  = 0;

    // Grande vitesse max, aucun frein logiciel
    moteurGauche.setMaxSpeed(50000);
    moteurDroit.setMaxSpeed(50000);
}

void ClassMotors::StartMotors() {
    xTaskCreatePinnedToCore(vMotors, "vMotors", 8000, this, 2, &vMotorsHandle, 1);
}

void ClassMotors::EnvoyerVitesse(TaskParams* params) {
    // Toujours garder la dernière commande : overwrite
    xQueueOverwrite(xQueue, params);
}

void ClassMotors::Stop() {
    moteurGauche.setSpeed(0);
    moteurDroit.setSpeed(0);
}

void ClassMotors::ResetPosition(float x, float y, float angle) {
    if (xSemaphoreTake(posMutex, portMAX_DELAY) == pdTRUE) {
        x_pos = x;
        y_pos = y;
        orientation = angle;
        xSemaphoreGive(posMutex);
    }

    moteurGauche.setCurrentPosition(0);
    moteurDroit.setCurrentPosition(0);

    lastStepGauche = 0;
    lastStepDroit  = 0;
}


void ClassMotors::vMotors(void* pvParameters) {
    ClassMotors* instance = (ClassMotors*)pvParameters;

    TaskParams params;
    float speedL = 0;
    float speedR = 0;

    const float stepPerMeter = instance->stepPerRev / (M_PI * instance->dRoues);

    TickType_t lastWake = xTaskGetTickCount();

    while (true) {

        // Si nouvelle consigne reçue
        if (xQueueReceive(instance->xQueue, &params, 0) == pdTRUE) {
            // conversion m/s → steps/s
            speedL = params.vitesseGauche * stepPerMeter;
            speedR = params.vitesseDroite * stepPerMeter;

            instance->moteurGauche.setSpeed(speedL);
            instance->moteurDroit.setSpeed(speedR);
        }

        // Exécute les steps
        instance->moteurGauche.runSpeed();
        instance->moteurDroit.runSpeed();

        // Mise à jour odométrie
        instance->UpdateOdometry();

        // Tick 1kHz
        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(1));
    }
}

void ClassMotors::GetPosition(float &x, float &y, float &angle) {
    if (xSemaphoreTake(posMutex, portMAX_DELAY) == pdTRUE) {
        x = x_pos;
        y = y_pos;
        angle = orientation;
        xSemaphoreGive(posMutex);
    }
}

void ClassMotors::UpdateOdometry() {
    // Lecture steps actuels
    long csL = moteurGauche.currentPosition();
    long csR = moteurDroit.currentPosition();

    // Delta depuis la dernière lecture
    long dL = csL - lastStepGauche;
    long dR = csR - lastStepDroit;

    // Si aucun mouvement → rien à mettre à jour
    if (dL == 0 && dR == 0) return;

    // Mise à jour mémoire
    lastStepGauche = csL;
    lastStepDroit  = csR;

    // Conversion step → mètres
    const float mPerStep = (M_PI * dRoues) / stepPerRev;

    float sL = dL * mPerStep;   // déplacement roue gauche en mètres
    float sR = dR * mPerStep;   // déplacement roue droite

    // Déplacement robot
    float ds = (sL + sR) / 2.0f;                     // déplacement moyen
    float dTheta = (sR - sL) / ecartRoues;           // rotation

    // LOCK MUTEX
    if (xSemaphoreTake(posMutex, portMAX_DELAY) == pdTRUE) {
        
        // Mise à jour orientation
        orientation += dTheta;

        // Normalisation angle [-π, π]
        if (orientation > M_PI)  orientation -= 2.0f * M_PI;
        if (orientation < -M_PI) orientation += 2.0f * M_PI;

        // Mise à jour position dans ton repère
        // x = avant ; y = gauche ; θ positif = gauche
        x_pos += ds * cosf(orientation);
        y_pos += ds * sinf(orientation);

        xSemaphoreGive(posMutex);
    }
}

