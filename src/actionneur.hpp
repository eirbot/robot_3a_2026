#ifndef ACTIONNEUR_HPP
#define ACTIONNEUR_HPP

#include "ClassActionneur.hpp"
#include "utilities.hpp"

enum ActionneurID {
    AVANT_GAUCHE = 0,
    AVANT_DROIT,
    ARRIERE_GAUCHE,
    ARRIERE_DROIT,
    ACTION_COUNT
};

class Actionneur {
public:
    Actionneur();

    void Init();

    // === Commandes globales ===
    void MoveOneElevatorTo(ActionneurID id, float height_mm);
    void RotateOneKapla(ActionneurID id, int angle);
    void OrientOne(ActionneurID id, int angle);
    void SetAllVerinSpeed(float speed_mm_s);
    void SetOneVerinSpeed(ActionneurID id, float speed_mm_s);
    void StopAllVerin();
    void StopOneVerin(ActionneurID id);

    // === États ===
    bool AreAllReady();
    bool AreAllHomed();
    bool AreAllIdle();

    float GetHeight(ActionneurID id);

private:
    ClassActionneur* actionneurs[ACTION_COUNT];
    ActionneurCommand& cmd = *(new ActionneurCommand());
};

#endif
