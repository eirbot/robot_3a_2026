# ihm/tasks.py
import time
import psutil
import os
import numpy as np
from ihm.shared import socketio, state, audio, send_led_cmd, robot_pos
from utils import get_ip, get_battery_voltage, get_cpu_temp

def background_loop():
    angle_simu = 0
    while True:
        # 1. Timer Match
        if state["match_running"] and state["start_time"]:
            elapsed = time.time() - state["start_time"]
            remaining = 100.0 - elapsed
            if remaining <= 0:
                state["timer_str"] = "0.0"; state["match_running"] = False; state["match_finished"] = True
                if state["music_enabled"] and audio: audio.stop(); audio.play('end')
                send_led_cmd("MATCH_STOP"); socketio.emit('state_update', state)
            else:
                state["timer_str"] = f"{remaining:.1f}"; socketio.emit('state_update', state)

        # 2. Infos Système
        devs = {
            'lidar': os.path.exists('/dev/ttyUSB0'),
            'esp_motors': os.path.exists('/dev/esp32_motors'),
            'esp_arms': os.path.exists('/dev/esp32_arms'),
            'camera': False # A connecter avec l'objet camera si on veut le status précis
        }
        
        socketio.emit('sys_info', {
            'cpu': f"{psutil.cpu_percent()}%", 
            'temp': get_cpu_temp(),
            'volt': get_battery_voltage(), 
            'current': "0.50",
            'ip': get_ip(), 
            'devs': devs
        })
        socketio.sleep(0.1) # 10Hz