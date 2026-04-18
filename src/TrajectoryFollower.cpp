#include "TrajectoryFollower.hpp"
#include <ArduinoJson.h>
#include <math.h>

TrajectoryFollower::TrajectoryFollower()
: nPoints(0), currentIdx(0), active(false), hasCorr(false),
  Ld(0.20f), v_nom(0.35f) // 20cm lookahead, 0.35m/s par défaut
{
    poseCorr = {0.0f, 0.0f, 0.0f};
}

float TrajectoryFollower::wrapPi(float a) {
    while (a >  M_PI) a -= 2.0f * M_PI;
    while (a < -M_PI) a += 2.0f * M_PI;
    return a;
}

bool TrajectoryFollower::loadFromJson(const char* json) {
    StaticJsonDocument<4096> doc; // suffisant pour 50+ points

    DeserializationError err = deserializeJson(doc, json);
    if (err) {
        Serial.print("JSON error: ");
        Serial.println(err.c_str());
        return false;
    }

    if (!doc.is<JsonArray>()) {
        Serial.println("JSON n'est pas un array");
        return false;
    }

    JsonArray arr = doc.as<JsonArray>();

    int idx = 0;
    for (JsonVariant v : arr) {
        if (!v.is<JsonArray>()) continue;
        JsonArray pt = v.as<JsonArray>();
        if (pt.size() < 2) continue;

        if (idx >= MAX_POINTS) break;

        // x, y en mm -> convertis en m
        float x_mm = pt[0].as<float>();
        float y_mm = pt[1].as<float>();
        points[idx].x = x_mm / 1000.0f;
        points[idx].y = y_mm / 1000.0f;
        idx++;
    }

    if (idx == 0) {
        Serial.println("Aucun point valide dans la trajectoire");
        return false;
    }

    nPoints = idx;
    currentIdx = 0;
    active = true;

    Serial.print("Trajectoire chargee avec ");
    Serial.print(nPoints);
    Serial.println(" points.");
    return true;
}

void TrajectoryFollower::setCorrectedPose(const Pose2D& pose) {
    poseCorr = pose;
    hasCorr = true;
}

bool TrajectoryFollower::hasCorrectedPose() const {
    return hasCorr;
}

bool TrajectoryFollower::isFinished() const {
    return !active;
}

void TrajectoryFollower::reset() {
    active = false;
    nPoints = 0;
    currentIdx = 0;
}

void TrajectoryFollower::setLookahead(float Ld_m) {
    Ld = Ld_m;
}

void TrajectoryFollower::setNominalSpeed(float v_mps) {
    v_nom = v_mps;
}

bool TrajectoryFollower::computeCommand(const Pose2D& poseOdom, const VelMots2D& velmots, float dt, float& vL_out, float& vR_out, float& temps_arc) {
    
    // 1. SÉCURITÉ : Fin de trajet ou Out-Of-Bounds (Évite les crashs mémoire)
    if (!active || nPoints == 0 || currentIdx >= nPoints - 1) {
        vL_out = 0.0f;
        vR_out = 0.0f;
        active = false;
        return false;
    }

    // Récupère la vitesse nominale définie dans le main
    float current_v_nom = v_nom;
    if (current_v_nom < 0.05f) current_v_nom = 0.3f; // Sécurité si oubli d'init

    Serial.print("Point suivant, currentIdx : ");
    Serial.println(currentIdx + 1);

    // Pose utilisée pour le suivi
    Pose2D pose = hasCorr ? poseCorr : poseOdom;
    Point2D target = points[currentIdx + 1];

    // Calcul de la distance pure (Monde)
    float dx_w = target.x - pose.x;
    float dy_w = target.y - pose.y;
    float d = sqrtf(dx_w*dx_w + dy_w*dy_w);

    Serial.print("target  : ");
    Serial.print(target.x);
    Serial.print("   ");
    Serial.println(target.y);

    float c = cosf(pose.theta);
    float s = sinf(pose.theta);

    // Repère monde -> Repère robot
    float x_r =  c*dx_w + s*dy_w;     // X: Avant/Arrière
    float y_r = -s*dx_w + c*dy_w;     // Y: Gauche/Droite

    // --- LA MAGIE : MARCHE ARRIÈRE AUTOMATIQUE ---
    // Si X est négatif, la cible est derrière le robot !
    bool goBackward = (x_r < 0.0f);
    
    // On projette virtuellement le point devant le robot pour le calcul d'angle
    // (En inversant X et Y, on crée un miroir parfait pour braquer à l'envers)
    float steer_x = goBackward ? -x_r : x_r;
    float steer_y = goBackward ? -y_r : y_r;

    // Angle de courbure de l'arc de cercle
    float theta = 2.0f * atan2f(steer_y, steer_x);
    float Dist_Center = d;

    // Longueur réelle de l'arc (évite la division par zéro en ligne droite)
    if (fabs(theta) > 0.001f) {
        Dist_Center = (theta / 2.0f) * d / sinf(theta / 2.0f);
    }

    // Si on recule, on ordonne une distance négative
    if (goBackward) {
        Dist_Center = -Dist_Center;
    }

    // Distances individuelles pour chaque roue (Odométrie différentielle)
    float Dist_L = Dist_Center - (WHEEL_BASE / 2.0f) * theta;
    float Dist_R = Dist_Center + (WHEEL_BASE / 2.0f) * theta;

    // --- CALCUL DU TEMPS ET DES VITESSES ---
    // On base le temps sur la roue qui a le plus grand chemin à parcourir
    float max_dist = fmaxf(fabs(Dist_L), fabs(Dist_R));
    temps_arc = max_dist / current_v_nom;

    // Décélération douce sur la fin de la trajectoire
    int nPointsDec = nPoints / 2;
    if(currentIdx > nPoints - nPointsDec){
        int decIdx = currentIdx - (nPoints - nPointsDec);
        temps_arc *= (1.0f + decIdx * 0.2f); // Allonge le temps pour réduire la vitesse
    }

    // Sécurité absolue anti division par zéro
    if (temps_arc < 0.02f) temps_arc = 0.02f;

    // Vitesses théoriques
    float vL = Dist_L / temps_arc;
    float vR = Dist_R / temps_arc;

    // --- LIMITATION D'ACCÉLÉRATION ---
    float aL = (vL - velmots.vL) / temps_arc;
    float aR = (vR - velmots.vR) / temps_arc;
    float max_accel = fmaxf(fabs(aL), fabs(aR));
    
    if (max_accel >= (ACCEL_MM_S2 / 1000.0f)) {
        float factor = (ACCEL_MM_S2 / 1000.0f) / max_accel;
        vL = velmots.vL + aL * factor * temps_arc;
        vR = velmots.vR + aR * factor * temps_arc;
    }

    // --- LIMITATION DE VITESSE MAX ---
    float max_spd = fmaxf(fabs(vL), fabs(vR));
    if (max_spd >= (MAX_SPEED_MM_S / 1000.0f)) {
        float factor = (MAX_SPEED_MM_S / 1000.0f) / max_spd;
        vL *= factor;
        vR *= factor;
    }

    // --- RECALCUL DU TEMPS RÉEL (Sécurisé) ---
    // On utilise uniquement la roue la plus rapide pour éviter les divisions par zéro
    // sur la roue intérieure des virages serrés.
    float max_v = fmaxf(fabs(vL), fabs(vR));
    if (max_v > 0.01f) {
        temps_arc = max_dist / max_v;
    }
    
    // SÉCURITÉ ANTI-GEL ABSOLUE :
    // Tes points sont espacés de quelques centimètres. Un segment ne 
    // devrait *jamais* prendre plus de 1.5 seconde.
    if (temps_arc > 1.5f) temps_arc = 1.5f;
    if (temps_arc < 0.02f) temps_arc = 0.02f;

    // On envoie aux moteurs !
    vL_out = vL;
    vR_out = vR;

    currentIdx++;
    
    Serial.print("  temps_arc: ");
    Serial.println(temps_arc);

    return true;
}