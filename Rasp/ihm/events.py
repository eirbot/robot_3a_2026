# ihm/events.py
import os
import time
from ihm.shared import socketio, state, cfg, save_config, send_led_cmd, audio, robot_pos

STRAT_POINTS = {1: 10, 2: 25, 3: 40}

def get_strat_score(sid):
    return STRAT_POINTS.get(int(sid), 0)

# --- SOCKET HANDLERS ---
@socketio.on('connect')
def handle_connect(): socketio.emit('state_update', state)

@socketio.on('map_connect')
def handle_map_connect(): socketio.emit('robot_position', robot_pos)

@socketio.on('update_score')
def handle_update_score(data):
    if not state["match_running"] and state["manual_score_enabled"]:
        state["score_current"] = max(0, state["score_current"] + int(data.get('delta', 0)))
        socketio.emit('state_update', state)

@socketio.on('update_config')
def handle_config(data):
    changed = False
    keys = ['lidar_enabled', 'music_enabled', 'leds_enabled', 'manual_score_enabled', 'strat_mode', 'strat_id']
    old_mode = state.get('strat_mode')
    old_id = state.get('strat_id')
    
    for k in keys:
        if k in data:
            state[k] = data[k]; changed = True
            
    if not state['match_running'] and state['strat_mode'] == 'STATIC':
        if old_mode != 'STATIC' or old_id != state['strat_id']:
            state['score_current'] = get_strat_score(state['strat_id'])

    if changed:
        save_config({k: state[k] for k in keys if k in state})
        socketio.emit('state_update', state)

@socketio.on('action')
def handle_action(data):
    perform_action(data.get('cmd'))

# --- LOGIQUE MATCH ---
def perform_action(cmd):
    if cmd == 'team':
        state["team"] = "JAUNE" if state["team"] == "BLEUE" else "BLEUE"
        save_config({"team": state["team"]})
        send_led_cmd(f"TEAM:{state['team']}")
        
    elif cmd == 'start':
        if not state["match_running"]:
            state["match_running"] = True
            state["match_finished"] = False
            state["start_time"] = time.time()
            if state['score_current'] == 0 and state['strat_mode'] == 'STATIC':
                 state['score_current'] = get_strat_score(state['strat_id'])
            if state["music_enabled"] and audio: audio.stop(); audio.play('match', loop=True)
            send_led_cmd("MATCH_START")
            
    elif cmd == 'stop':
        if state["match_running"]:
            state["match_running"] = False
            if state["music_enabled"] and audio: audio.stop(); audio.play('end')
            send_led_cmd("MATCH_STOP")

    elif cmd == 'reset':
        state["match_running"] = False; state["match_finished"] = False
        state["score_current"] = get_strat_score(state['strat_id']) if state['strat_mode'] == 'STATIC' else 0
        state["timer_str"] = "100.0"; state["start_time"] = None
        state["tirette"] = "NON-ARMED"
        send_led_cmd("OFF")
        if state["music_enabled"] and audio: audio.stop(); audio.play('intro')

    elif cmd == 'reboot': os.system("sudo reboot")
    elif cmd == 'shutdown': os.system("sudo shutdown now")
    
    socketio.emit('state_update', state)