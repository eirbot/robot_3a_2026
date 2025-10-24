#ifndef CLASS_ACTIONNEUR_HPP
#define CLASS_ACTIONNEUR_HPP

#include <Arduino.h>
#include <ESP32Servo.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "ClassAscenseur.hpp"

#define VERIN_SPEED_MAX_PWM 255
#define VERIN_SPEED_MAX_MM_S 50.0f

#define SERVO_FREQ_HZ   50
#define SERVO_MIN_US    500
#define SERVO_MAX_US    2400

// Commandes traitées par la task d'actionneur
enum class ActionneurCmdType : uint8_t {
    CMD_HOMING,
    CMD_MOVE_ASC,   // valeur: position mm
    CMD_SERVO_POS,  // valeur: angle ou position
    CMD_VERIN_EXT   // valeur: 0/1 pour rétracté/etendu
};

struct ActionneurCommand {
    ActionneurCmdType type;
    float value;   // usage dépend du type
    uint8_t channel; // si plusieurs servos/verins
};

class ClassActionneur {
public:
    ClassActionneur();
    ~ClassActionneur();
    void Init(int stepPin, int dirPin, int pinCapteur,
              int servoRotatePin, int servoOrientPin,
              int verinDirPin, int verinPWMPin);
    void StartTask();
    void StopTask();
    bool PostCommand(const ActionneurCommand& cmd);
    void StartHomingNonBlocking();

    // Etats actionneur
    bool IsReady();
    bool IsHomed();
    bool IsIdle();
    float GetHeight();
    bool IsElevatorBusy();

private:
    QueueHandle_t cmdQueue = NULL;
    TaskHandle_t taskHandle = NULL;
    static void vActionneurTask(void* pvParams);
    // === Sous-systèmes ===
    
    ClassAscenseur ascenseur;
    Servo servoRotate;
    Servo servoOrient;

    int verinDirPin;
    int verinPWMPin;
};

#endif
