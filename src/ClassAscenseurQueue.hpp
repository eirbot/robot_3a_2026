#ifndef CLASS_ASCENSEUR_WRAP
#define CLASS_ASCENSEUR_WRAP

#include "ClassAscenseur.hpp"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

class AscenseurQueue {
    
    public:
        AscenseurQueue(

        // Sensor
        uint8_t snsPin,

        // Ascenseur
        uint8_t stepPin, uint8_t dirPin, String name, bool invertRotation,

        // Positions
        float initHeight, float resetHeight, float midheight, float highheight
        );

        void runSequenceDEBUG();
        
        void init(uint8_t queueLength, uint16_t stackSize, UBaseType_t priority);
        
        bool queue_command(const char* command);
        
        bool goToHeightInit();
        bool gotToHeightIntermediaire();
        bool gotoHeightRelease();
        bool init();
        bool reset();
        
    private:
        ClassAscenseur ascenseur; 
    
        TaskHandle_t taskHandle;
        QueueHandle_t commandQueue;

        float _initHeight; // init height
        float _resetHeight;
        float _midHeight;
        float _highHeight;

    
        static void taskFunction(void* pvParameters);
};

#endif