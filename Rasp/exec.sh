#!/bin/bash

# Petit délai pour s'assurer que le serveur X est bien chaud (optionnel mais recommandé sur les robots)
sleep 1

echo "Démarrage du robot Eirbot 2026..." >> /var/log/ihm.log

# On utilise le python du venv
DISPLAY=:0 /home/eirbot/Documents/robot_3a_2026/.venv/bin/python /home/eirbot/Documents/robot_3a_2026/main_robot.py