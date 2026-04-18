#include <Arduino.h>
#include "ClassMotors.hpp"
#include "TrajectoryFollower.hpp"
#include <driver/gpio.h>

// UART vers la Raspberry : ici Serial (USB)
#define SERIAL_PI   Serial
#define BAUD_PI     115200

#define EN_Motor 21

ClassMotors motors;
TrajectoryFollower follower;

bool newTrajectory = false;

// Tâches
void taskControl(void* arg);
void taskSerialRx(void* arg);
void taskSerialTx(void* arg);

void setup() {
    // AGRANDISSEMENT DU BUFFER SERIE (Crucial)
    SERIAL_PI.setRxBufferSize(2048);
    
    SERIAL_PI.begin(BAUD_PI);
    delay(500);
    SERIAL_PI.println("ESP32 Trajectory + Motors ready");

    pinMode(EN_Motor, OUTPUT);
    digitalWrite(EN_Motor ,HIGH);

    motors.StartMotors();

    // PARAMÈTRES OPTIMISÉS
    follower.setLookahead(0.20f);    // 20 cm de lookahead
    follower.setNominalSpeed(0.70f); // 70 cm/s de vitesse de pointe !

    // taskControl sur core 0 (séparé du wifi/serial core 1)
    // Stacks augmentés pour éviter les stack overflows
    xTaskCreatePinnedToCore(taskControl,  "Control",  8192, nullptr, 3, nullptr, 0);
    xTaskCreatePinnedToCore(taskSerialRx, "SerialRx", 12288, nullptr, 2, nullptr, 1);
    xTaskCreatePinnedToCore(taskSerialTx, "SerialTx",  4096, nullptr, 1, nullptr, 1);
}

void loop() {
    vTaskDelay(pdMS_TO_TICKS(100));
}

static void applyVLVR(float vL, float vR) {
    TaskParams p;
    p.vitesseGauche = vL;
    p.vitesseDroite = vR;
    motors.EnvoyerVitesse(&p);
}

// TÂCHE DE CONTRÔLE : TEMPS RÉEL (50Hz)
void taskControl(void* arg) {
    // Attente initiale pour laisser StartMotors() terminer avant la 1ère itération
    vTaskDelay(pdMS_TO_TICKS(100));
    TickType_t lastWake = xTaskGetTickCount();
    uint32_t lastMicros = micros();

    float vL = 0.0f, vR = 0.0f;
    float temps_arc = 0.0f;
    VelMots2D velmots {vL, vR};
    bool wasMoving = false;

    while (true) {
        uint32_t now = micros();
        float dt = (now - lastMicros) / 1e6f;
        if (dt <= 0.0f) dt = 0.001f;
        lastMicros = now;

        // Odométrie
        float x, y, th;
        motors.GetPosition(x, y, th);
        Pose2D odomPose { x, y, th };

        // Nouveau trajet reçu
        if (newTrajectory) {
            newTrajectory = false;
            wasMoving = true;
        }

        // --- PILOTAGE ACTIF ---
        if (follower.isActive()) {
            bool isMoving = follower.computeCommand(odomPose, velmots, dt, vL, vR, temps_arc);
            
            // Si on vient juste de s'arrêter
            if (wasMoving && !isMoving) {
                SERIAL_PI.println("trajectoryFinished");
            }
            wasMoving = isMoving;
        } else {
            vL = 0.0f;
            vR = 0.0f;
            wasMoving = false;
        }

        applyVLVR(vL, vR);
        velmots.vL = vL;
        velmots.vR = vR;

        // Boucle stricte de 20ms (50 Hz)
        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(20)); 
    }
}

// Réception série depuis la Rasp
// Réception série depuis la Rasp
void taskSerialRx(void* arg) {
    String line;

    while (true) {
        while (SERIAL_PI.available()) {
            char c = SERIAL_PI.read();
            if (c == '\n') {
                line.trim();
                if (line.length() > 0) {
                    if (line[0] == '[') {
                        if (follower.loadFromJson(line.c_str())) {
                            SERIAL_PI.println("BEZ OK");
                            newTrajectory = true;
                        } else {
                            SERIAL_PI.println("BEZ ERR");
                        }
                    }
                    else if (line.startsWith("POSE")) {
                        float x_mm, y_mm, th;
                        if (sscanf(line.c_str(), "POSE %f %f %f", &x_mm, &y_mm, &th) == 3) {
                            Pose2D p;
                            p.x = x_mm / 1000.0f;
                            p.y = y_mm / 1000.0f;
                            p.theta = th;
                            follower.setCorrectedPose(p);
                        }
                    }
                    // --- LA CORRECTION ANTI-PARASITES EST ICI ---
                    else if (line.indexOf("SET POSE") != -1) {
                        float x_mm = 0, y_mm = 0, th = 0;
                        
                        // On ignore tout ce qu'il y a avant "SET POSE" (les parasites)
                        int match_index = line.indexOf("SET POSE");
                        String clean_line = line.substring(match_index);
                        
                        if (sscanf(clean_line.c_str(), "SET POSE %f %f %f", &x_mm, &y_mm, &th) == 3) {
                            motors.ResetPosition(x_mm / 1000.0f, y_mm / 1000.0f, th);
                            
                            // LOG DE CONFIRMATION
                            SERIAL_PI.print("[ESP32] ✅ POSE RESET OK : X=");
                            SERIAL_PI.print(x_mm / 1000.0f, 3);
                            SERIAL_PI.print("m, Y=");
                            SERIAL_PI.print(y_mm / 1000.0f, 3);
                            SERIAL_PI.println("m");
                        } else {
                            SERIAL_PI.println("[ESP32] ❌ ERREUR PARSING SET POSE !");
                        }
                    }
                    // --------------------------------------------
                    else if (line.startsWith("STOP")) {
                        follower.reset();
                        motors.Stop();
                    }
                }
                line = "";
            } else if (c != '\r') {
                line += c;
            }
        }
        vTaskDelay(pdMS_TO_TICKS(2));
    }
}

void taskSerialTx(void* arg) {
    TickType_t lastWake = xTaskGetTickCount();
    while (true) {
        // Envoi odométrie en continu à 20Hz pour la Raspberry
        float x, y, th;
        motors.GetPosition(x, y, th);
        
        SERIAL_PI.print("[");
        SERIAL_PI.print(x, 4);
        SERIAL_PI.print(", ");
        SERIAL_PI.print(y, 4);
        SERIAL_PI.print(", ");
        SERIAL_PI.print(th, 4);
        SERIAL_PI.println("]");

        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(50)); 
    }
}