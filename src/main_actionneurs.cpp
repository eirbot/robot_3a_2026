#include "Actionneurs.hpp"
#include "ComWithRaspActionneurs.hpp"

Actionneur act1 = {ServoE, ServoF, Verin31EXT, Verin32EXT, asc1_stp, asc1_dirEXT, sns_asc_1EXT, true};
Actionneur act2 = {ServoA, ServoB, Verin11EXT, Verin12EXT, asc2_stp, asc2_dirEXT, sns_asc_2EXT, false};
Actionneur act3 = {ServoC, ServoD, Verin21EXT, Verin22EXT, asc3_stp, asc3_dirEXT, sns_asc_3EXT, false};
Actionneur act4 = {ServoG, ServoH, Verin41EXT, Verin42EXT, asc4_stp, asc4_dirEXT, sns_asc_4EXT, false};

static ComWithRasp comRasp;

void readAllSns(){
  act1.sns_read();
  act2.sns_read();
  act3.sns_read();
  act4.sns_read();
  IntDetected = false;
}

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

  pinMode(IntEXT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(IntEXT), IntEXTfct, FALLING);

  comRasp.StartCom();

  act1.homming();
  act2.homming();
  act3.homming();
  act4.homming();
}

void loop() {
  if(comRasp.flagInit){
    Serial.println("flag recieved");
    act1.homming();
    act2.homming();
    act3.homming();
    act4.homming();
    comRasp.flagInit=false;
  }
}