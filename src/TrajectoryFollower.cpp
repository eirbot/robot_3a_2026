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
    currentIdx = 0;
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

void TrajectoryFollower::computeCommand(const Pose2D& poseOdom, float dt, float& vL_out, float& vR_out, float& temps_arc) {

    Serial.print("Point suivant, currentIdx : ");
    Serial.println( currentIdx +1);
    
    if (!active || nPoints == 0) {
        vL_out = 0.0f;
        vR_out = 0.0f;
        return;
    }

    // Pose utilisée pour le suivi : si pose corrigée dispo -> on la prend
    Pose2D pose = poseCorr;
    if (!hasCorr) {
        pose = poseOdom;
    }

    // Sélection du point lookahead (pure pursuit)
    Point2D target = points[currentIdx+1];

    // Distance du robot à ce point
    auto dist = [&](const Point2D& p) {
        float dx = p.x - pose.x;
        float dy = p.y - pose.y;
        return sqrtf(dx*dx + dy*dy);
    };

    float d = dist(target);

    // Coordonnées du point cible dans le repère robot
    float dx = target.x - pose.x;
    float dy = target.y - pose.y;

    float c = cosf(pose.theta);
    float s = sinf(pose.theta);

    // monde -> robot
    float x_r =  c*dx + s*dy;     // avant
    float y_r = -s*dx + c*dy;     // gauche

    // Angle par rapport à l'axe avant robot
    float theta = 2.0*atan2f(y_r, x_r);
    float R = 0;

    float Dist = x_r;
    if(theta!=0){
        Dist = theta/2.0*d/sinf(theta/2.0);
        R = d/(2.0*sin(theta/2.0));
    }
    temps_arc = Dist/v_nom;

    float Dist_L = (R-WHEEL_BASE/2.0)*theta;
    float Dist_R = (R+WHEEL_BASE/2.0)*theta;

    Serial.print("Dist_L : ");
    Serial.print(Dist_L);
    Serial.print("  Dist_R : ");
    Serial.println(Dist_R);

    float vL = Dist_L/temps_arc;
    float vR = Dist_R/temps_arc;

    Serial.print("vL : ");
    Serial.print(vL);
    Serial.print("  vR : ");
    Serial.println(vR);

    vL_out = vL;
    vR_out = vR;

    currentIdx++;
    Serial.print("  temps_arc: ");
    Serial.println(temps_arc);

    if (currentIdx == nPoints) {
        vL_out = 0.0f;
        vR_out = 0.0f;
        active = false;
        return;
    }
}
