#include <Arduino.h>
#include "Actionneur.hpp"

Servo monServo;          // Création de l’objet Servo
const int pinServo = 27; // Broche PWM du signal servo

void setup() {
    Serial.begin(115200);
    Serial.println("Démo Servo ESP32 - ESP32Servo");

    // Initialisation du PWM pour les servos
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);

    // Configuration de la fréquence PWM du servo (50 Hz)
    monServo.setPeriodHertz(50);

    // Attache du servo à la broche avec les valeurs min/max d’impulsions (en µs)
    monServo.attach(pinServo, 500, 2400); // 0° → 500µs / 180° → 2400µs

    monServo.write(90); // Position initiale (milieu)
    delay(1000);
}

void loop() {
  Serial.println("Aller de 0° à 180°");
  for (int angle = 0; angle <= 180; angle++) {
    monServo.write(angle);
    delay(15);
  }

  Serial.println("Retour de 180° à 0°");
  for (int angle = 180; angle >= 0; angle--) {
    monServo.write(angle);
    delay(15);
  }

  delay(500);
}