#ifndef CLASS_ASCENSEUR_MANAGER_HPP

#include <Arduino.h>
#include "utilities.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include <map>
#include <iostream>

#include "ClassAscenseurQueue.hpp"

extern AscenseurQueue ASC1;
extern AscenseurQueue ASC2;
extern AscenseurQueue ASC3;
extern AscenseurQueue ASC4;

class ClassCommandManager{

    public:
        ClassCommandManager(); // CONSTRUCTOR
        void StartCommandTask(); // CREATE TASK

    private:
        void SendCommand(const std::string &input); // LINK TO ACTIONNEUR METHODS
        static void CommandTask(void *param); // FREE RTOS TASK
        void ProcessUARTData(const char *data); 
        bool uart_read_line(char *buffer, size_t maxLen);
        static constexpr size_t UART_BUFFER_SIZE = 128;
        size_t uartIndex = 0;
        char uartBuffer[UART_BUFFER_SIZE];
        bool queue_command(const char* command);
        TaskHandle_t vManagerHandle;
};

#endif
