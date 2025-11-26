#pragma once
#include <Arduino.h>

// Pose robot (repère monde)
// x : avant, y : gauche, theta : rad
struct Pose2D {
    float x;
    float y;
    float theta;
};

struct Point2D {
    float x;
    float y;
};

class TrajectoryFollower {
public:
    static constexpr int MAX_POINTS = 64;

    float seg_v;
    float seg_w;
    float seg_time_total;
    float seg_time_elapsed;
    bool segmentActive;

    TrajectoryFollower();

    // Charge une trajectoire depuis un JSON style [[x0,y0],[x1,y1],...]
    // Les x,y sont supposés en mm -> convertis en m.
    bool loadFromJson(const char* json);

    // Met à jour la pose corrigée venant de la Rasp (en m, rad)
    void setCorrectedPose(const Pose2D& pose);
    bool hasCorrectedPose() const;

    // Indique si la trajectoire est finie
    bool isFinished() const;

    // Réinitialise l’état interne (annule la traj en cours)
    void reset();

    void computeSegment(const Pose2D& pose);

    // Pure pursuit : calcule (v,w) à partir de la pose actuelle
    // - poseOdom : odom interne ESP32 (m, m, rad)
    // - dt : période de contrôle (s), au cas où tu veux lisser plus tard
    // Résultat en m/s et rad/s
    void computeCommand(const Pose2D& poseOdom, float dt, float& v_out, float& w_out, float& temps_deplacement);
    

    // Paramètres
    void setLookahead(float Ld_m);    // distance d’anticipation (m)
    void setNominalSpeed(float v_mps); // vitesse linéaire nominale (m/s)

    Point2D   points[MAX_POINTS];
    int       nPoints;
    int       currentIdx;
    bool      active;

private:
    

    Pose2D    poseCorr;      // dernière pose corrigée
    bool      hasCorr;

    float     Ld;            // lookahead distance (m)
    float     v_nom;         // vitesse nominale (m/s)

    static float wrapPi(float a);
};
