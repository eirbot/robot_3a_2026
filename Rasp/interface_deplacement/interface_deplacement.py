import serial
import time
import json
import ast
import numpy as np
import threading
import ihm.shared as shared
from interface_deplacement.esp32_detect import find_esp32_port

_serial_lock = threading.Lock()
_ser = None

def init():
    global _ser
    port = find_esp32_port()
    if not port:
        print("[COM] Aucun ESP32 détecté au démarrage.")
        return None

    print(f"[COM] Ouverture permanente du port {port}...")
    try:
        _ser = serial.Serial(port=port, baudrate=115200, timeout=1)
        time.sleep(2.0) # Pause indispensable pour laisser l'ESP booter
        _ser.reset_input_buffer()
        _ser.reset_output_buffer()
        print("[COM] Port série prêt pour le match !")
    except Exception as e:
        print(f"[COM] Erreur critique à l'ouverture du port : {e}")

def envoyer(message):
    global _ser
    if len(message) == 0:
        return False

    with _serial_lock:
        if _ser is None or not _ser.is_open:
            init()
            if _ser is None or not _ser.is_open:
                return False

        try:
            _ser.reset_input_buffer()

            if isinstance(message, str):
                # --- COMMANDES TEXTE ---
                cmd = message.strip() + '\n'
                _ser.write(cmd.encode())
                _ser.flush()
                print(f"[COM->ESP] {message.strip()}")
                
                if message.startswith("SET POSE"):
                    try:
                        parts = message.split()
                        shared.robot_pos['y'] = float(parts[2]) / 1000.0 if float(parts[2]) > 10 else float(parts[2])
                        shared.robot_pos['x'] = float(parts[3]) / 1000.0 if float(parts[3]) > 10 else float(parts[3])
                        shared.robot_pos['theta'] = float(parts[4]) * (180.0 / np.pi)
                    except: pass
                time.sleep(0.05)
                return True

            elif isinstance(message, (list, np.ndarray)):
                # --- TRAJECTOIRES BEZIER ---
                trajectoire_bezier_mm = np.array(message)
                
                # 1. Envoi du SET POSE
                cur_y = shared.robot_pos.get('y', 0)
                cur_x = shared.robot_pos.get('x', 0)
                cur_th = shared.robot_pos.get('theta', 0)
                
                y_mm = cur_y * 1000.0 if cur_y < 10 else cur_y
                x_mm = cur_x * 1000.0 if cur_x < 10 else cur_x
                th_rad = cur_th * np.pi / 180.0
                
                pose_cmd = f"SET POSE {y_mm:.1f} {x_mm:.1f} {th_rad:.4f}\n"
                _ser.write(pose_cmd.encode())
                _ser.flush()
                print(f"[COM->ESP] SYNC: {pose_cmd.strip()}")
                
                time.sleep(0.1) # Laisse le temps à l'ESP de traiter le SET POSE

                # 2. ENVOI DE LA TRAJECTOIRE BRUTE (Comme ton code original)
                traj_esp = trajectoire_bezier_mm.copy()
                if traj_esp.shape[1] >= 2:
                    traj_esp[:, [0, 1]] = traj_esp[:, [1, 0]] # Inversion X/Y
                
                json_str = json.dumps(traj_esp.tolist())
                print(f"[COM->ESP] Envoi trajectoire: {len(traj_esp)} pts")
                
                _ser.write((json_str + '\n').encode())
                _ser.flush()
                
                # 3. ATTENTE BEZ OK (Timeout large de 15 secondes)
                print("[DEBUG] Attente de BEZ OK...")
                msg = ""
                start_time = time.time()
                
                while msg != "BEZ OK":
                    if time.time() - start_time > 15.0:
                        print("[COM] ERREUR: Timeout de 15s dépassé en attendant BEZ OK.")
                        return False
                        
                    raw = _ser.readline()
                    msg = raw.decode(errors="ignore").strip()
                    if msg:
                        print(f"[ESP32] {msg}")
                        if "BEZ ERR" in msg:
                            return False
                        if msg == "BEZ OK":
                            break
                    
                # 4. ATTENTE FIN DE TRAJET (Infini, comme le manual_remote)
                print("[DEBUG] En route... attente de trajectoryFinished")
                while msg != "trajectoryFinished":
                    raw = _ser.readline()
                    msg = raw.decode(errors="ignore").strip()
                    if msg:
                        if msg.startswith('[') and not msg.startswith('[E'):
                            try:
                                msg_list = ast.literal_eval(msg)
                                shared.robot_pos['x'] = msg_list[0]
                                shared.robot_pos['y'] = msg_list[1]
                                shared.robot_pos['theta'] = msg_list[2] * 180 / np.pi
                            except: pass
                        elif "trajectoryFinished" in msg:
                            print("[COM] Trajectoire terminée avec succès !")
                            break
                        else:
                            print(f"[ESP32] {msg}")
                return True

        except serial.SerialException as e:
            print(f"[COM] Erreur série : {e}")
            if _ser:
                _ser.close()
            return False

def wait_idle(timeout=10.0):
    return True

def is_ready():
    global _ser
    return _ser is not None and _ser.is_open