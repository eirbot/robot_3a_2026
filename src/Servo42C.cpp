#include "Servo42C.hpp"

Servo42C::Servo42C(const char* name, HardwareSerial& serial, int addr)
    : _name(name), _serial(serial), _addr(addr) {}

void Servo42C::begin(uint32_t baud) {
    _serial.begin(baud);
    delay(100);
}

// ===== Commandes =====
void Servo42C::buildPacket(uint8_t cmd, const uint8_t* data, uint8_t len, uint8_t* out, uint8_t& outlen) {
    out[0] = 0x3E;
    out[1] = _addr;
    out[2] = cmd;
    for (uint8_t i = 0; i < len; i++) out[3 + i] = data[i];
    uint8_t sum = 0;
    for (uint8_t i = 0; i < 3 + len; i++) sum += out[i];
    out[3 + len] = 0xFF - sum;
    outlen = 4 + len;
}

void Servo42C::sendPacket(uint8_t cmd, const uint8_t* data, uint8_t len) {
    uint8_t buf[16];
    uint8_t outlen;
    buildPacket(cmd, data, len, buf, outlen);
    _serial.write(buf, outlen);
}

void Servo42C::setSpeedRPM(int16_t rpm) {
    uint8_t data[2];
    data[0] = rpm & 0xFF;
    data[1] = (rpm >> 8) & 0xFF;
    sendPacket(0xA2, data, 2);
}

void Servo42C::enable(bool on) {
    uint8_t val = on ? 1 : 0;
    sendPacket(0xF3, &val, 1);
}

void Servo42C::stop() {
    setSpeedRPM(0);
}

// ===== Lecture statut (encodeur / vitesse) =====
bool Servo42C::readStatus(Servo42C_Status& out) {
    sendPacket(0x9C, nullptr, 0);
    uint8_t buf[16];
    if (!readResponse(buf, 13, 50)) return false;

    // format : 0x3E addr 0x9C + data[8] + checksum
    out.position = (int32_t)((buf[5] << 24) | (buf[6] << 16) | (buf[7] << 8) | buf[8]);
    out.speed    = (int16_t)((buf[9] << 8) | buf[10]);
    out.state    = buf[11];
    return true;
}

bool Servo42C::readResponse(uint8_t* buf, uint8_t len, uint32_t timeout) {
    uint32_t start = millis();
    uint8_t i = 0;
    while ((millis() - start) < timeout) {
        if (_serial.available()) {
            buf[i++] = _serial.read();
            if (i >= len) return true;
        }
    }
    return false;
}
