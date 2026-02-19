#include "ClassAscenseur.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>


void setup() {
    Serial.begin(115200);
    Serial.println("TEST ASCENSEUR UNITAIRE");
    delay(1000);
    ClassAscenseur ascenseur(ASC_4_STP, ASC_4_DIR, ASC_4_INV);
    Serial.println("---INITIALISATION DE L'ASCENSEUR----");
    ascenseur.Init(ASC_4_SNS, MM_PER_REV);
    delay(1000);
    Serial.println("---HOMING DE L'ASCENSEUR----");
    ascenseur.StartHoming();
    delay(1000);
    Serial.println("---ASCENSEUR READY----");
    ascenseur.StandardOp(10, 4096, 2);

    delay(3000);
    ascenseur.MoveToHeight(12.5);
    delay(3000);
    ascenseur.MoveToHeight(-25.0);
}

void loop(){}

