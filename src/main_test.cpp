#include "Arduino.h"
#include "ClassMotors.hpp"
#include "utilities.hpp"

// #define STEP 17
// #define DIR 16
#define EN_Motor 21
#define BAUD_PI 115200


ClassMotors motors;

// Géométrie robot (cohérente avec ClassMotors)
constexpr float WHEEL_BASE = 0.22f; // m

// Tâches
void taskControl(void* arg);
void taskSerialRx(void* arg);
void taskSerialTx(void* arg);


void setup() {
    Serial.begin(BAUD_PI);
    delay(500);
    Serial.println("ESP32 Trajectory + Motors ready");

    pinMode(EN_Motor, OUTPUT);
    digitalWrite(EN_Motor ,HIGH);

    motors.StartMotors();
}

void loop() {

  TaskParams Params;

  Params.vitesseDroite = 0.5;
  Params.vitesseGauche = 0.5;
  motors.EnvoyerVitesse(&Params);
  Serial.print("1 tour XD");
  delay(3000);
  Params.vitesseDroite = 0.2;
  Params.vitesseGauche = 0.0;
  motors.EnvoyerVitesse(&Params);
  delay(3000);
}
