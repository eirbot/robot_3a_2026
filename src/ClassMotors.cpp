#include "ClassMotors.hpp"

ClassMotors::ClassMotors() {
  xQueue = xQueueCreate(30, sizeof(TaskParams));
  xQueueBuffer = xQueueCreate(30, sizeof(TaskParams));
}

void ClassMotors::vMotors(void *pvParameters) {
  ClassMotors *instance = (ClassMotors *)pvParameters;
  TaskParams taskParams;
  int steps = 0;

  // Gestion des arrets
  const TickType_t maxIdleTime = pdMS_TO_TICKS(5000); // 5000 ms = 5 secondes
  TickType_t stopStartTime = 0;
  bool wasStopped = false;

  while (1) {
    if (xQueueReceive(instance->xQueue, &taskParams, portMAX_DELAY) == pdPASS) {

      TickType_t lastOdoUpdate = xTaskGetTickCount();

      float speed = (taskParams.vitesse * stepPerRev) / ((M_PI * dRoues));
      float accel = speed * 0.6;
      moteurGauche.setMaxSpeed(speed);
      moteurGauche.setAcceleration(accel);
      moteurDroit.setMaxSpeed(speed);
      moteurDroit.setAcceleration(accel);

      instance->currentStep = moteurGauche.currentPosition();

      if (taskParams.angle == 0 && taskParams.distance == 0) {

      } else if (taskParams.angle == 0) { // Pour avancer
        steps = (int)((taskParams.distance / (M_PI * dRoues)) * stepPerRev);
        instance->stepDid = 0;

        moteurGauche.move(steps); // steps negatif pour reculer
        moteurDroit.move(steps);

        int antiCrashCounter = 0;

        while (moteurGauche.distanceToGo() != 0 ||
               moteurDroit.distanceToGo() != 0) { // Gooo

          // Si FLAG_STOP est actif
          if (!LiDAR_state) {
            if (!wasStopped) {
              // Ralentissement progressif avec mise à jour odométrie en temps réel
              StopStepper(moteurGauche, moteurDroit, instance);

              // On met à jour l'odométrie juste après le freinage pour avoir la
              // position exacte de pause
              instance->UpdateOdometry();

              stopStartTime =
                  xTaskGetTickCount(); // Première fois qu'on détecte l'arrêt
              wasStopped = true;

              instance->stepDid =
                  moteurGauche.currentPosition() - instance->GetCurrentStep();
              instance->distanceDid =
                  (instance->GetStepDid() * M_PI * dRoues) / stepPerRev;

              float remainingSteps = steps - instance->stepDid;
              moteurGauche.setAcceleration(accel);
              moteurDroit.setAcceleration(accel);

              moteurGauche.move(remainingSteps);
              moteurDroit.move(remainingSteps);

            } else if ((xTaskGetTickCount() - stopStartTime) > maxIdleTime) {
              wasStopped = false; // Remet à zéro après vidage
              FLAG_STOP = true;

              instance->stepDid =
                  moteurGauche.currentPosition() - instance->GetCurrentStep();
              instance->distanceDid =
                  (instance->GetStepDid() * M_PI * dRoues) / stepPerRev;

              instance->TransferQueueBuffer();
              
              // On annule le mouvement restant pour que distanceToGo() devienne 0
              // Sinon WaitUntilDone() bloque indéfiniment !
              moteurGauche.move(0);
              moteurDroit.move(0);

              break; // sort de la boucle de mouvement
            }
          } else {
            if (wasStopped) {
              wasStopped = false;
            }

            moteurGauche.run();
            moteurDroit.run();

            if ((xTaskGetTickCount() - lastOdoUpdate) >= odoInterval) {
              instance->UpdateOdometry();
              lastOdoUpdate = xTaskGetTickCount();
            }
          }
          antiCrashCounter++;
          if (antiCrashCounter > 3000) {
            taskYIELD();
            antiCrashCounter = 0;
          }
        }

        // S'assurer que les tout derniers pas sont comptabilisés à la fin du
        // mouvement
        instance->UpdateOdometry();

      } else if (taskParams.distance == 0) { // Pour tourner
        steps = (int)((std::abs(taskParams.angle) / 360.0) *
                      (M_PI * ecartRoues) * stepPerRev / (M_PI * dRoues));
        instance->stepDid = steps;

        if (taskParams.direction == 0) { // 0 droite, 1 gauche
          moteurGauche.move(steps);
          moteurDroit.move(-steps);
        } else {
          moteurGauche.move(-steps);
          moteurDroit.move(steps);
        }

        while (moteurGauche.distanceToGo() != 0 ||
               moteurDroit.distanceToGo() != 0) { // Goooo
          moteurGauche.run();
          moteurDroit.run();

          if ((xTaskGetTickCount() - lastOdoUpdate) >= odoInterval) {
            instance->UpdateOdometry();
            lastOdoUpdate = xTaskGetTickCount();
          }
        }

        // S'assurer que les tout derniers pas de la rotation sont comptabilisés
        instance->UpdateOdometry();

      } else {
      }
      vTaskDelay(10);
    }
  }
}

void ClassMotors::StartMotors() {
  xTaskCreatePinnedToCore(vMotors, "vMotors", 10000, this, 1, &vMotorsHandle,
                          1);
}

void ClassMotors::EnvoyerDonnees(void *Params) {
  TaskParams *ptaskParams =
      (TaskParams *)(Params); // Merci au patron de l'année derrnière en dépit
                              // de ses maigres performances concernant la coupe
  xQueueSend(xQueue, ptaskParams, portMAX_DELAY);
}

void ClassMotors::WaitUntilDone() {
  // On attend que la file soit vide ET que les moteurs soient à l'arrêt
  while (uxQueueMessagesWaiting(xQueue) > 0 ||
         moteurGauche.distanceToGo() != 0 || moteurDroit.distanceToGo() != 0) {
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void ClassMotors::TransferQueueBuffer() {
  TaskParams tmp;
  while (xQueueReceive(xQueue, &tmp, 0) == pdTRUE) {
    xQueueSend(xQueueBuffer, &tmp, 0); // Sauvegarde dans le tampon
  }
}

void ClassMotors::RestoreQueueBuffer() {
  TaskParams tmp;
  while (xQueueReceive(xQueueBuffer, &tmp, 0) == pdTRUE) {
    xQueueSend(xQueue, &tmp, 0); // Recharge
  }
}

void ClassMotors::Stop() {
  // Stopper les moteurs en douceur
  StopStepper(moteurGauche, moteurDroit, this);

  // Calculs de distance uniquement si un mouvement était actif
  if (GetCurrentStep() != 0) {
    stepDid = moteurGauche.currentPosition() - GetCurrentStep();
    distanceDid = (stepDid * M_PI * dRoues) / stepPerRev;
  } else {
    stepDid = 0;
    distanceDid = 0.0;
  }

  // Suspendre proprement la tâche de moteur (sécurité)
  if (vMotorsHandle != NULL) {
    vTaskSuspend(vMotorsHandle);
  }

  // Vider proprement la file de commandes
  UBaseType_t nbMessages = uxQueueMessagesWaiting(xQueue);
  TaskParams tmp;
  for (UBaseType_t i = 0; i < nbMessages; ++i) {
    xQueueReceive(xQueue, &tmp, 0);
  }

  // Reprendre la tâche
  if (vMotorsHandle != NULL) {
    vTaskResume(vMotorsHandle);
  }
}

void ClassMotors::RestartMotors() {
  if (vMotorsHandle != NULL) {
    vTaskResume(vMotorsHandle);
  }
}

void StopStepper(AccelStepper &moteur1, AccelStepper &moteur2, ClassMotors* instance) {
  moteur1.setAcceleration(DECCEL); // Ralentissement
  moteur2.setAcceleration(DECCEL); // Ralentissement

  moteur1.stop(); // Arrête le moteur
  moteur2.stop(); // Arrête le moteur
  
  TickType_t lastOdoUpdate = xTaskGetTickCount();
  
  while (moteur1.isRunning() || moteur2.isRunning()) {
    // On attend que les moteurs s'arrêtent
    moteur1.run();
    moteur2.run();
    
    if (instance != nullptr && (xTaskGetTickCount() - lastOdoUpdate) >= odoInterval) {
        instance->UpdateOdometry();
        lastOdoUpdate = xTaskGetTickCount();
    }
  }
  
  if (instance != nullptr) {
      instance->UpdateOdometry();
  }
  
  vTaskDelay(100);
}

void ClassMotors::GetPosition(float &x, float &y, float &angle) {
  if (xSemaphoreTake(xPositionMutex, portMAX_DELAY) == pdTRUE) {
    x = x_pos;
    y = y_pos;
    angle = orientation;
    xSemaphoreGive(xPositionMutex);
  }
}

void ClassMotors::SetPosition(float x, float y, float angle) {
  if (xSemaphoreTake(xPositionMutex, portMAX_DELAY) == pdTRUE) {
    x_pos = x;
    y_pos = y;
    orientation = angle;
    xSemaphoreGive(xPositionMutex);
  }
}

void ClassMotors::UpdateOdometry() {
  long currentStepGauche = moteurGauche.currentPosition();
  long currentStepDroit = moteurDroit.currentPosition();
  long deltaStepGauche = currentStepGauche - lastStepGauche;
  long deltaStepDroit = currentStepDroit - lastStepDroit;

  if (deltaStepGauche == 0 && deltaStepDroit == 0)
    return;

  lastStepGauche = currentStepGauche;
  lastStepDroit = currentStepDroit;

  float distanceParStep = (M_PI * dRoues) / stepPerRev;
  float s_L = deltaStepGauche * distanceParStep;
  float s_R = deltaStepDroit * distanceParStep;
  float delta_s = (s_R + s_L) / 2.0;
  float delta_theta = (s_R - s_L) / ecartRoues;

  // Optimisation : On fait les maths d'abord, on verrouille ensuite !
  if (xSemaphoreTake(xPositionMutex, portMAX_DELAY) == pdTRUE) {
    orientation += delta_theta;

    if (orientation > M_PI)
      orientation -= 2 * M_PI;
    if (orientation < -M_PI)
      orientation += 2 * M_PI;

    x_pos += delta_s * cos(orientation);
    y_pos += delta_s * sin(orientation);

    xSemaphoreGive(xPositionMutex);
  }
}
