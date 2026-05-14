#include "Actionneurs.hpp"
#include "ComWithRaspActionneurs.hpp"

static ComWithRasp comRasp;

void readAllSns(){
  act1.sns_read();
  act2.sns_read();
  act3.sns_read();
  act4.sns_read();
  IntDetected = false;
}

void setup() {

  Serial.begin(115200);

  Wire.begin(21, 22); 
  Wire.setClock(100000);

  if (!pcf.begin()) {
    Serial.println("PCF8575 introuvable");
    while (1);
  }

  pinMode(IntEXT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(IntEXT), IntEXTfct, FALLING);

  startActionneurTask();

  comRasp.StartCom();

}

void loop() {}