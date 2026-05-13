#!/bin/bash
echo "Démarrage du robot Eirbot 2026..." >> /var/log/ihm.log

# Configuration de l'environnement pour PulseAudio/PipeWire
export XDG_RUNTIME_DIR=/run/user/$(id -u)

# Affichage
DISPLAY=:0 /home/eirbot/Documents/robot_3a_2026/.venv/bin/python /home/eirbot/Documents/robot_3a_2026/main_robot.py