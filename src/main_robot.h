#ifndef MAIN_H
#define MAIN_H

#include "Arduino.h"
#include "common.h"
#include "ComWithRasp.hpp"

extern TaskParams Parameters;

extern unsigned long startMillis;

extern GoToPosition serialGoto;

struct Command{
    char cmd;
    const std::vector<int> &params;
};

Command BufferCommands[100];

#endif
