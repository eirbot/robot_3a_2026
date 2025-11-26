#include "TrajectoryFollower.hpp"
#include <ArduinoJson.h>
#include <math.h>

// TrajectoryFollower::TrajectoryFollower()
// : nPoints(0), currentIdx(0), active(false), hasCorr(false),
//   Ld(0.2f), v_nom(0.1f) // 20cm lookahead, 0.2m/s par défaut
// {
//     poseCorr = {0.0f, 0.0f, 0.0f};
// }

TrajectoryFollower::TrajectoryFollower()
: nPoints(0), currentIdx(0), active(false), hasCorr(false),
  Ld(0.2f), v_nom(0.1f),
  seg_v(0), seg_w(0), seg_time_total(0), seg_time_elapsed(0), segmentActive(false)
{
    poseCorr = {0.0f, 0.0f, 0.0f};
}


float TrajectoryFollower::wrapPi(float a) {
    while (a >  M_PI) a -= 2.0f * M_PI;
    while (a < -M_PI) a += 2.0f * M_PI;
    return a;
}

bool TrajectoryFollower::loadFromJson(const char* json) {
    StaticJsonDocument<4096> doc; // suffisant pour 50 points

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


void TrajectoryFollower::computeSegment(const Pose2D& pose)
{
    Point2D target = points[currentIdx];

    float dx = target.x - pose.x;
    float dy = target.y - pose.y;

    float d = sqrtf(dx*dx + dy*dy);
    if (d < 0.01f) {
        segmentActive = false;
        return;
    }

    float c = cosf(pose.theta);
    float s = sinf(pose.theta);

    float x_r =  c*dx + s*dy;
    float y_r = -s*dx + c*dy;

    float alpha = atan2f(y_r, x_r);

    float kappa = 2.0f * sinf(alpha) / d;

    seg_v = v_nom;
    seg_w = seg_v * kappa;

    float L_arc = (fabsf(alpha) < 0.01f)
                  ? d
                  : d * alpha / sinf(alpha);

    seg_time_total = L_arc / seg_v;
    seg_time_elapsed = 0;

    segmentActive = true;
}


void TrajectoryFollower::computeCommand(const Pose2D& poseOdom,float dt,float& v_out,float& w_out,float& temps_deplacement){

    if (!active || currentIdx >= nPoints) {
        v_out = 0;
        w_out = 0;
        temps_deplacement = 0.02;
        return;
    }

    // Choisir la pose (odom ou corrigée)
    Pose2D pose = hasCorr ? poseCorr : poseOdom;

    // Récupération du point à atteindre
    Point2D target = points[currentIdx];

    // Calcul du vecteur vers la cible
    float dx = target.x - pose.x;
    float dy = target.y - pose.y;
    float d = sqrtf(dx*dx + dy*dy);

    if (d < 0.01f) {   // point considéré atteint à 1 cm
        currentIdx++;
        if (currentIdx >= nPoints) active = false;
        v_out = 0;
        w_out = 0;
        temps_deplacement = 0.01;
        return;
    }

    // Coordonnées de la cible dans le repère robot
    float c = cosf(pose.theta);
    float s = sinf(pose.theta);

    float x_r =  c*dx + s*dy;     // en avant
    float y_r = -s*dx + c*dy;     // à gauche

    // angle relatif
    float alpha = atan2f(y_r, x_r);

    // ========= ARC DE CERCLE =========
    // Courbure kappa = 2 * sin(alpha) / d
    float kappa = 2.0f * sinf(alpha) / d;

    // Vitesse linéaire fixée
    float v = v_nom;

    // Vitesse angulaire pour suivre l’arc
    float w = v * kappa;

    // Longueur de l'arc (formule exacte)
    float L_arc = d * alpha / sinf(alpha);

    // En cas alpha petit, prendre approximation
    if (fabsf(alpha) < 0.01f)
        L_arc = d;

    temps_deplacement = L_arc / v;

    // Sortie commande
    v_out = v;
    w_out = w;

    // Passer au point suivant à la prochaine itération
    currentIdx++;
}
