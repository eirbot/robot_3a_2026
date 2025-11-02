#!/bin/bash
set -e

echo "🔧 [1/8] Mise à jour du système..."
sudo apt update -y
sudo apt install -y python3-pip python3-tk python3-pygame git

echo "📁 [2/8] Création de l’arborescence..."
sudo mkdir -p /home/pi/eirbot/ihm/systemd
sudo mkdir -p /home/pi/eirbot/ihm/audio
cd /home/pi/eirbot/ihm

echo "🐍 [3/8] Installation des dépendances Python..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "gpiozero==2.0" > requirements.txt
    echo "rpi_ws281x==5.0.0" >> requirements.txt
    echo "pygame==2.5.2" >> requirements.txt
    pip install -r requirements.txt
fi

echo "🔌 [4/8] Configuration des permissions série..."
sudo usermod -a -G dialout pi

echo "🔗 [5/8] Création des règles udev pour les ESP32..."
sudo bash -c 'cat > /etc/udev/rules.d/99-esp32.rules <<EOF
# Règles ESP32 : attribution de noms fixes
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="esp32_motors"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea61", SYMLINK+="esp32_arms"
EOF'

sudo udevadm control --reload-rules
sudo udevadm trigger

echo "🪩 [6/8] Copie du service systemd..."
if [ -f systemd/ihm.service ]; then
    sudo cp systemd/ihm.service /etc/systemd/system/ihm.service
else
    echo "⚠️ Aucun service trouvé, création d’un service par défaut..."
    sudo bash -c 'cat > /etc/systemd/system/ihm.service <<EOF
[Unit]
Description=Eirbot Control Interface (IHM)
After=network.target sound.target

[Service]
User=pi
WorkingDirectory=/home/pi/eirbot/ihm
ExecStart=/usr/bin/python3 /home/pi/eirbot/ihm/main.py
Restart=always
RestartSec=2
StandardOutput=append:/var/log/ihm.log
StandardError=append:/var/log/ihm.log

[Install]
WantedBy=multi-user.target
EOF'
fi

sudo systemctl daemon-reload
sudo systemctl enable ihm.service

echo "🎧 [7/8] Activation du son sur jack (désactivation HDMI si besoin)..."
sudo raspi-config nonint do_audio 1  # force sortie jack
sudo amixer set PCM 90%

echo "🚀 [8/8] Démarrage du service IHM..."
sudo systemctl start ihm.service
sudo systemctl status ihm.service --no-pager

echo "✅ Installation terminée !"
echo "→ Service : ihm.service"
echo "→ Dossiers : /home/pi/eirbot/ihm/"
echo "→ Ports : /dev/esp32_motors /dev/esp32_arms /dev/ttyUSB0 (Lidar)"
