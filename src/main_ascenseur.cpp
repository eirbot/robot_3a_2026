#include "ClassAscenseur.hpp"

// PIN CONFIG 
// Change according to your wiring
#define STEP_PIN     26
#define DIR_PIN      27
#define CAPTEUR_PIN  14

// mm per motor revolution (lead screw pitch, pulley, etc.)
#define MM_PER_REV   8.0

ClassAscenseur ascenseur;

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("TEST ASCENSEUR");

    // Init elevator
    ascenseur.Init(STEP_PIN, DIR_PIN, CAPTEUR_PIN, MM_PER_REV);

}

void loop() {

    // test 1 : verifie que la commande est rejetée si homing n'as pas été réalisé
    Serial.println("Test 1 : Commande sans homing");
    ascenseur.MoveToHeight(50);
    // on s'attend à "[WARN] Ascenseur non calibré !"
    vTaskDelay(pdMS_TO_TICKS(2000));

    // test 2 : homing
    Serial.println("Test 2 : Homing");
    ascenseur.StartHoming();
    // on s'attend à "[INFO] Démarrage homing..."
    // homing est bloquant

    // test 3 : commande après homing
    Serial.println("Test 3 : Commande après homing");
    ascenseur.MoveToHeight(50);
}
