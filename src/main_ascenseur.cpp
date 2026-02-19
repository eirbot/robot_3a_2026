#include <Arduino.h>
#include "ClassCommandManager.hpp"

// Create the command manager instance
ClassCommandManager commandManager;

void setup() {
    Serial.begin(115200);        // Initialize UART
    while (!Serial);             // Wait for Serial port (for some boards)

    ASC1.Init(ASC_1_SNS, MM_PER_REV);
    ASC2.Init(ASC_2_SNS, MM_PER_REV);
    ASC3.Init(ASC_3_SNS, MM_PER_REV);
    ASC4.Init(ASC_4_SNS, MM_PER_REV);

    ASC1.StandardOp(3, 4096, 2);
    ASC2.StandardOp(3, 4096, 2);
    ASC3.StandardOp(3, 4096, 2);
    ASC4.StandardOp(3, 4096, 2);
    // Start the command handling task
    commandManager.StartCommandTask();

    // Print ready message
    Serial.println("Command manager started. Send commands in TRG/CMD/ARG format, e.g., ASC1/MOVE/5.0");

}

void loop() {
    // Main loop can be used for other tasks or left empty
    vTaskDelay(pdMS_TO_TICKS(1000)); // Sleep to reduce CPU usage
}