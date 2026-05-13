#include "Arduino.h"
#include "PCF8575.h"  // Bibliothèque de Rob Tillaart
#include "GpioActionneurs.hpp"
#include <ESP32Servo.h>
#include "ComWithRaspActionneurs.hpp"

PCF8575 pcf(0x20, &Wire);

volatile bool IntDetected = false; 

struct Actionneur {
  uint8_t p9G, p17G, v1, v2, stp, dir, sns;
  bool dir_elevator;
  Servo servo9G, servo17G;
  bool canMove;
  int sns_status;
  int p17G_status;

  void initialiser() {
    pcf.setButtonMask(bit(sns));
    
    pinMode(stp, OUTPUT);
    servo9G.attach(p9G);
    servo17G.attach(p17G);
    
    canMove = true;
    sns_status = 0;
    p17G_status = 89;
  }

  void sns_read(){
    sns_status = pcf.read(sns);
    canMove = (sns_status == LOW); 
  }

  void servo_9G(int angle){
    servo9G.write(angle);
  }

  void soft_servo(int objectif){
    while(abs(objectif-p17G_status)>=1){
      if(objectif-p17G_status >= 0 ){
        p17G_status += 1;
      }
      else{
        p17G_status -= 1;
      }
      servo17G.write(p17G_status);
      delay(10);
    }
  }

  void homming(){
    pcf.write(dir, dir_elevator ? HIGH : LOW);
    soft_servo(90);
    this->goDown(10000);

    pcf.write(dir, dir_elevator ? LOW : HIGH);
    canMove = true;
    this->goUp(1000);
  }

  void fairePas() {
    if (canMove) {
      digitalWrite(stp, !digitalRead(stp));
    }
  }

  void closePiston(){
    pcf.write(v1, HIGH);
    pcf.write(v2, LOW);
  }

  void openPiston(){
    pcf.write(v1, LOW);
    pcf.write(v2, HIGH);
  }

  void goUp(int steps){
    pcf.write(dir, dir_elevator ? LOW : HIGH);
    canMove = true;
    for(int k =0; k<steps; k++){
        this->fairePas();
        delayMicroseconds(80);
      }
  }

  void goDown(int steps){
    pcf.write(dir, dir_elevator ? HIGH : LOW);
    canMove = true;
    sns_read();
    if(sns_status==LOW){
      for(int k =0; k<steps; k++){
        this->fairePas();
        delayMicroseconds(50);
        if(IntDetected){
          sns_read();
          IntDetected = false;
        }
        if(sns_status==HIGH){
          break;
        }
      }
    }
  }

  void grab(){
    this->openPiston();
    delay(1000);
    this->goDown(10000);
    this->closePiston();
    delay(2000);
    this->goUp(3000);
  }
};

Actionneur act1 = {ServoE, ServoF, Verin31EXT, Verin32EXT, asc1_stp, asc1_dirEXT, sns_asc_1EXT, true};
Actionneur act2 = {ServoA, ServoB, Verin11EXT, Verin12EXT, asc2_stp, asc2_dirEXT, sns_asc_2EXT, false};
Actionneur act3 = {ServoC, ServoD, Verin21EXT, Verin22EXT, asc3_stp, asc3_dirEXT, sns_asc_3EXT, false};
Actionneur act4 = {ServoG, ServoH, Verin41EXT, Verin42EXT, asc4_stp, asc4_dirEXT, sns_asc_4EXT, false};

void demo(){
  act1.soft_servo(40);
  act4.soft_servo(140);
  act2.soft_servo(60);
  act3.soft_servo(120);

  act2.soft_servo(90);
  act3.soft_servo(90);
  act1.soft_servo(90);
  act4.soft_servo(90);

  act1.closePiston();
  act2.closePiston();
  act3.closePiston();
  act4.closePiston();

  act1.goUp(5000);
  act2.goUp(5000);
  act3.goUp(5000);
  act4.goUp(5000);

  act1.grab();
  act2.grab();
  act3.grab();
  act4.grab();

  act1.soft_servo(40);
  act4.soft_servo(140);
  act2.soft_servo(60);
  act3.soft_servo(120);

  act1.servo_9G(180);
  act2.servo_9G(180);
  act3.servo_9G(180);
  act4.servo_9G(180);

  delay(1000);

  act1.servo_9G(0);
  act2.servo_9G(0);
  act3.servo_9G(0);
  act4.servo_9G(0);

  act2.soft_servo(90);
  act3.soft_servo(90);
  act1.soft_servo(90);
  act4.soft_servo(90);
}

void ARDUINO_ISR_ATTR IntEXTfct() {
  IntDetected = true;
}

void readAllSns(){
  act1.sns_read();
  act2.sns_read();
  act3.sns_read();
  act4.sns_read();
  IntDetected = false;
}

void setup() {
  static ComWithRasp comRasp;

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

  pinMode(IntEXT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(IntEXT), IntEXTfct, FALLING);

  comRasp.StartCom();

  act1.homming();
  act2.homming();
  act3.homming();
  act4.homming();
}

unsigned long SlowLoopTime = 0;
bool SlowLoopPhase = true;
unsigned long stepperTimer = 0;
unsigned long snsTimer = 0;

void loop() {
  // if (IntDetected) {
  //   Serial.println("Signal détecté !");
  //   IntDetected = false;
  // }
  

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