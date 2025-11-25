#!/bin/bash
set -e

USER_NAME="eirbot"
PROJECT_DIR="/home/$USER_NAME/Documents/robot_3a_2026"
IHM_DIR="$PROJECT_DIR/ihm"
VENV_DIR="$PROJECT_DIR/.venv"

echo "[1/9] Mise à jour du système..."
sudo apt update -y
sudo apt install -y python3-pip python3-venv python3-tk python3-pygame git

echo "[2/9] Vérification de la structure du projet..."
sudo mkdir -p "$IHM_DIR/systemd"
sudo mkdir -p "$IHM_DIR/audio"
sudo chown -R $USER_NAME:$USER_NAME "$PROJECT_DIR"
cd "$IHM_DIR"

echo "[3/9] Vérification ou création de l'environnement virtuel global..."
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Aucun environnement valide trouvé, création de $VENV_DIR"
    rm -rf "$VENV_DIR"
    python3 -m venv --system-site-packages "$VENV_DIR"
    echo "Environnement virtuel créé."
else
    echo "Environnement virtuel déjà présent."
fi

# Activation de la venv
source "$VENV_DIR/bin/activate"

echo "[4/9] Installation des dépendances Python..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "gpiozero==2.0" > requirements.txt
    echo "rpi_ws281x==5.0.0" >> requirements.txt
    echo "pygame==2.5.2" >> requirements.txt
    pip install -r requirements.txt
fi

echo "[5/9] Configuration des permissions série..."
sudo usermod -a -G dialout $USER_NAME

echo "[6/9] Création des règles udev pour les ESP32..."
sudo bash -c 'cat > /etc/udev/rules.d/99-esp32.rules <<EOF
# Règles ESP32 : attribution de noms fixes
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="esp32_motors"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea61", SYMLINK+="esp32_arms"
EOF'

sudo udevadm control --reload-rules
sudo udevadm trigger

echo "[7/9] Copie du service systemd..."
if [ -f systemd/ihm.service ]; then
    sudo cp systemd/ihm.service /etc/systemd/system/ihm.service
else
    echo "Aucun service trouvé, création d’un service par défaut..."
    sudo bash -c "cat > /etc/systemd/system/ihm.service <<EOF
[Unit]
Description=Eirbot Control Interface (IHM)
After=network.target sound.target

[Service]
User=$USER_NAME
WorkingDirectory=$IHM_DIR
ExecStart=$VENV_DIR/bin/python3 $IHM_DIR/main.py
Restart=always
RestartSec=2
StandardOutput=append:/var/log/ihm.log
StandardError=append:/var/log/ihm.log

[Install]
WantedBy=multi-user.target
EOF"
fi

sudo systemctl daemon-reload
sudo systemctl enable ihm.service

echo "[8/9] Activation du son sur jack..."
sudo raspi-config nonint do_audio 1
sudo amixer cset numid=4 1 || true


echo "[9/9] Démarrage du service IHM..."
sudo systemctl start ihm.service
sudo systemctl status ihm.service --no-pager

echo "Installation terminée !"
echo "→ Service : ihm.service"
echo "→ Dossier IHM : $IHM_DIR"
echo "→ Environnement virtuel : $VENV_DIR"
echo "→ Ports : /dev/esp32_motors /dev/esp32_arms /dev/ttyUSB0 (Lidar)"
