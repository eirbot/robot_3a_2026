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

struct ActionneurTargets {
    const char* name;
    Actionneur* instance;
};

static const ActionneurTargets targets[] = {
    {"ACT1", &ACT1},
    {"ACT2", &ACT2},
    {"ACT3", &ACT3},
    {"ACT4", &ACT4}
};

void ClassCommandManager::SendCommand(const std::string &input) {
    // Split TRG/CMD
    size_t pos1 = input.find('/');
    size_t pos2 = input.find('/', pos1 + 1);
    if (pos1 == std::string::npos || pos2 == std::string::npos) {
        return;}

    std::string trg = input.substr(0, pos1);
    std::string cmd = input.substr(pos1 + 1, pos2 - pos1 - 1);

    for (const auto& t : targets) {
        if (trg == t.name) {
        t.instance->queue_command(cmd.c_str());
        break;
        }
    }
}