#include "TrajectoryFollower.hpp"
#include <ArduinoJson.h>
#include <math.h>

TrajectoryFollower::TrajectoryFollower()
: nPoints(0), currentIdx(0), active(false), hasCorr(false),
  Ld(0.2f), v_nom(0.1f) // 20cm lookahead, 0.2m/s par défaut
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

void TrajectoryFollower::computeCommand(const Pose2D& poseOdom, float dt, float& v_out, float& w_out) {
    if (!active || nPoints == 0) {
        v_out = 0.0f;
        w_out = 0.0f;
        return;
    }

    // Pose utilisée pour le suivi : si pose corrigée dispo -> on la prend
    Pose2D pose = poseCorr;
    if (!hasCorr) {
        pose = poseOdom;
    }

    // Sélection du point lookahead (pure pursuit)
    int idx = currentIdx;
    Point2D target = points[idx];

    // Distance du robot à ce point
    auto dist = [&](const Point2D& p) {
        float dx = p.x - pose.x;
        float dy = p.y - pose.y;
        return sqrtf(dx*dx + dy*dy);
    };

    float d = dist(target);

    // Avance dans les points tant que la distance est < Ld
    while (idx < nPoints - 1 && d < Ld) {
        idx++;
        target = points[idx];
        d = dist(target);
    }

    currentIdx = idx;

    // Si on est très proche du dernier point -> arrêt
    const float stopThresh = 0.02f; // 2 cm
    if (idx == nPoints - 1 && d < stopThresh) {
        v_out = 0.0f;
        w_out = 0.0f;
        active = false;
        return;
    }

    // Coordonnées du point cible dans le repère robot
    float dx = target.x - pose.x;
    float dy = target.y - pose.y;

    float c = cosf(pose.theta);
    float s = sinf(pose.theta);

    // monde -> robot
    float x_r =  c*dx + s*dy;     // avant
    float y_r = -s*dx + c*dy;     // gauche

    // Angle par rapport à l'axe avant robot
    float alpha = atan2f(y_r, x_r);

    // Pure pursuit : courbure kappa = 2 * sin(alpha) / Ld
    float L = max(Ld, 0.05f); // éviter division par 0
    float kappa = 2.0f * sinf(alpha) / L;

    // Vitesse linéaire : on peut réduire un peu si on est proche de la fin
    float v = v_nom;
    if (idx == nPoints - 1) {
        // ralentit quand on approche du dernier point
        float ratio = d / L;
        ratio = constrain(ratio, 0.2f, 1.0f);
        v *= ratio;
    }

    float w = kappa * v;

    // Saturation vitesse angulaire (sécurité)
    const float w_max = 3.0f; // rad/s
    if (w > w_max)  w = w_max;
    if (w < -w_max) w = -w_max;

    v_out = v;
    w_out = w;
}
