#include <Arduino.h>
#include "Actionneur.hpp"

Actionneur actionneurs;

void setup() {
    Serial.begin(115200);
    
    // Attendre que le port série soit prêt
    while (!Serial) {
      vTaskDelay(pdMS_TO_TICKS(100)); // attente
    }
    
    actionneurs.Init();
}

void loop() {
    if (actionneurs.AreAllReady()) {
        Serial.println("Tous les actionneurs prêts !");
    } else {
        Serial.println("Mouvement en cours...");
    }

    vTaskDelay(pdMS_TO_TICKS(500));
}