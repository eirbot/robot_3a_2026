#include "Actionneurs.hpp"

PCF8575 pcf(0x20, &Wire);
volatile bool IntDetected = false;

void ARDUINO_ISR_ATTR IntEXTfct() {
  IntDetected = true;
}