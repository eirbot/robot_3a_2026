#!/bin/bash
# Petit délai pour laisser le système respirer
sleep 1
echo "Démarrage du robot Eirbot 2026..." >> /var/log/ihm.log

# On force les drivers audio et affichage
export SDL_AUDIODRIVER=alsa
DISPLAY=:0 /home/eirbot/Documents/robot_3a_2026/.venv/bin/python /home/eirbot/Documents/robot_3a_2026/main_robot.py