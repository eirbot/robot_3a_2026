#include "Actionneur.hpp"

// === PINS À ADAPTER SELON TON CÂBLAGE ===

// --- Avant gauche ---
#define STEP_AG 2
#define DIR_AG 15
#define CAP_AG 33
#define SERVO_ROT_AG 22
#define SERVO_ORIENT_AG 23
#define VERIN_DIR_AG 25
#define VERIN_PWM_AG 26

// --- Avant droit ---
#define STEP_AD 4
#define DIR_AD 16
#define CAP_AD 32
#define SERVO_ROT_AD 27
#define SERVO_ORIENT_AD 14
#define VERIN_DIR_AD 12
#define VERIN_PWM_AD 13

// --- Arrière gauche ---
#define STEP_RG 17
#define DIR_RG 5
#define CAP_RG 18
#define SERVO_ROT_RG 19
#define SERVO_ORIENT_RG 21
#define VERIN_DIR_RG 2
#define VERIN_PWM_RG 3

// --- Arrière droit ---
#define STEP_RD 10
#define DIR_RD 9
#define CAP_RD 8
#define SERVO_ROT_RD 7
#define SERVO_ORIENT_RD 6
#define VERIN_DIR_RD 11
#define VERIN_PWM_RD 20

Actionneur::Actionneur() {
    actionneurs[AVANT_GAUCHE] = new ClassActionneur();
    actionneurs[AVANT_DROIT] = new ClassActionneur();
    actionneurs[ARRIERE_GAUCHE] = new ClassActionneur();
    actionneurs[ARRIERE_DROIT] = new ClassActionneur();
}

void Actionneur::Init() {
    // Initialisation des actionneurs  
    actionneurs[AVANT_GAUCHE]->Init(STEP_AG, DIR_AG, CAP_AG,
                                    SERVO_ROT_AG, SERVO_ORIENT_AG,
                                    VERIN_DIR_AG, VERIN_PWM_AG);
  
    actionneurs[AVANT_DROIT]->Init(STEP_AD, DIR_AD, CAP_AD,
                                   SERVO_ROT_AD, SERVO_ORIENT_AD,
                                   VERIN_DIR_AD, VERIN_PWM_AD);
    
    actionneurs[ARRIERE_GAUCHE]->Init(STEP_RG, DIR_RG, CAP_RG,
                                      SERVO_ROT_RG, SERVO_ORIENT_RG,
                                      VERIN_DIR_RG, VERIN_PWM_RG);

    actionneurs[ARRIERE_DROIT]->Init(STEP_RD, DIR_RD, CAP_RD,
                                     SERVO_ROT_RD, SERVO_ORIENT_RD,
                                     VERIN_DIR_RD, VERIN_PWM_RD);

    // Démarrage des tasks et homings
    for (int i = 0; i < ACTION_COUNT; i++) {
        actionneurs[i]->StartTask();           // démarre la task dédiée
        actionneurs[i]->StartHomingNonBlocking(); // lance homing sans bloquer Init()

    }
}

// === Commandes globales ===
void Actionneur::MoveOneElevatorTo(ActionneurID id, float height_mm) {
    cmd.type = ActionneurCmdType::CMD_MOVE_ASC;
    cmd.value = height_mm;
    cmd.channel = 0;

    if (id < ACTION_COUNT && cmd.type == ActionneurCmdType::CMD_MOVE_ASC)
        actionneurs[id]->PostCommand(cmd);
}

void Actionneur::RotateOneKapla(ActionneurID id, int angle) {
    cmd.type = ActionneurCmdType::CMD_SERVO_POS;
    cmd.value = angle;
    cmd.channel = 1;

    if (id < ACTION_COUNT)
        actionneurs[id]->PostCommand(cmd);
}

void Actionneur::OrientOne(ActionneurID id, int angle) {
    cmd.type = ActionneurCmdType::CMD_SERVO_POS;
    cmd.value = angle;
    cmd.channel = 0;
    
    if (id < ACTION_COUNT)
        actionneurs[id]->PostCommand(cmd);
}

void Actionneur::SetAllVerinSpeed(float speed_mm_s) {
    cmd.type = ActionneurCmdType::CMD_VERIN_EXT;
    cmd.value = speed_mm_s;
    cmd.channel = 0;
    
    for (int i = 0; i < ACTION_COUNT; i++)
        actionneurs[i]->PostCommand(cmd);
}

void Actionneur::SetOneVerinSpeed(ActionneurID id, float speed_mm_s) {
    cmd.type = ActionneurCmdType::CMD_VERIN_EXT;
    cmd.value = speed_mm_s;
    cmd.channel = 0;
    
    if (id < ACTION_COUNT)
        actionneurs[id]->PostCommand(cmd);
}

void Actionneur::StopAllVerin() {
    cmd.type = ActionneurCmdType::CMD_VERIN_EXT;
    cmd.value = 0;
    cmd.channel = 0;
    
    for (int i = 0; i < ACTION_COUNT; i++)
        actionneurs[i]->PostCommand(cmd);
}

void Actionneur::StopOneVerin(ActionneurID id) {
    cmd.type = ActionneurCmdType::CMD_VERIN_EXT;
    cmd.value = 0;
    cmd.channel = 0;
    
    if (id < ACTION_COUNT)
        actionneurs[id]->PostCommand(cmd);
}

// === États ===
bool Actionneur::AreAllReady() {
    for (int i = 0; i < ACTION_COUNT; i++)
        if (!actionneurs[i]->IsReady()) return false;
    return true;
}

bool Actionneur::AreAllHomed() {
    for (int i = 0; i < ACTION_COUNT; i++)
        if (!actionneurs[i]->IsHomed()) return false;
    return true;
}

bool Actionneur::AreAllIdle() {
    for (int i = 0; i < ACTION_COUNT; i++)
        if (actionneurs[i]->IsElevatorBusy()) return false;
    return true;
}

float Actionneur::GetHeight(ActionneurID id) {
    if (id >= ACTION_COUNT) return -1;
    return actionneurs[id]->GetHeight();
}
