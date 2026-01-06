# ihm/routes.py
import os
import time
import cv2
import glob
import traceback # Ajouté pour voir les détails des erreurs
import serial.tools.list_ports
from flask import render_template, request, jsonify, redirect, url_for, Response
from werkzeug.utils import secure_filename
from ihm.shared import app, state, cfg, audio, save_config, send_led_cmd, AUDIO_DIR

# --- AJOUT TEMPORAIRE DEBUG ---
print("\n" + "="*40)
print("[DEBUG CONFIG CAMÉRA]")
print(f"Contenu brut de cfg['camera'] : {cfg.get('camera')}")
is_enabled = cfg.get('camera', {}).get('enabled', False)
print(f"La caméra est-elle activée ? => {is_enabled}")
print("="*40 + "\n")
# ------------------------------

# --- IMPORT CAMERA ---
# On tente d'importer la classe LibCamera proprement au début
LibCamera = None
try:
    # Assurez-vous que le fichier est bien dans utils/sensors/camera_libcamera.py
    # et que le dossier utils/sensors/ contient un fichier __init__.py
    from utils.sensors.camera_libcamera import LibCamera
except ImportError as e:
    print(f"\n[ATTENTION] Impossible d'importer la classe LibCamera : {e}")
    print("Vérifiez que 'picamera2' est installé et que le fichier existe.\n")

STRAT_DIR = os.path.join(os.getcwd(), 'strat', 'strategies')

# --- INITIALISATION CAMERA ---
cam_cfg = cfg.get("camera", {})
camera = None

if cam_cfg.get("enabled", False):
    if LibCamera is None:
        print("[ERREUR] La caméra est activée dans la config, mais la librairie est introuvable.")
    else:
        try:
            print(f"[IHM] Tentative de démarrage de la caméra...")
            print(f"      Resolution: {cam_cfg.get('width', 320)}x{cam_cfg.get('height', 240)} @ {cam_cfg.get('fps', 15)}fps")
            
            # Instanciation et démarrage
            camera = LibCamera(
                resolution=(cam_cfg.get("width", 320), cam_cfg.get("height", 240)), 
                framerate=cam_cfg.get("fps", 15)
            ).start()
            
            print("[IHM] Caméra démarrée avec succès !")
            
        except Exception as e:
            print(f"\n[ERREUR CRITIQUE CAMERA] Impossible de démarrer la caméra : {e}")
            print("Détails de l'erreur :")
            traceback.print_exc() # Affiche la ligne exacte du plantage
            camera = None

def generate_frames():
    """Générateur de flux vidéo MJPEG"""
    while True:
        # Sécurité : Si la caméra n'est pas initialisée, on arrête le générateur
        if not camera: 
            break 
            
        success, frame = camera.read()
        
        if success and frame is not None:
            try:
                # Compression JPEG pour l'envoi réseau
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                if ret:
                    yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            except Exception:
                pass
        
        # Petite pause pour ne pas saturer le CPU si on attend une image
        time.sleep(0.02)

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
        return "Camera not available (Check logs)", 404
        
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/blockly')
def blockly_interface():
    return render_template('blockly.html')

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
    code_xml = data.get('xml')

    if not filename or not code_python:
        return jsonify({'status': 'error', 'msg': 'Données manquantes'}), 400

    safe_name = filename.replace('.py', '').replace('.xml', '')
    
    try:
        py_path = os.path.join(STRAT_DIR, safe_name + ".py")
        with open(py_path, 'w') as f:
            f.write(code_python)
            
        if code_xml:
            xml_path = os.path.join(STRAT_DIR, safe_name + ".xml")
            with open(xml_path, 'w') as f:
                f.write(code_xml)

        return jsonify({'status': 'success', 'msg': f'Stratégie {safe_name} sauvegardée !'})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@app.route('/api/list_blockly_strats')
def list_blockly_strats():
    files = glob.glob(os.path.join(STRAT_DIR, "*.xml"))
    strats = [os.path.basename(f).replace('.xml', '') for f in files]
    return jsonify(strats)

@app.route('/api/load_strat/<name>')
def load_strat(name):
    safe_name = name.replace('.xml', '')
    xml_path = os.path.join(STRAT_DIR, safe_name + ".xml")
    
    if os.path.exists(xml_path):
        with open(xml_path, 'r') as f:
            content = f.read()
        return jsonify({'status': 'success', 'xml': content})
    else:
        return jsonify({'status': 'error', 'msg': 'Fichier XML introuvable'}), 404