#!/bin/bash

# Petit délai pour s'assurer que le serveur X est bien chaud (optionnel mais recommandé sur les robots)
sleep 1

# 1. Définir sur quel écran on veut afficher (l'écran HDMI du robot est toujours :0)
export DISPLAY=:0

# 2. Indiquer où se trouve la "clé" pour avoir le droit d'afficher
# (C'est généralement dans le home de l'utilisateur connecté graphiquement)
export XAUTHORITY=/home/eirbot/.Xauthority

# 3. Logs pour savoir ce qui se passe
echo "--- Lancement manuel ou service ---" >> /var/log/ihm.log
date >> /var/log/ihm.log

# 4. Lancement du programme
# On utilise 'exec' pour que le processus Python remplace le shell (plus propre pour les signaux d'arrêt)
exec /home/eirbot/Documents/robot_3a_2026/.venv/bin/python /home/eirbot/Documents/robot_3a_2026/main_robot.py
