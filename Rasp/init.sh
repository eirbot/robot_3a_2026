#!/bin/bash
set -e

USER_NAME="eirbot"
PROJECT_DIR="/home/$USER_NAME/Documents/robot_3a_2026"
IHM_DIR="$PROJECT_DIR/ihm"
VENV_DIR="$PROJECT_DIR/.venv"

echo "[1/9] Mise à jour du système..."
sudo apt update -y
sudo apt install -y python3-pip python3-venv python3-tk git

echo "[2/9] Vérification de la structure du projet..."
sudo mkdir -p "$IHM_DIR/systemd"
sudo mkdir -p "$IHM_DIR/audio"
sudo chown -R $USER_NAME:$USER_NAME "$PROJECT_DIR"

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
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements.txt"
else
    echo "Fichier requirements.txt introuvable dans $PROJECT_DIR."
    echo "Veuillez vérifier le chemin ou créer le fichier."
    exit 1
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

echo "[7/9] Copie des service systemd..."
if [ -f "$PROJECT_DIR/systemd/robot.service" ] && [ -f "$PROJECT_DIR/systemd/led_service.service" ]; then
    sudo cp "$PROJECT_DIR/systemd/robot.service" /etc/systemd/system/robot.service
    sudo cp "$PROJECT_DIR/systemd/led_service.service" /etc/systemd/system/led_service.service
else
    echo "Aucun service trouvé dans le dossier systemd."
    exit 1
fi
    
sudo systemctl daemon-reload
sudo systemctl enable robot.service
sudo systemctl enable led_service.service

echo "[8/9] Activation du son sur jack..."
sudo raspi-config nonint do_audio 1
# Tente de mettre le volume à 100% sur la sortie 'Headphone' ou 'PCM' (plus robuste que numid)
sudo amixer sset 'Headphone' 100% 2>/dev/null || sudo amixer sset 'PCM' 100% 2>/dev/null || echo "Info: Impossible de régler le volume via amixer (normal sur certains OS récents)"


echo "[9/9] Démarrage des service systemd..."
# sudo systemctl start ihm.service
sudo systemctl start led_service.service

echo "Installation terminée !"
echo "→ Service : robot.service led_service.service"
echo "→ Dossier Projet : $PROJECT_DIR"
echo "→ Environnement virtuel : $VENV_DIR"
