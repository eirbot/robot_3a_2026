#!/bin/bash
set -e

USER_NAME=$(whoami)
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
IHM_DIR="$PROJECT_DIR/ihm"
VENV_DIR="$PROJECT_DIR/.venv"

echo "[1/9] Mise à jour du système..."
sudo apt update -y
sudo apt install -y python3-pip python3-venv python3-tk git

echo "[2/9] Vérification de la structure du projet..."
sudo mkdir -p "$PROJECT_DIR/systemd"
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
    "$VENV_DIR/bin/python3" -m pip install --upgrade pip
    "$VENV_DIR/bin/python3" -m pip install -r "$PROJECT_DIR/requirements.txt"
else
    echo "Fichier requirements.txt introuvable dans $PROJECT_DIR."
fi

echo "[5/9] Configuration des permissions série..."
sudo usermod -a -G dialout $USER_NAME

echo "[6/9] Installation des dépendances pour l'affichage Web local (pywebview)"
sudo apt-get update && sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1

echo "[7/9] Configuration des services Systemd..."
# On génère le service dynamiquement pour s'adapter aux chemins réels
cat <<EOF | sudo tee /etc/systemd/system/robot_launcher.service
[Unit]
Description=Eirbot 2026 Button Launcher
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER_NAME/.Xauthority
Environment=XDG_RUNTIME_DIR=/run/user/$(id -u $USER_NAME)
ExecStart=$VENV_DIR/bin/python3 $PROJECT_DIR/launcher.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable robot_launcher.service
sudo systemctl restart robot_launcher.service
echo " -> Service robot_launcher installé et redémarré."

echo "[8/9] Activation du son (PulseAudio/PipeWire)..."
# Plus besoin de forcer raspi-config pour le jack, PipeWire gère automatiquement.
pactl set-sink-volume @DEFAULT_SINK@ 100% 2>/dev/null || echo "Info: Impossible de régler le volume par défaut"

echo "[9/9] Finalisation..."
echo "Installation terminée !"
echo "→ Utilisateur : $USER_NAME"
echo "→ Dossier Projet : $PROJECT_DIR"
