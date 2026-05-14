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

void decode(String cmd, std::vector<int> params){
  if (cmd == "G" && params.size() == 1) {
    if((int)params[0]==1){
      act1.closePiston();
    } else if((int)params[0]==2) {
      act2.closePiston();
    } else if((int)params[0]==3) {
      act3.closePiston();
    } else if((int)params[0]==4) {
      act4.closePiston();
    }
  } else if (cmd == "R" && params.size() == 1) {
    if((int)params[0]==1){
      act1.openPiston();
    } else if((int)params[0]==2) {
      act2.openPiston();
    } else if((int)params[0]==3) {
      act3.openPiston();
    } else if((int)params[0]==4) {
      act4.openPiston();
    }
  } else if (cmd == "T" && params.size() == 1) {
    if((int)params[0]==1){
      if(act1.p9G_status == 0){
        act1.servo_9G(180);
        act1.p9G_status = 180;
      }
      else{
        act1.servo_9G(0);
        act1.p9G_status = 0;
      }
    } else if((int)params[0]==2) {
      if(act2.p9G_status == 0){
        act2.servo_9G(180);
        act2.p9G_status = 180;
      }
      else{
        act2.servo_9G(0);
        act2.p9G_status = 0;
      }
    } else if((int)params[0]==3) {
      if(act3.p9G_status == 0){
        act3.servo_9G(180);
        act3.p9G_status = 180;
      }
      else{
        act3.servo_9G(0);
        act3.p9G_status = 0;
      }
    } else if((int)params[0]==4) {
      if(act4.p9G_status == 0){
        act4.servo_9G(180);
        act4.p9G_status = 180;
      }
      else{
        act4.servo_9G(0);
        act4.p9G_status = 0;
      }
    }
  } else if (cmd == "P" && params.size() == 2) {
    if((int)params[0]==1){
      int angle = 90;
      if((int)params[1] == 1){
        angle = 40;
      }
      act1.soft_servo(angle);
    }
    if((int)params[0]==2){
      int angle = 90;
      if((int)params[1] == 1){
        angle = 60;
      }
      act2.soft_servo(angle);
    }
    if((int)params[0]==3){
      int angle = 90;
      if((int)params[1] == 1){
        angle = 120;
      }
      act3.soft_servo(angle);
    }
    if((int)params[0]==4){
      int angle = 90;
      if((int)params[1] == 1){
        angle = 140;
      }
      act4.soft_servo(angle);
    }
  } else if (cmd == "A" && params.size() == 2) {
    Serial.println("SetPos");
    int mmToStep =80;
    int asked_height = (int)params[1]* mmToStep;
    if((int)params[0]==1){
      if(asked_height - act1.asc_height >=0){
        act1.goUp(asked_height - act1.asc_height);
      }
      else{
        act1.goDown(act1.asc_height - asked_height);
      }
      act1.asc_height = asked_height;
    }
    else if((int)params[0]==2){
      if(asked_height - act2.asc_height >=0){
        act2.goUp(asked_height - act2.asc_height);
      }
      else{
        act2.goDown(act2.asc_height - asked_height);
      }
      act2.asc_height = asked_height;
    }
    else if((int)params[0]==3){
      if(asked_height - act3.asc_height >=0){
        act3.goUp(asked_height - act3.asc_height);
      }
      else{
        act3.goDown(act3.asc_height - asked_height);
      }
      act3.asc_height = asked_height;
    }
    else if((int)params[0]==4){
      if(asked_height - act4.asc_height >=0){
        act4.goUp(asked_height - act4.asc_height);
      }
      else{
        act4.goDown(act4.asc_height - asked_height);
      }
      act4.asc_height = asked_height;
    }
    
  } else if (cmd == "I") {
    Serial.println("init_robot");
    act2.homming();
    act3.homming();
    act1.homming();
    act4.homming();

  } else {
  }
}

void setup() {

  iReadBuffer = 0;
  iWriteBuffer = 0;

  Serial.begin(115200);
  
  Wire.begin(21, 22); 
  Wire.setClock(100000);

  if (pcf.begin()) {
    Serial.println("PCF8575 trouvé");

    act1.initialiser();
    act2.initialiser();
    act3.initialiser();
    act4.initialiser();

    pinMode(IntEXT, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(IntEXT), IntEXTfct, FALLING);

  }

  comRasp.StartCom();
}

void loop() {
  if(iReadBuffer< iWriteBuffer){
    Serial.println(BufferCommands[iReadBuffer%BufferSize].cmd);
    decode(
      BufferCommands[iReadBuffer%BufferSize].cmd, 
      BufferCommands[iReadBuffer%BufferSize].params
    );
    iReadBuffer+=1;
  }
}