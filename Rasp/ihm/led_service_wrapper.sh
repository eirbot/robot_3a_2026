#!/bin/bash
# Wrapper pour exécuter le contrôle LED en sudo avec la venv Python
source /home/eirbot/Documents/robot_3a_2026/.venv/bin/activate
python3 /home/eirbot/Documents/robot_3a_2026/ihm/led_service.py "$@"
