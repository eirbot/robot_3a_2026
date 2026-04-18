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
    
    // 1. SÉCURITÉ MÉMOIRE
    if (!active || nPoints == 0 || currentIdx >= nPoints - 1) {
        vL_out = 0.0f;
        vR_out = 0.0f;
        active = false;
        return false;
    }

    float current_v_nom = v_nom;
    if (current_v_nom < 0.05f) current_v_nom = 0.5f;

    Pose2D pose = hasCorr ? poseCorr : poseOdom;
    Point2D target = points[currentIdx + 1];

    // Distance réelle entre le robot et le point cible
    float dx_w = target.x - pose.x;
    float dy_w = target.y - pose.y;
    float d = sqrtf(dx_w*dx_w + dy_w*dy_w);

    // 2. LOGIQUE D'AVANCEMENT (Tolérance 12cm pour la fluidité)
    if (d < 0.12f && currentIdx < nPoints - 2) {
        currentIdx++;
        target = points[currentIdx + 1];
        dx_w = target.x - pose.x;
        dy_w = target.y - pose.y;
        d = sqrtf(dx_w*dx_w + dy_w*dy_w);
    }

    // 3. ARRÊT CHIRURGICAL SUR LE DERNIER POINT (Précision 1cm)
    if (currentIdx >= nPoints - 2 && d < 0.01f) {
        vL_out = 0.0f;
        vR_out = 0.0f;
        active = false;
        Serial.println("[ESP32] DESTINATION ATTEINTE AVEC PRECISION !");
        return false;
    }

    // --- MATHÉMATIQUES (Repère Robot) ---
    float c = cosf(pose.theta);
    float s = sinf(pose.theta);
    float x_r =  c*dx_w + s*dy_w;     
    float y_r = -s*dx_w + c*dy_w;     

    // MARCHE ARRIÈRE AUTOMATIQUE
    bool goBackward = (x_r < 0.0f);
    float steer_x = goBackward ? -x_r : x_r;
    float steer_y = goBackward ? -y_r : y_r;

    float theta = 2.0f * atan2f(steer_y, steer_x);
    
    float vL = current_v_nom;
    float vR = current_v_nom;
    
    // Calcul différentiel pour les virages
    if (fabs(theta) > 0.001f) {
        float R = d / (2.0f * sinf(fabs(theta) / 2.0f));
        float w = current_v_nom / R;
        
        if (theta > 0) { // Cible à gauche
            vL = current_v_nom - (WHEEL_BASE / 2.0f) * w;
            vR = current_v_nom + (WHEEL_BASE / 2.0f) * w;
        } else { // Cible à droite
            vL = current_v_nom + (WHEEL_BASE / 2.0f) * w;
            vR = current_v_nom - (WHEEL_BASE / 2.0f) * w;
        }
    }

    // Inversion finale des moteurs si on recule
    if (goBackward) {
        vL = -vL;
        vR = -vR;
    }

    // --- FREINAGE PROPORTIONNEL ---
    int nPointsDec = nPoints / 4;
    if (nPointsDec < 3) nPointsDec = 3;
    
    if (currentIdx > nPoints - nPointsDec) {
        if (currentIdx >= nPoints - 2) {
            // Asservissement proportionnel sur les tout derniers centimètres
            float v_approche = d * 2.0f; 
            if (v_approche < 0.05f) v_approche = 0.05f; // Pas moins de 5 cm/s pour ne pas bloquer
            
            vL = (vL > 0) ? v_approche : -v_approche;
            vR = (vR > 0) ? v_approche : -v_approche;
        } else {
            // Décélération douce en approche
            float ratio = (float)(nPoints - 1 - currentIdx) / nPointsDec; 
            if (ratio < 0.25f) ratio = 0.25f; 
            vL *= ratio;
            vR *= ratio;
        }
    }

    // --- LIMITATION D'ACCÉLÉRATION (Vraie physique via dt) ---
    float aL = (vL - velmots.vL) / dt;
    float aR = (vR - velmots.vR) / dt;
    float max_accel = fmaxf(fabs(aL), fabs(aR));
    float max_accel_allowed = ACCEL_MM_S2 / 1000.0f;
    
    if (max_accel > max_accel_allowed) {
        float factor = max_accel_allowed / max_accel;
        vL = velmots.vL + aL * factor * dt;
        vR = velmots.vR + aR * factor * dt;
    }

    // --- LIMITATION DE VITESSE MAXIMALE ---
    float max_spd = fmaxf(fabs(vL), fabs(vR));
    float max_spd_allowed = MAX_SPEED_MM_S / 1000.0f;
    if (max_spd > max_spd_allowed) {
        float factor = max_spd_allowed / max_spd;
        vL *= factor;
        vR *= factor;
    }

    // Envoi des commandes
    vL_out = vL;
    vR_out = vR;
    temps_arc = dt; // Résiduel pour garder la même signature de fonction

    // LOG UNIQUE ET PROPRE
    Serial.print("[ESP32] TargetIdx: ");
    Serial.print(currentIdx + 1);
    Serial.print(" | Dist: ");
    Serial.print(d, 3);
    Serial.print("m | vL: ");
    Serial.print(vL, 3);
    Serial.print(" | vR: ");
    Serial.println(vR, 3);

    return true;
}