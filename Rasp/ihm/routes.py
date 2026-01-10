# ihm/routes.py
import os
import time
import cv2
import glob
import serial.tools.list_ports
from flask import render_template, request, jsonify, redirect, url_for, Response, send_from_directory
from werkzeug.utils import secure_filename
from ihm.shared import app, state, cfg, audio, save_config, send_led_cmd, AUDIO_DIR, socketio

# --- IMPORT CAMERA ---
LibCamera = None
try:
    from utils.sensors.camera_libcamera import LibCamera
except ImportError:
    pass

STRAT_DIR = os.path.join(os.getcwd(), 'strat', 'strategies')

# --- INIT DEFAULTS CONFIG ---
if 'config' in state:
    conf = state['config']
    # On définit les valeurs par défaut si elles n'existent pas
    defaults = {
        'lidar': True, 'lidar_simu': False, 'skip_homologation': False,
        'ekf': True, 'camera': True, 'avoidance': True,
        'strat_mode': 'DYNAMIC', 'static_strat': ''
    }
    updated = False
    for k, v in defaults.items():
        if k not in conf:
            conf[k] = v
            updated = True
    
    if updated:
        state['config'] = conf # Force update du Manager

# --- CAMERA ---
cam_cfg = cfg.get("camera", {})
camera = None
if cam_cfg.get("enabled", False) and LibCamera:
    try:
        camera = LibCamera(resolution=(320, 240), framerate=15).start()
    except: camera = None

def generate_frames():
    # Compteur de sécurité pour éviter le chargement infini
    fail_count = 0
    
    while True:
        # Si l'objet caméra n'existe plus/pas
        if not camera: 
            break
            
        try:
            success, frame = camera.read()
            
            if success:
                # Reset du compteur si on a une image
                fail_count = 0
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            else:
                # Pas d'image récupérée
                fail_count += 1
                # Si on échoue 10 fois de suite (environ 0.5 seconde), on coupe le flux
                if fail_count > 10:
                    print("[CAM] Trop d'échecs de lecture, arrêt du flux.")
                    break
                    
        except Exception as e:
            print(f"[CAM] Erreur critique flux : {e}")
            break
            
        time.sleep(0.05)

# --- ROUTES ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/debug')
def page_debug():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return render_template('debug.html', state=state, ports=ports)

@app.route('/media')
def page_media():
    files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
    return render_template('media.html', files=files, audio_cfg=cfg.get("audio", {}))

@app.route('/map')
def page_map(): return render_template('map.html')

@app.route('/video_feed')
def video_feed():
    # On vérifie si l'objet camera existe ET si le driver a réussi à démarrer (running)
    if not camera or not getattr(camera, 'running', False):
        return "Camera Inactive", 404
        
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/blockly')
def blockly_interface(): return render_template('blockly.html')

@app.route('/favicon.ico')
def favicon(): return "", 204

@app.route('/audio_files/<path:filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

# --- API ---
@app.route('/api/score_edit', methods=['POST'])
def score_edit():
    # 1. Calcul du nouveau score
    current = state.get('score_current', 0)
    new_score = max(0, current + request.json.get('delta', 0))
    state['score_current'] = new_score
    socketio.emit('state_update', state)
    
    return jsonify({'status': 'ok', 'score': new_score})

@app.route('/api/action/<act>', methods=['POST'])
def handle_action(act):
    print(f"[IHM] Action: {act}")
    
    if act == 'start':
        # On donne le signal de départ, le thread strat fera la transition vers "RUNNING"
        state['match_running'] = True
        
    elif act == 'stop':
        # Arrêt d'urgence
        state['match_running'] = False
        state['fsm_state'] = 'STOPPED'
        
    elif act == 'reset': 
        # On remet l'état d'attente reconnu par main_strat
        state['fsm_state'] = 'WAIT_START' 
        state['score_current'] = 0
        state['timer_str'] = "100.0"
        state['match_finished'] = False
        state['match_running'] = False
        
    elif act == 'team':
        state['team'] = 'JAUNE' if state['team'] == 'BLEUE' else 'BLEUE'
        
    elif act == 'tirette':
        # Simule le retrait de la tirette (déclenche le start si le code strat surveille la tirette)
        # Note : Pour l'instant main_strat regarde surtout "match_running"
        state['tirette'] = "TRIGGERED"
        state['match_running'] = True # On lance aussi le match

    socketio.emit('state_update', state)
    
    return jsonify({'status': 'ok'})

@app.route('/api/config_edit', methods=['POST'])
def config_edit():
    data = request.json
    key = data.get('key')
    val = data.get('val')
    
    if 'config' in state:
        conf = state['config']
        
        # --- CORRECTION : Gestion récursive (profondeur infinie) ---
        # Permet de gérer "audio.tracks.intro", "camera.enabled", etc.
        keys = key.split('.')
        current_level = conf
        
        # On descend dans les dossiers jusqu'à l'avant-dernier
        for k in keys[:-1]:
            if k not in current_level:
                current_level[k] = {} # On crée le dossier s'il n'existe pas
            # Si jamais c'était une valeur simple, on la transforme en dict pour éviter le crash
            if not isinstance(current_level[k], dict):
                current_level[k] = {}
            current_level = current_level[k]
            
        # On assigne la valeur dans le dernier niveau
        current_level[keys[-1]] = val
        # -----------------------------------------------------------

        state['config'] = conf
        save_config(conf)
        
        # Mise à jour immédiate du module Audio (pour que le changement soit pris en compte sans reboot)
        if keys[0] == 'audio':
            audio.load_config(conf.get('audio', {}))
        
        # Gestion des triggers spéciaux (Stratégie)
        if key == 'static_strat':
            state['strat_id'] = val
        elif key == 'strat_mode' and val == 'STATIC':
            if conf.get('static_strat'):
                state['strat_id'] = conf['static_strat']
        
    return jsonify({'status': 'ok'})

@app.route('/api/save_strat', methods=['POST'])
def save_strat():
    data = request.json
    name = data['filename'].replace('.xml','').replace('.py','')
    with open(os.path.join(STRAT_DIR, name+".py"), 'w') as f: f.write(data['code'])
    with open(os.path.join(STRAT_DIR, name+".xml"), 'w') as f: f.write(data['xml'])
    return jsonify({'status': 'success'})

@app.route('/api/list_blockly_strats')
def list_strats():
    return jsonify([os.path.basename(f).replace('.xml','') for f in glob.glob(os.path.join(STRAT_DIR, "*.xml"))])

@app.route('/api/load_strat/<name>')
def load_strat(name):
    try:
        with open(os.path.join(STRAT_DIR, name+".xml"), 'r') as f: return jsonify({'status':'success','xml':f.read()})
    except: return jsonify({'status':'error'}), 404

@app.route('/api/flash_esp/<target>', methods=['POST'])
def flash(target): return jsonify({'status':'ok', 'msg': f'Flash {target} simulé'})

@app.route('/api/list_audio_files')
def list_audio_files():
    # On renvoie la liste triée
    files = sorted([f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')])
    return jsonify(files)

@app.route('/api/upload_sound', methods=['POST'])
def upload():
    if 'file' in request.files:
        f = request.files['file']
        if f.filename != '':
            f.save(os.path.join(AUDIO_DIR, secure_filename(f.filename)))
            return jsonify({'status': 'ok', 'filename': f.filename})
    return jsonify({'status': 'error'}), 400

@app.route('/api/play_test', methods=['POST'])
def play_test():
    filename = request.json.get('filename')
    # On utilise l'audio manager du robot (mpg123)
    audio.play(filename) 
    return jsonify({'status': 'ok'})

@app.route('/api/set_audio_track', methods=['POST'])
def set_track(): return jsonify({'status':'ok'}) 

@app.route('/api/led_control', methods=['POST'])
def led():
    d = request.json
    if d['mode'] == 'color': send_led_cmd(f"COLOR:{d['value']}")
    return jsonify({'status':'ok'})