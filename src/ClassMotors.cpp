#include "ClassMotors.hpp"

ClassMotors *ClassMotors::instancePtr = nullptr;

ClassMotors::ClassMotors()
    : moteurGauche(AccelStepper::DRIVER, MOTOR_LEFT_STEP_PIN,
                   MOTOR_LEFT_DIR_PIN),
      moteurDroit(AccelStepper::DRIVER, MOTOR_RIGHT_STEP_PIN,
                  MOTOR_RIGHT_DIR_PIN) {
  // Setup queue (1 slot = overwrite)
  xQueue = xQueueCreate(1, sizeof(TaskParams));

  // Odométrie
  posMutex = xSemaphoreCreateMutex();
  x_pos = 0;
  y_pos = 0;
  orientation = 0;
  lastStepGauche = 0;
  lastStepDroit = 0;

  // Grande vitesse max, aucun frein logiciel
  moteurGauche.setMaxSpeed(50000);
  moteurDroit.setMaxSpeed(50000);
  instancePtr = this;
}

void ClassMotors::StartMotors() {
  xTaskCreatePinnedToCore(vMotors, "vMotors", 8000, this, 2, &vMotorsHandle, 0);
  timer = timerBegin(0, 80, true);
  timerAttachInterrupt(timer, &ClassMotors::onTimer, true);
  timerAlarmWrite(timer, 50, true);
  timerAlarmEnable(timer);
}

void ClassMotors::EnvoyerVitesse(TaskParams *params) {
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
  lastStepDroit = 0;
}

void IRAM_ATTR ClassMotors::onTimer() {
  if (instancePtr == nullptr)
    return;

  instancePtr->moteurGauche.runSpeed();
  instancePtr->moteurDroit.runSpeed();
}

void ClassMotors::vMotors(void *pvParameters) {
  ClassMotors *instance = (ClassMotors *)pvParameters;

  TaskParams params;

  // Vitesses cibles demandées par la stratégie (steps/s)
  float targetSpeedL = 0;
  float targetSpeedR = 0;

  // Vitesses actuelles réelles (steps/s)
  float actualSpeedL = 0;
  float actualSpeedR = 0;

  const float stepPerMeter = instance->stepPerRev / (M_PI * instance->dRoues);

  // Calcul de l'accélération max par milliseconde (Δv max par tick de 1ms)
  // ACCEL_MM_S2 est en mm/s^2. En m/s^2 c'est ACCEL_MM_S2 / 1000.
  // L'accélération en steps/s^2 est (ACCEL_MM_S2 / 1000) * stepPerMeter.
  // L'accélération en steps/s par milliseconde (dt = 0.001s) est donc :
  const float maxAccelPerMs = (ACCEL_MM_S2 / 1000.0f) * stepPerMeter * 0.001f;

  TickType_t lastWake = xTaskGetTickCount();

  while (true) {

    // 1. Lire la nouvelle consigne SI DISPONIBLE
    if (xQueueReceive(instance->xQueue, &params, 0) == pdTRUE) {
      targetSpeedL = params.vitesseGauche * stepPerMeter;
      targetSpeedR = params.vitesseDroite * stepPerMeter;
    }

    // 2. Rampe d'accélération (Slew Rate Limiter) - Moteur Gauche
    if (actualSpeedL < targetSpeedL) {
      actualSpeedL += maxAccelPerMs;
      if (actualSpeedL > targetSpeedL)
        actualSpeedL = targetSpeedL;
    } else if (actualSpeedL > targetSpeedL) {
      actualSpeedL -= maxAccelPerMs;
      if (actualSpeedL < targetSpeedL)
        actualSpeedL = targetSpeedL;
    }

    // 3. Rampe d'accélération - Moteur Droit
    if (actualSpeedR < targetSpeedR) {
      actualSpeedR += maxAccelPerMs;
      if (actualSpeedR > targetSpeedR)
        actualSpeedR = targetSpeedR;
    } else if (actualSpeedR > targetSpeedR) {
      actualSpeedR -= maxAccelPerMs;
      if (actualSpeedR < targetSpeedR)
        actualSpeedR = targetSpeedR;
    }

    // 4. Appliquer les vitesses profilées aux moteurs
    instance->moteurGauche.setSpeed(actualSpeedL);
    instance->moteurDroit.setSpeed(actualSpeedR);

    // Mise à jour odométrie
    instance->UpdateOdometry();

    // Tick 1kHz (Précis grâce à vTaskDelayUntil)
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
  if (dL == 0 && dR == 0)
    return;

  // Mise à jour mémoire
  lastStepGauche = csL;
  lastStepDroit = csR;

  // Conversion step → mètres
  const float mPerStep = (M_PI * dRoues) / stepPerRev;

  float sL = dL * mPerStep; // déplacement roue gauche en mètres
  float sR = dR * mPerStep; // déplacement roue droite

  // Déplacement robot
  float ds = (sL + sR) / 2.0f;           // déplacement moyen
  float dTheta = (sR - sL) / ecartRoues; // rotation

  // LOCK MUTEX
  if (xSemaphoreTake(posMutex, portMAX_DELAY) == pdTRUE) {

    // Mise à jour orientation
    orientation += dTheta;

    // Normalisation angle [-π, π]
    if (orientation > M_PI)
      orientation -= 2.0f * M_PI;
    if (orientation < -M_PI)
      orientation += 2.0f * M_PI;

    // Mise à jour position dans ton repère
    // x = avant ; y = gauche ; θ positif = gauche
    x_pos += ds * cosf(orientation);
    y_pos += ds * sinf(orientation);

    xSemaphoreGive(posMutex);
  }
}
