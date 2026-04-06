#include "task_manager_ascenseur.hpp"

// Constructor
ClassCommandAscenseur::ClassCommandAscenseur() {
    memset(uartBuffer, 0, UART_BUFFER_SIZE);
}

// Start FreeRTOS task
void ClassCommandAscenseur::StartCommandTask() {
    xTaskCreatePinnedToCore(
        ClassCommandAscenseur::CommandTask, // Task function
        "CommandTask",                     // Name
        4096,                              // Stack size (adjust as needed)
        this,                              // Parameter
        1,                                 // Priority
        &vAscenseurHandle,                   // Task handle
        0                                  // Core ID (0 or 1)
    );
}

// FreeRTOS task
void ClassCommandAscenseur::CommandTask(void *param) {
    ClassCommandAscenseur *Ascenseur = static_cast<ClassCommandAscenseur *>(param);

    while (true) {
        if (Ascenseur->uart_read_line(Ascenseur->uartBuffer, UART_BUFFER_SIZE)) {
            Ascenseur->ProcessUARTData(Ascenseur->uartBuffer);
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}


bool ClassCommandAscenseur::uart_read_line(char *buffer, size_t maxLen) {
    while (Serial1.available()) {
        char c = Serial1.read();
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
void ClassCommandAscenseur::ProcessUARTData(const char *data) {
    if (data && *data != '\0') {
        SendCommand(std::string(data));
    }
}

struct ActionneurTargets {
    const char* name;
    AscenseurQueue* instance;
};

static const ActionneurTargets targets[] = {
    {"ASC1", &ASC1},
    {"ASC2", &ASC2},
    {"ASC3", &ASC3},
    {"ASC4", &ASC4}
};

void ClassCommandAscenseur::SendCommand(const std::string &input) {
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

