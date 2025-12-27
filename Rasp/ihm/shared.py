import os
import json
import socket
from flask import Flask
from flask_socketio import SocketIO

from utils import LedStrip, AudioManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR) 
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

if not os.path.exists(AUDIO_DIR): os.makedirs(AUDIO_DIR)

strategies_list = {}

def load_config():
    if not os.path.exists(CONFIG_PATH): return {}
    with open(CONFIG_PATH, 'r') as f: return json.load(f)

def save_config(new_cfg):
    global cfg
    cfg.update(new_cfg)
    with open(CONFIG_PATH, 'w') as f: json.dump(cfg, f, indent=4)

cfg = load_config()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = 'secret_robot_2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Hardware
leds = LedStrip(enabled=cfg.get("leds_enabled", True))
audio = AudioManager(cfg.get("audio", {}))

# Etat Global Partagé
state = {
    "team": cfg.get("team", "BLEUE"),
    "score_current": 0,
    "match_running": False,
    "match_finished": False,
    "timer_str": "100.0",
    "start_time": None,
    "tirette": "NON-ARMED",
    "lidar_enabled": cfg.get("lidar_enabled", True),
    "music_enabled": cfg.get("music_enabled", True),
    "leds_enabled": cfg.get("leds_enabled", True),
    "manual_score_enabled": cfg.get("manual_score_enabled", True),
    "strat_id": "strat_homologation", 
    "fsm_state": "INIT",
    "strat_mode": cfg.get("strat_mode", "DYNAMIC"),
    "strat_id": cfg.get("strat_id", 1)
}

# Position Robot Partagée (Mise à jour par le Main, Lue par l'IHM)
robot_pos = {'x': 1500, 'y': 1000, 'theta': 0}

def send_led_cmd(cmd):
    if not state["leds_enabled"]: return
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.sendto(cmd.encode(), "/tmp/ledsock")
        sock.close()
    except: pass