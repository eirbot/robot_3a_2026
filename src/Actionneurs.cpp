#include "Arduino.h"
#include "PCF8575.h"  // Bibliothèque de Rob Tillaart
#include "GpioActionneurs.hpp"
#include <ESP32Servo.h>

PCF8575 pcf(0x20, &Wire); 

struct Actionneur {
  uint8_t p9G, p17G, v1, v2, stp, dir, sns;
  Servo servo9G, servo17G;
  bool canMove;
  int sns_status;

  void initialiser() {
    pcf.setButtonMask(bit(sns));
    
    pinMode(stp, OUTPUT);
    servo9G.attach(p9G);
    servo17G.attach(p17G);
    
    canMove = true;
    sns_status = 0;
  }

  void sns_read(){
    sns_status = pcf.read(sns);
    canMove = (sns_status == LOW); 
  }

  void commander(bool On) {
    if(sns_status == HIGH) { 
      pcf.write(v1, LOW);
      pcf.write(v2, LOW);
      pcf.write(dir, LOW);
      servo9G.write(0);
      servo17G.write(90);
      canMove = false;
    } else {
      canMove = true;
      pcf.write(v1, On ? HIGH : LOW);
      pcf.write(v2, On ? LOW : HIGH);
      pcf.write(dir, On ? LOW : HIGH);
      servo9G.write(On ? 0 : 180);
      servo17G.write(On ? 90 : 90);
    }
  }

  void homming(){
    pcf.write(dir, LOW);
    unsigned long hommingBegging = micros();
    unsigned long hommingTimer = hommingBegging;
    unsigned long snsTimer = hommingBegging;
    unsigned long now = hommingBegging;
    while(now - hommingBegging <=5000000){
      if(now - hommingTimer >= 500){
        this->fairePas();
        hommingTimer = micros();
      }
      if(now - snsTimer >= 110000){
        this->sns_read();
        snsTimer = micros();
      }
      now = micros();

      if(sns_status){
        break;
      }
    }
  }

  void fairePas() {
    if (canMove) {
      digitalWrite(stp, !digitalRead(stp));
    }
  }
};

Actionneur act1 = {ServoE, ServoF, Verin31EXT, Verin32EXT, asc1_stp, asc1_dirEXT, sns_asc_1EXT};
Actionneur act2 = {ServoA, ServoB, Verin11EXT, Verin12EXT, asc2_stp, asc2_dirEXT, sns_asc_2EXT};
Actionneur act3 = {ServoC, ServoD, Verin21EXT, Verin22EXT, asc3_stp, asc3_dirEXT, sns_asc_3EXT};
Actionneur act4 = {ServoG, ServoH, Verin41EXT, Verin42EXT, asc4_stp, asc4_dirEXT, sns_asc_4EXT};

void setup() {
  Serial.begin(115200);
  
  Wire.begin(21, 22); 
  Wire.setClock(100000);

  if (!pcf.begin()) {
    Serial.println("PCF8575 introuvable");
    while (1);
  }

  act1.initialiser();
  act2.initialiser();
  act3.initialiser();
  act4.initialiser();

  Serial.println("Systeme pret.");

  act4.homming();
}

unsigned long SlowLoopTime = 0;
bool SlowLoopPhase = true;
unsigned long stepperTimer = 0;
unsigned long snsTimer = 0;

void loop() {
//   // Changement d'état toutes les secondes
//   if(millis() - SlowLoopTime >= 1000){
//     act2.commander(SlowLoopPhase);
//     act1.commander(SlowLoopPhase);
//     SlowLoopPhase = !SlowLoopPhase;
//     SlowLoopTime = millis();
//   }
  
//   // Génération des pas (Square wave)
//   if(micros() - stepperTimer >= 500) {
//     act2.fairePas();
//     act1.fairePas();
//     stepperTimer = micros();
//   }

//   if(millis() - snsTimer >= 15) {
//     act2.sns_read();
//     act1.sns_read();
//     snsTimer = millis();
//   }
}