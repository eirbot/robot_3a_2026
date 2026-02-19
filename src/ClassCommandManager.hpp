#ifndef CLASS_COMMAND_MANAGER_HPP

#include <Arduino.h>
#include "ClassAscenseur.hpp"
#include "utilities.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include <map>
#include <iostream>

extern ClassAscenseur ASC1;
extern ClassAscenseur ASC2;
extern ClassAscenseur ASC3;
extern ClassAscenseur ASC4;

class ClassCommandManager{

    public:
        ClassCommandManager();
        void StartCommandTask();

    private:
        void SendCommand(const std::string &input);
        static void CommandTask(void *param);
        void ProcessUARTData(const char *data);
        bool uart_read_line(char *buffer, size_t maxLen);
        static constexpr size_t UART_BUFFER_SIZE = 128;
        size_t uartIndex = 0;
        char uartBuffer[UART_BUFFER_SIZE];

        TaskHandle_t vManagerHandle;
};

#endif
