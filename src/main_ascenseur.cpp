#include "ClassAscenseur.hpp"

// PIN CONFIG 
// Change according to your wiring
#define STEP_PIN 16
#define DIR_PIN  17
#define CAPTEUR_PIN  5

// mm per motor revolution (lead screw pitch, pulley, etc.)
#define MM_PER_REV   8.0
#define STEP_PER_REV 1600// 200 = 1.8° stepper (full step) // Homing config #define HOMING_SPEED_MM_S 20 #define HOMING_BACKOFF_MM 5 #define ACCEL_MM_S2 50 // Max speed config #define MAX_SPEED_MM_S 100
ClassAscenseur ascenseur;

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("TEST ASCENSEUR");

    // Init elevator
    ascenseur.Init(STEP_PIN, DIR_PIN, CAPTEUR_PIN, MM_PER_REV, 1);

    delay(3000);

    // on s'attend à "[WARN] Ascenseur non calibré !"
    vTaskDelay(pdMS_TO_TICKS(2000));

    // test 2 : homing
    Serial.println("Homing");
    ascenseur.StartHoming();
    delay(2000);
    Serial.println("----------------");

}
int k = 0;
void loop() {
    if(k == 0){
    // test 1 : verifie que la commande est rejetée si homing n'as pas été réalisé
    Serial.println("Test 1 : Commande");
    ascenseur.MoveToHeight(25.0f);
    k++; }
}

