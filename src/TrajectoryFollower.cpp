#include "TrajectoryFollower.hpp"
#include <ArduinoJson.h>
#include <math.h>

TrajectoryFollower::TrajectoryFollower()
: nPoints(0), currentIdx(0), active(false), hasCorr(false),
  Ld(0.20f), v_nom(0.70f) // 20cm lookahead, 0.70 m/s par défaut
{
    poseCorr = {0.0f, 0.0f, 0.0f};
}

float TrajectoryFollower::wrapPi(float a) {
    while (a >  M_PI) a -= 2.0f * M_PI;
    while (a < -M_PI) a += 2.0f * M_PI;
    return a;
}

bool TrajectoryFollower::loadFromJson(const char* json) {
    StaticJsonDocument<4096> doc; 

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

bool TrajectoryFollower::isActive() const {
    return active;
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
    
    if (!active || nPoints == 0) {
        vL_out = 0.0f; vR_out = 0.0f; active = false; return false;
    }

    // Récupération de la position
    Pose2D pose = hasCorr ? poseCorr : poseOdom;
    Point2D finalTarget = points[nPoints - 1];

    // Distance au point d'arrivée final
    float d_final = hypotf(finalTarget.x - pose.x, finalTarget.y - pose.y);

    // --- 1. CONDITION D'ARRÊT CHIRURGICALE (1.0 cm) ---
    if (d_final < 0.010f) {
        vL_out = 0.0f; vR_out = 0.0f;
        active = false;
        Serial.println("[ESP32] DESTINATION ATTEINTE AVEC PRECISION !");
        return false;
    }

    // --- 2. RECHERCHE DU POINT DE LOOKAHEAD (Vrai Pure Pursuit) ---
    // On cherche le premier point situé à Ld mètres (ex: 8 cm) devant le robot.
    float current_Ld = 0.08f; 
    Point2D lookaheadPt = finalTarget; // Par défaut, on vise la fin
    
    // On cherche loin devant pour éviter les zigzags sur les points denses
    for (int i = currentIdx; i < nPoints; i++) {
        float dist_pt = hypotf(points[i].x - pose.x, points[i].y - pose.y);
        if (dist_pt >= current_Ld) {
            lookaheadPt = points[i];
            currentIdx = i; // On met à jour l'index pour ne pas reculer dans le tableau
            break;
        }
    }

    // --- 3. TRANSFORMATION REPÈRE ROBOT ---
    float c = cosf(pose.theta);
    float s = sinf(pose.theta);
    float dx = lookaheadPt.x - pose.x;
    float dy = lookaheadPt.y - pose.y;
    
    float x_r =  c * dx + s * dy; // X: Avant/Arrière
    float y_r = -s * dx + c * dy; // Y: Gauche/Droite
    float L2 = x_r * x_r + y_r * y_r;

    // --- 4. CALCUL DE LA COURBURE (\gamma) ---
    float gamma = 0.0f;
    if (L2 > 0.001f) {
        gamma = (2.0f * y_r) / L2; // Formule exacte du Pure Pursuit
    }

    // --- 5. VITESSE LINÉAIRE (V) ET MARCHE ARRIÈRE ---
    bool goBackward = (x_r < 0.0f); // Si la cible est derrière, on recule
    float V = v_nom;
    if (V < 0.05f) V = 0.5f; // Sécurité

    // Freinage proportionnel pur en approchant de la fin
    float V_brake = d_final * 2.5f; // Diminue progressivement
    if (V_brake < 0.15f) V_brake = 0.15f; // Ne descend jamais sous 15 cm/s pour ne pas bloquer
    
    if (V > V_brake) V = V_brake;
    if (goBackward) V = -V;

    // --- 6. VITESSE ANGULAIRE (\omega) ET ROUES ---
    float W = gamma * V;

    // Bride de rotation (Anti-Toupie) pour forcer le robot à avancer
    float max_W = 3.0f; // Rad/s Max
    if (W > max_W) W = max_W;
    if (W < -max_W) W = -max_W;

    // Cinématique différentielle
    float vL = V - (WHEEL_BASE / 2.0f) * W;
    float vR = V + (WHEEL_BASE / 2.0f) * W;

    // --- 7. APPLICATION DES LIMITES PHYSIQUES (Accel et VMax) ---
    float aL = (vL - velmots.vL) / dt;
    float aR = (vR - velmots.vR) / dt;
    float max_accel = fmaxf(fabs(aL), fabs(aR));
    float max_accel_allowed = ACCEL_MM_S2 / 1000.0f;
    
    if (max_accel > max_accel_allowed) {
        float factor = max_accel_allowed / max_accel;
        vL = velmots.vL + aL * factor * dt;
        vR = velmots.vR + aR * factor * dt;
    }

    float max_spd = fmaxf(fabs(vL), fabs(vR));
    float max_spd_allowed = MAX_SPEED_MM_S / 1000.0f;
    if (max_spd > max_spd_allowed) {
        float factor = max_spd_allowed / max_spd;
        vL *= factor;
        vR *= factor;
    }

    // --- SORTIE ---
    vL_out = vL;
    vR_out = vR;
    temps_arc = dt; 

    // Log minimal : uniquement au changement de point cible (pour ne pas saturer le UART à 50Hz)
    static int lastLoggedIdx = -1;
    if (currentIdx != lastLoggedIdx) {
        Serial.print("[ESP32] Tgt:");
        Serial.print(currentIdx);
        Serial.print(" | Pos:(");
        Serial.print(pose.x, 3); // Position X actuelle
        Serial.print(",");
        Serial.print(pose.y, 3); // Position Y actuelle
        Serial.print(") | dFin:");
        Serial.print(d_final, 3); // Distance restante
        Serial.print("m | vL:");
        Serial.print(vL, 2);     // Vitesse moteur Gauche
        Serial.print(" | vR:");
        Serial.println(vR, 2);   // Vitesse moteur Droit
        lastLoggedIdx = currentIdx;
    }

    return true;
}