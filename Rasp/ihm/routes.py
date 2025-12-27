# ihm/routes.py
import os
import time
import cv2
import glob
import serial.tools.list_ports
from flask import render_template, request, jsonify, redirect, url_for, Response
from werkzeug.utils import secure_filename
from ihm.shared import app, state, cfg, audio, save_config, send_led_cmd, AUDIO_DIR
from utils import ThreadedCamera

STRAT_DIR = os.path.join(os.getcwd(), 'strat', 'strategies')

# --- CAMERA ---
cam_cfg = cfg.get("camera", {})
camera = None
if cam_cfg.get("enabled", False):
    try:
        # On initialise seulement si activé
        camera = ThreadedCamera(src=cam_cfg.get("id",0), width=320, height=240, fps=15).start()
    except: pass

def generate_frames():
    while True:
        # Sécurité : Si la caméra plante ou n'existe pas, on arrête le flux
        if not camera: 
            break 
            
        success, frame = camera.read()
        if success and frame is not None:
            try:
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            except: pass
        
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
    if camera is None:
        return "Camera not available", 404
        
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/blockly')
def blockly_interface():
    return render_template('blockly.html')

# Ajoute cette route pour dire au navigateur "Pas d'icone, tout va bien"
@app.route('/favicon.ico')
def favicon():
    return "", 204

# --- API ---
@app.route('/api/upload_sound', methods=['POST'])
def upload_sound():
    if 'file' in request.files:
        f = request.files['file']
        if f.filename: f.save(os.path.join(AUDIO_DIR, secure_filename(f.filename)))
    return redirect(url_for('page_media'))

@app.route('/api/set_audio_track', methods=['POST'])
def set_audio_track():
    d = request.json
    curr = cfg.get("audio", {})
    if 'tracks' not in curr: curr['tracks'] = {}
    curr['tracks'][d['event']] = d['filename']
    save_config({"audio": curr})
    if audio: audio.load_config(curr)
    return jsonify({"status": "ok"})

@app.route('/api/led_control', methods=['POST'])
def led_control():
    d = request.json
    if d['mode'] == 'color':
        rgb = tuple(int(d['value'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        send_led_cmd(f"COLOR:{rgb[0]},{rgb[1]},{rgb[2]}")
    elif d['mode'] == 'gradient':
        c1 = tuple(int(d['c1'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        c2 = tuple(int(d['c2'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        send_led_cmd(f"GRADIENT:{c1[0]},{c1[1]},{c1[2]},{c2[0]},{c2[1]},{c2[2]}")
    return jsonify({"status": "ok"})

@app.route('/api/save_strat', methods=['POST'])
def save_strat():
    data = request.json
    filename = data.get('filename')
    code_python = data.get('code')
    code_xml = data.get('xml')  # <--- Nouveau champ

    if not filename or not code_python:
        return jsonify({'status': 'error', 'msg': 'Données manquantes'}), 400

    # Nettoyage du nom
    safe_name = filename.replace('.py', '').replace('.xml', '')
    
    try:
        # 1. Sauvegarde du Python (Pour le Robot)
        py_path = os.path.join(STRAT_DIR, safe_name + ".py")
        with open(py_path, 'w') as f:
            f.write(code_python)
            
        # 2. Sauvegarde du XML (Pour Blockly)
        if code_xml:
            xml_path = os.path.join(STRAT_DIR, safe_name + ".xml")
            with open(xml_path, 'w') as f:
                f.write(code_xml)

        return jsonify({'status': 'success', 'msg': f'Stratégie {safe_name} sauvegardée !'})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@app.route('/api/list_blockly_strats')
def list_blockly_strats():
    """Renvoie la liste des stratégies qui ont un fichier XML (donc modifiables)"""
    files = glob.glob(os.path.join(STRAT_DIR, "*.xml"))
    strats = [os.path.basename(f).replace('.xml', '') for f in files]
    return jsonify(strats)

@app.route('/api/load_strat/<name>')
def load_strat(name):
    """Renvoie le contenu XML d'une strat"""
    safe_name = name.replace('.xml', '') # Sécurité
    xml_path = os.path.join(STRAT_DIR, safe_name + ".xml")
    
    if os.path.exists(xml_path):
        with open(xml_path, 'r') as f:
            content = f.read()
        return jsonify({'status': 'success', 'xml': content})
    else:
        return jsonify({'status': 'error', 'msg': 'Fichier XML introuvable'}), 404