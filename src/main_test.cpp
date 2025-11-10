#include "Arduino.h"
#include "ClassMotors.hpp"

// #define STEP 17
// #define DIR 16
#define EN 21

void setup() {
  Serial.begin(9600);
  // pinMode(STEP,OUTPUT);
  // pinMode(DIR,OUTPUT);
  pinMode(EN,OUTPUT);
  mot.StartMotors();
}

void loop() {
  // digitalWrite(EN, HIGH);
  // digitalWrite(DIR, HIGH);
  // for(int k=0;k<100;k++){
  //   digitalWrite(STEP,HIGH);
  //   ets_delay_us(10);
  //   digitalWrite(STEP,LOW);
  //   Serial.println("1tour");
  //   ets_delay_us(10);
  // }

  TaskParams Params;

  int r=100;

  Params = {(int)r, 0, 0, SPEEDMAX};
  mot.EnvoyerDonnees(&Params);
  mot.WaitUntilDone();
  delay(3000);
}
