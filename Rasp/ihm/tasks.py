# ihm/tasks.py
import time
import psutil
import os
import numpy as np
# On assure d'importer robot_pos
from ihm.shared import socketio, state, audio, send_led_cmd, robot_pos 
from utils import get_ip, get_battery_voltage, get_cpu_temp, get_battery_current, get_voltage_float

def background_loop():
    print("[IHM] Background loop démarrée.")
    
    while True:
        # 1. Timer Match (inchangé)
        if state["match_running"] and state["start_time"]:
            elapsed = time.time() - state["start_time"]
            remaining = 100.0 - elapsed
            if remaining <= 0:
                state["timer_str"] = "0.0"; state["match_running"] = False; state["match_finished"] = True
                if state["music_enabled"] and audio: audio.stop(); audio.play('end')
                send_led_cmd("MATCH_STOP"); socketio.emit('state_update', state)
            else:
                state["timer_str"] = f"{remaining:.1f}"; socketio.emit('state_update', state)

        # 2. Infos Système (inchangé)
        devs = {
            'lidar': os.path.exists('/dev/lidar'),
            'esp_motors': os.path.exists('/dev/esp32_motors'),
            'esp_arms': os.path.exists('/dev/esp32_arms'),
            'camera': False 
        }
        
        volts = get_voltage_float()
        
        # --- BAU Virtuel (INA226) ---
        if volts < 3.0 and state.get("fsm_state") != "STOPPED":
             print("[TASKS] 🚨 ARRET D'URGENCE (BAU) VIA INA226 (Tension < 3V) !")
             state['match_running'] = False
             state['fsm_state'] = "STOPPED"
             state['tirette'] = "WAIT"
             send_led_cmd("COLOR:255,0,0") 
             socketio.emit('state_update', state)

        socketio.emit('sys_info', {
            'cpu': f"{psutil.cpu_percent()}%", 
            'temp': get_cpu_temp(),
            'volt': get_battery_voltage(), 
            'volt_float': volts,
            'current': get_battery_current(),
            'ip': get_ip(), 
            'devs': devs
        })

        # --- 3. Envoi Position Robot en temps réel (Map) ---
        socketio.emit('robot_position', robot_pos)

        socketio.sleep(0.1) # 10Hz (Suffisant pour une fluidité visuelle)