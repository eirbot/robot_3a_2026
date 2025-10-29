#pragma once
#include <Arduino.h>

struct Servo42C_Status {
    int32_t position;   // ticks absolus (encodeur)
    int16_t speed;      // rpm actuel
    int8_t  state;      // état du moteur
};

class Servo42C {
public:
    Servo42C(const char* name, HardwareSerial& serial, int addr = 0x80);

    void begin(uint32_t baud = 115200);
    void setSpeedRPM(int16_t rpm);
    void enable(bool on);
    void stop();

    bool readStatus(Servo42C_Status& out); // Lecture télémétrie (true si réponse reçue)

private:
    void sendPacket(uint8_t cmd, const uint8_t* data, uint8_t len);
    void buildPacket(uint8_t cmd, const uint8_t* data, uint8_t len, uint8_t* out, uint8_t& outlen);
    bool readResponse(uint8_t* buf, uint8_t len, uint32_t timeout);

    const char* _name;
    HardwareSerial& _serial;
    int _addr;
};
