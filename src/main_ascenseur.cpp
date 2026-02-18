#include "ClassAscenseur.hpp"
#include <stdio.h>
#include <string.h>

// Elevator objects
ClassAscenseur ASC1(ASC_1_STP, ASC_1_DIR, ASC_1_INV);
ClassAscenseur ASC2(ASC_2_STP, ASC_2_DIR, ASC_2_INV);
ClassAscenseur ASC3(ASC_3_STP, ASC_3_DIR, ASC_3_INV);
ClassAscenseur ASC4(ASC_4_STP, ASC_4_DIR, ASC_4_INV);

#define MAX_FIELD_LEN   16
#define RX_QUEUE_LENGTH 16  // Number of queued messages

// FreeRTOS queue handle
static QueueHandle_t rxQueue;

// -------- Message structure -------- //
typedef struct {
    char address[MAX_FIELD_LEN]; // "ASCn"
    char command[MAX_FIELD_LEN]; // "MOVE", "HOME"
    char arg[MAX_FIELD_LEN];     // value in mm for MOVE, ignored for HOME
} Message_t;

// Device table
struct DeviceEntry {
    const char* name;
    ClassAscenseur* instance;
};
DeviceEntry devices[] = {
    { "ASC1", &ASC1 },
    { "ASC2", &ASC2 },
    { "ASC3", &ASC3 },
    { "ASC4", &ASC4 },
};
#define DEVICE_COUNT (sizeof(devices)/sizeof(devices[0]))

typedef void (ClassAscenseur::*CmdMethod)(float);
struct CommandEntry {
    const char* name;
    CmdMethod method;
};
CommandEntry commands[] = {

    { "MOVE", &ClassAscenseur::MoveToHeight },
    { "HOME", &ClassAscenseur::StartHoming },
};
#define COMMAND_COUNT (sizeof(commands)/sizeof(commands[0]))

// -------- Dispatch function --------
void DispatchMessage(const Message_t* msg) {
    ClassAscenseur* target = nullptr;
    CmdMethod method = nullptr;
    // Find device
    for (int i = 0; i < DEVICE_COUNT; i++) {
        if (strcmp(msg->address, devices[i].name) == 0) {
            target = devices[i].instance;
            break;
        }
    }
    if (!target) return;

    // Find command
    for (int i = 0; i < COMMAND_COUNT; i++) {
        if (strcmp(msg->command, commands[i].name) == 0) {
            method = commands[i].method;
            break;
        }
    }
    if (!method) return;

    // Find value
    float value = atof(msg->arg);
    Serial.println("Dispatching: " + String(msg->address) + " " + String(msg->command) + " " + String(value));
    (target->*method)(value);
}

// -------- FreeRTOS Tasks --------

// Serial reading task: reads lines and sends to queue
void SerialTask(void* pvParameters) {
    char line[64];
    while (1) {
        if (Serial.available()) {
            size_t len = Serial.readBytesUntil('\n', line, sizeof(line));
            line[len] = '\0';

            Message_t msg;
            memset(&msg, 0, sizeof(msg));
            if (sscanf(line, "%15s %15s %15s", msg.address, msg.command, msg.arg) >= 2) {
                xQueueSend(rxQueue, &msg, portMAX_DELAY);
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

// Command dispatch task: reads messages from queue and executes them
void DispatchTask(void* pvParameters) {
    Message_t msg;
    while (1) {
        if (xQueueReceive(rxQueue, &msg, portMAX_DELAY) == pdTRUE) {
            DispatchMessage(&msg);
        }
    }
}

// -------- Setup function --------
void setup() {
    Serial.begin(115200);
    delay(1000);
    // Initialize elevators
    Serial.println("---INITIALISATION DES ASCENSEURS----");
    delay(1000);
    ASC1.Init(ASC_1_SNS, MM_PER_REV);
    ASC2.Init(ASC_2_SNS, MM_PER_REV);
    ASC3.Init(ASC_3_SNS, MM_PER_REV);
    ASC4.Init(ASC_4_SNS, MM_PER_REV);

    delay(1000);
    Serial.println("---HOMING DES ASCENSEURS----");
    ASC1.StartHoming();
    ASC2.StartHoming();
    ASC3.StartHoming();
    ASC4.StartHoming();
    Serial.println("---HOMING SUCCESSFULL ASCENSEUR READY ----");

    delay(2000); // Wait for homing to complete
    // Create FreeRTOS queue
    rxQueue = xQueueCreate(RX_QUEUE_LENGTH, sizeof(Message_t));

    // Create tasks
    xTaskCreate(SerialTask, "SerialTask", 2048, NULL, 1, NULL);
    xTaskCreate(DispatchTask, "DispatchTask", 2048, NULL, 1, NULL);
    Serial.println("---SYSTEM READY----");
    // Start the scheduler (Arduino/ESP32 automatically calls vTaskStartScheduler)
}

// Empty loop because FreeRTOS handles tasks
void loop() {
    // Nothing needed here
}