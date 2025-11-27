# Robot 3A 2026

Projet de robot autonome pour la coupe de robotique 2026. Le système combine un microcontrôleur ESP32 pour le contrôle des actionneurs et des moteurs, avec une Raspberry Pi pour l'interface utilisateur et la localisation via LiDAR.

## 📋 Architecture du Projet

```
robot_3a_2026/
├── src/                          # Code ESP32 (C++)
│   ├── ClassMotors.*             # Contrôle des moteurs
│   ├── ClassActionneur.*         # Gestion des actionneurs
│   ├── ClassAscenseur.*          # Ascenseur spécialisé
│   ├── TrajectoryFollower.*      # Suivi de trajectoire
│   ├── main_actionneur.cpp       # Point d'entrée actionneurs
│   ├── main_motor.cpp            # Point d'entrée moteurs
│   └── main_test.cpp             # Tests unitaires
├── Rasp/                         # Code Raspberry Pi (Python)
│                                  # ⚠️ Synchronisé en SFTP sur la Rasp - À exécuter sur le robot
│   ├── ihm/                      # Interface Homme-Machine
│   │   ├── main.py               # Application UI principale
│   │   ├── ui_manager.py         # Gestion de l'interface
│   │   ├── leds_manager.py       # Contrôle des LEDs WS281x
│   │   ├── audio_manager.py      # Gestion du son
│   │   ├── gpio_input.py         # Gestion des boutons
│   │   └── config.json           # Configuration
│   ├── interface_deplacement/    # Contrôle du déplacement
│   │   ├── ClassRobot.py         # Classe robot
│   │   ├── ClassDialogue.py      # Communication ESP32
│   │   ├── ClassPoint.py         # Gestion des points/trajectoires
│   │   ├── bezier.py             # Courbes de Bézier
│   │   └── esp32_detect.py       # Détection du port ESP32
│   ├── LiDAR/                    # Localisation par LiDAR
│   │   ├── lidar_localizer.py    # Localisation de base
│   │   ├── ekf_localizer.py      # Filtre de Kalman étendu
│   │   ├── rplidar_c1m1.py       # Interface LiDAR
│   │   └── test_*.py             # Tests
│   ├── strat/                    # Stratégies de match
│   ├── requirements.txt          # Dépendances Python
│   └── init.sh                   # Script d'initialisation
├── platformio.ini                # Configuration PlatformIO
└── docu/                         # Documentation

```

## 🔧 Composants Matériques

### Microcontrôleur (ESP32)
- **Moteurs** : Contrôle via AccelStepper et drivers
- **Actionneurs** : 
  - Pistons électriques pour l'agrippement des éléments de jeu
  - Servo moteurs pour la rotation des éléments
- **Ascenseur** : Module dédié
- **Communication** : UART avec Raspberry Pi

### Raspberry Pi
- **Écran tactile** : Interface 800x480
- **LEDs** : Bande WS281x adressable (60 LEDs)
- **Audio** : Sortie stéréo
- **Boutons** : UP, DOWN, SELECT, BACK
- **LiDAR** : RPLiDAR C1M1
- **Capteurs** : INA226 (consommation électrique)

## 🚀 Installation et Configuration

### Prérequis ESP32
- PlatformIO CLI ou VS Code + extension PlatformIO
- Board : ESP32-DevKit-C

### Prérequis Raspberry Pi
- Python 3.7+
- Raspberry Pi OS (ou équivalent)

### Installation des dépendances Python

⚠️ **Sur la Raspberry Pi** (après synchronisation SFTP) :
```bash
cd /path/to/robot
source init.sh
```

**Dépendances incluses :**
- `gpiozero` : Gestion GPIO
- `rpi_ws281x` : Contrôle LEDs WS281x
- `matplotlib` : Visualisation données
- `smbus2` : Communication I2C
- `psutil` : Informations système
- `pygame` : Interface graphique avancée

## 📦 Compilation et Déploiement

### Environnements PlatformIO

#### Actionneur (ESP32)
```bash
platformio run -e Actionneur -t upload
```
Compile et téléverse le firmware de contrôle des actionneurs.

#### Moteurs (ESP32)
```bash
platformio run -e Motor -t upload
```
Compile et téléverse le firmware de contrôle des moteurs.

#### Tests (ESP32)
```bash
platformio run -e Test -t upload
```
Compile et téléverse les tests unitaires.

### Rasp - Interface Utilisateur
```bash
cd /ihm
python main.py
```

Débute l'interface utilisateur avec :
- Affichage de l'état du robot
- Contrôle des systèmes
- Musique d'intro/match
- Animations LED

### Déploiement sur Raspberry Pi

⚠️ **Important** : Le dossier `Rasp/` est synchronisé en SFTP vers la Raspberry Pi. 
Les scripts doivent être exécutés **directement sur le robot**, pas en local.

**Synchronisation du code** (via VS Code SFTP) :
1. Ouvrir la palette de commandes : `Ctrl+Maj+P`
2. Exécuter : `SFTP: Config`
3. Configurer les paramètres de connexion dans `sftp.json`
4. Synchroniser automatiquement les fichiers lors des modifications

**Sur la Raspberry Pi** :
```bash
cd /path/to/robot/Rasp
source init.sh
cd ihm
python main.py
```

## 🎛️ Configuration

### `Rasp/ihm/config.json`
Configuration centralisée de l'interface :
- **Team** : Couleur de l'équipe (BLEUE)
- **GPIO** : Numéros des pins des boutons
- **LEDs** : Configuration adressable (60 LEDs, pin GPIO 18)
- **Audio** : Activation/volume et pistes disponibles
- **UI** : Dimensions de l'écran (800x480)

## 📡 Système de Localisation

### LiDAR (RPLiDAR C1M1)
Le robot utilise un LiDAR pour la localisation autonome :

**Localisation simple** (`lidar_localizer.py`)
- Scan 360° des obstacles
- Détection de points de repère

**Filtre de Kalman Étendu** (`ekf_localizer.py`)
- Fusion odométrie + LiDAR
- Estimation robuste de position/orientation

## 🎮 Contrôle et Interface

### Boutons physiques GPIO
```
UP      (GPIO 17)  → Navigation menu haut
DOWN    (GPIO 27)  → Navigation menu bas
SELECT  (GPIO 22)  → Sélection/validation
BACK    (GPIO 23)  → Retour menu
START   (GPIO 5)   → Démarrage match
STOP    (GPIO 6)   → Arrêt d'urgence
```

### Indicateurs visuels
- **Bande LED** : États du robot (mode, prêt, en action)
- **Écran tactile** : Menus, configuration, feedback temps réel

## 🔌 Communication ESP32-Rasp

Communication via UART (ClassDialogue.py) :
- Envoi de commandes de mouvement
- Retour d'état des moteurs/actionneurs
- Synchronisation temps réel

## 📊 Suivi de Trajectoire

**TrajectoryFollower** : Suivi de courbes lisses via :
- Décélération progressive
- Correction PID des erreurs
- Courbes de Bézier pour trajectoires optimales

## 🧪 Tests et Débogage

### Tests ESP32
```bash
platformio run -e Test -t upload
platformio device monitor
```

### Tests Localisation
```bash
cd Rasp/LiDAR
python test_lidar.py      # Test interface LiDAR
python test_ekf.py        # Test filtre de Kalman
```

## 📝 Fichiers Importants

| Fichier | Rôle |
|---------|------|
| `src/ClassMotors.*` | Gestion moteurs pas-à-pas |
| `src/ClassActionneur.*` | Interface générique actionneurs |
| `src/ClassAscenseur.*` | Contrôle ascenseur dédié |
| `Rasp/ihm/main.py` | Point d'entrée IHM |
| `Rasp/interface_deplacement/ClassRobot.py` | Classe maître du robot |
| `Rasp/LiDAR/ekf_localizer.py` | Localisation avancée |

## 📄 Licence

Projet EIRBOT - Coupe de Robotique 2026

## 👥 Équipe

STGT - Équipe de Robotique ENSEIRB

---

**Dernière mise à jour** : Novembre 2025
