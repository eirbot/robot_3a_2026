# ihm/events.py
import ihm.shared as shared 
from ihm.shared import socketio

# --- GESTION CONNEXION ---

@socketio.on('connect')
def handle_connect(auth=None): # <--- AJOUT DE auth=None pour éviter le TypeError
    print(f"[IHM] Client connecté.")
    # 1. Envoie l'état global
    socketio.emit('state_update', shared.state)
    # 2. Envoie la liste des stratégies disponibles
    socketio.emit('strategies_list', shared.strategies_list)
    # 3. Envoie les infos système initiales
    # (optionnel, elles arriveront à la prochaine boucle de toute façon)

@socketio.on('disconnect')
def handle_disconnect():
    print("[IHM] Client déconnecté.")

# --- COMMANDES ROBOT (ACTION) ---

@socketio.on('action')
def handle_action(data):
    cmd = data.get('cmd')
    print(f"[IHM] Action reçue : {cmd}")
    
    if cmd == 'start':
        shared.state['match_running'] = True
        shared.state['match_finished'] = False
        if shared.state['start_time'] is None:
            import time
            shared.state['start_time'] = time.time()
            
    elif cmd == 'stop':
        shared.state['match_running'] = False
        # On ne met pas finished à True pour permettre de reprendre si erreur
        
    elif cmd == 'reset':
        shared.state['match_running'] = False
        shared.state['match_finished'] = False
        shared.state['start_time'] = None
        shared.state['score_current'] = 0
        shared.state['timer_str'] = "100.0"
        shared.state['fsm_state'] = "WAIT_START"
        
    elif cmd == 'team':
        # Bascule Bleu <-> Jaune
        if shared.state['team'] == "BLEUE":
            shared.state['team'] = "JAUNE"
        else:
            shared.state['team'] = "BLEUE"
            
    # Mise à jour immédiate de l'interface pour réactivité
    socketio.emit('state_update', shared.state)

# --- CONFIGURATION ---

@socketio.on('update_config')
def handle_config(data):
    # Mise à jour des clés reçues
    for key, val in data.items():
        if key in shared.state:
            shared.state[key] = val
            
    # Si on change de stratégie, on peut logguer
    if 'strat_id' in data:
        print(f"[IHM] Stratégie changée pour : {data['strat_id']}")

    # On renvoie l'état à tout le monde pour synchroniser
    socketio.emit('state_update', shared.state)

# --- SCORE MANUEL ---

@socketio.on('update_score')
def handle_score(data):
    delta = int(data.get('delta', 0))
    shared.state['score_current'] += delta
    if shared.state['score_current'] < 0: shared.state['score_current'] = 0
    socketio.emit('state_update', shared.state)

# --- INFO CARTE (Optionnel) ---
@socketio.on('map_connect')
def handle_map_connect():
    # Envoie la position actuelle du robot quand on ouvre la page Map
    socketio.emit('robot_position', shared.robot_pos)