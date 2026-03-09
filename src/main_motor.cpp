// #include <TMC2100.h>
#include <BasicStepperDriver.h>

#define STEPS 1600
#define STEP_PIN 4
#define DIR_PIN 2



BasicStepperDriver stepper(STEPS, DIR_PIN, STEP_PIN);

void setup() {
  stepper.setRPM(120);
  stepper.begin();
}

void loop() {
  // Rotate one revolution clockwise
  stepper.move(360);
  delay(2000);

  // Rotate one revolution counter-clockwise
  stepper.move(-360);
  delay(2000);
}

