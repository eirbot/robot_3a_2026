#include "ClassCommandManager.hpp"

// Constructor
ClassCommandManager::ClassCommandManager() {
    memset(uartBuffer, 0, UART_BUFFER_SIZE);
}

// Start FreeRTOS task
void ClassCommandManager::StartCommandTask() {
    xTaskCreatePinnedToCore(
        ClassCommandManager::CommandTask, // Task function
        "CommandTask",                     // Name
        4096,                              // Stack size (adjust as needed)
        this,                              // Parameter
        1,                                 // Priority
        &vManagerHandle,                   // Task handle
        0                                  // Core ID (0 or 1)
    );
}

// FreeRTOS task
void ClassCommandManager::CommandTask(void *param) {
    ClassCommandManager *manager = static_cast<ClassCommandManager *>(param);

    while (true) {
        if (manager->uart_read_line(manager->uartBuffer, UART_BUFFER_SIZE)) {
            manager->ProcessUARTData(manager->uartBuffer);
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}


bool ClassCommandManager::uart_read_line(char *buffer, size_t maxLen) {
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\r') continue; // Ignore carriage returns
        if (c == '\n') { // End of line
            buffer[uartIndex] = '\0';
            uartIndex = 0;
            return true;
        }
        if (uartIndex < maxLen - 1) {
            buffer[uartIndex++] = c;
        } else {
            // Overflow, reset buffer
            uartIndex = 0;
        }
    }
    return false;
}

// Pass received UART string to SendCommand
void ClassCommandManager::ProcessUARTData(const char *data) {
    if (data && *data != '\0') {
        SendCommand(std::string(data));
    }
}

// Elevator objects
ClassAscenseur ASC1(ASC_1_STP, ASC_1_DIR, "ASC1", ASC_1_INV);
ClassAscenseur ASC2(ASC_2_STP, ASC_2_DIR, "ASC2", ASC_2_INV);
ClassAscenseur ASC3(ASC_3_STP, ASC_3_DIR, "ASC3", ASC_3_INV);
ClassAscenseur ASC4(ASC_4_STP, ASC_4_DIR, "ASC4", ASC_4_INV);

void ClassCommandManager::SendCommand(const std::string &input) {
    // Split TRG/CMD/ARG
    size_t pos1 = input.find('/');
    size_t pos2 = input.find('/', pos1 + 1);
    if (pos1 == std::string::npos || pos2 == std::string::npos) {
        return;}

    std::string trg = input.substr(0, pos1);
    std::string cmd = input.substr(pos1 + 1, pos2 - pos1 - 1);
    std::string arg = input.substr(pos2 + 1);

    float argVal = std::stof(arg); // convert argument to float

    // Map target names to instances
    static std::map<std::string, ClassAscenseur*> targets = {
        {"ASC1", &ASC1},
        {"ASC2", &ASC2},
        {"ASC3", &ASC3},
        {"ASC4", &ASC4}
    };
    // Map command names to member functions
    static std::map<std::string, bool (ClassAscenseur::*)(float)> commands = {
        {"HOME", &ClassAscenseur::StartHoming},
        {"MOVE", &ClassAscenseur::MoveToHeight}
    };

    auto trgIt = targets.find(trg);
    auto cmdIt = commands.find(cmd);

    if (trgIt != targets.end() && cmdIt != commands.end()) {
        ClassAscenseur* trg = trgIt->second;
        auto cmd = cmdIt->second;
        // Serial.println("[DEBUG] Sending Command");
        (trg->*cmd)(argVal); // Calls trg->cmd(arg)
        // Serial.println("[DEBUG] Command Sent");
    }
}