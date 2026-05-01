#include "main_robot.h"

TaskHandle_t vstratHandle = NULL;
TaskHandle_t vterminal_bluetoothHandle = NULL;

unsigned long startMillis;

TaskParams Parameters = {0, 0, 0, 0};

GoToPosition serialGoto{X_POS_INIT, Y_POS_INIT, ANGLE_INIT, 1000, 1000, 0};

void setup() {
  esp_task_wdt_init(10, true);
  static ComWithRasp comRasp;

  // Config des vitesses max et accélérations
  moteurGauche.setMaxSpeed(SPEEDMAX);
  moteurGauche.setAcceleration(ACCELMAX);
  moteurDroit.setCurrentPosition(0);

  moteurDroit.setMaxSpeed(SPEEDMAX);
  moteurDroit.setAcceleration(ACCELMAX);
  moteurGauche.setCurrentPosition(0);

  xPositionMutex = xSemaphoreCreateMutex();
  if (xPositionMutex == NULL) {
    // Serial.println("Erreur : mutex non créé");
  }

  Serial.begin(115200);
  startMillis = millis();

  Serial.println("Démarrage du robot...");
  mot.StartMotors();

  Serial.println("Démarrage de la communication avec la Raspberry Pi...");
  
  comRasp.StartCom();
  comRasp.StartTelemetry();
}

void loop() {
}
