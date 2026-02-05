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

echo "[6/9] Installation des dépendances pour l'affichage Web local (pywebview)"
sudo apt-get update && sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1

echo "[7/9] Copie des service systemd..."
if [ -f "$PROJECT_DIR/systemd/robot.service" ]; then
    sudo cp "$PROJECT_DIR/systemd/robot.service" /etc/systemd/system/robot.service
else
    echo "Aucun service trouvé dans le dossier systemd."
    exit 1
fi
    
sudo systemctl daemon-reload
sudo systemctl enable robot.service

echo "[8/9] Activation du son sur jack..."
sudo raspi-config nonint do_audio 1
# Tente de mettre le volume à 100% sur la sortie 'Headphone' ou 'PCM' (plus robuste que numid)
sudo amixer sset 'Headphone' 100% 2>/dev/null || sudo amixer sset 'PCM' 100% 2>/dev/null || echo "Info: Impossible de régler le volume via amixer (normal sur certains OS récents)"


echo "[9/9] Démarrage des service systemd..."
# sudo systemctl start ihm.service
# sudo systemctl start led_service.service

echo "Installation terminée !"
echo "→ Service : robot.service"
echo "→ Dossier Projet : $PROJECT_DIR"
echo "→ Environnement virtuel : $VENV_DIR"
