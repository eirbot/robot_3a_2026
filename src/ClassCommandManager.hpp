#ifndef CLASS_COMMAND_MANAGER_HPP

#include <Arduino.h>
#include "utilities.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include <map>
#include <iostream>

#include "ClassActionneur.hpp"

extern Actionneur ACT1;
extern Actionneur ACT2;
extern Actionneur ACT3;
extern Actionneur ACT4;

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

        TaskHandle_t vManagerHandle;
};

#endif
