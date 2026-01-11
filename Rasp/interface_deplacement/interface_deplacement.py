import serial
import time
import json
import ast
import numpy as np
import math
from serial.serialutil import SerialException
import ihm.shared as shared

# --- CONFIGURATION ---
PORT = '/dev/esp32_motors'
BAUDRATE = 115200

# Variable globale pour garder la connexion ouverte
ser_client = None

def init():
    """
    À appeler UNE SEULE FOIS au début du main_robot.py
    Ouvre le port et attend le reboot de l'ESP.
    """
    global ser_client
    if ser_client is not None:
        return # Déjà connecté

    try:
        print(f"[COM] Connexion à l'ESP32 sur {PORT}...")
        # On ouvre le port sans DTR pour éviter certains resets, mais on gère le timing quand même
        ser_client = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=1, dsrdtr=False)
        
        # Séquence de stabilisation pour Raspberry Pi
        ser_client.dtr = False
        time.sleep(2.0) # On attend 2s UNE SEULE FOIS au démarrage
        ser_client.reset_input_buffer()
        
        print("[COM] Connexion établie et stabilisée ✅")
        return True

    except Exception as e:
        print(f"[COM] ERREUR CRITIQUE connexion : {e}")
        ser_client = None
        return False

def envoyer(message):
    global ser_client
    
    # Auto-connexion de secours si on a oublié d'appeler init()
    if ser_client is None:
        if not init():
            return # Echec total

    if len(message) == 0: return

    try:
        # --- CAS 1 : TRAJECTOIRE (LISTE) ---
        if not isinstance(message, str):
            trajectoire_bezier_mm = np.array(message)
            nb_points = len(trajectoire_bezier_mm)

            # 1. Envoi SET POSE (Position actuelle)
            # Cela recalibre l'ESP pour qu'il parte bien de là où le Python pense qu'il est
            y_mm = shared.robot_pos['y']
            x_mm = shared.robot_pos['x']
            theta_rad = shared.robot_pos['theta'] * (np.pi/180.0)
            
            cmd_pose = f"SET POSE {y_mm:.2f} {x_mm:.2f} {theta_rad:.4f}\n"
            ser_client.write(cmd_pose.encode())
            
            # Pause minime (juste pour séparer les paquets, pas pour le reboot)
            time.sleep(0.05) 

            # 2. Envoi JSON
            json_str = json.dumps(trajectoire_bezier_mm.tolist())
            ser_client.write((json_str + '\n').encode())
            
            print(f"[COM] Trajectoire envoyée ({nb_points} pts).")
            
            # --- BOUCLE DE SUIVI (Bloquante mais réactive) ---
            msg = ""
            start_wait = time.time()
            
            # Phase A : Attente validation "BEZ OK"
            while "BEZ OK" not in msg:
                if time.time() - start_wait > 5:
                    print("[COM] Timeout: Pas de BEZ OK (Liaison perdue ?)")
                    return
                
                try:
                    line = ser_client.readline().decode(errors="ignore").strip()
                    if line: msg = line
                except: pass

            print("[COM] Trajectoire validée.")

            # Phase B : Attente Fin Mouvement
            while True:
                try:
                    line = ser_client.readline().decode(errors="ignore").strip()
                except: break

                if line:
                    # Condition de sortie 1 : "trajectoryFinished"
                    if "trajectoryFinished" in line:
                        break

                    # Condition de sortie 2 : Index dépassé (Fix précédent)
                    if "currentIdx" in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            try:
                                current_idx = int(parts[-1].strip())
                                if current_idx >= nb_points:
                                    break # On est arrivé au bout
                            except: pass

                    # Mise à jour position temps réel
                    if line.startswith('[') and line.endswith(']'):
                        try:
                            msg_list = ast.literal_eval(line)
                            shared.robot_pos['x'] = msg_list[0] * 1000
                            shared.robot_pos['y'] = msg_list[1] * 1000
                            shared.robot_pos['theta'] = msg_list[2] * 180 / np.pi
                        except: pass

        # --- CAS 2 : COMMANDE TEXTE (ex: "SET POSE ...") ---
        elif isinstance(message, str):
            ser_client.write((message + '\n').encode())
            print(f"[COM] Cmd: {message}")

    except Exception as e:
        print(f"[COM] Erreur durant l'envoi : {e}")
        # En cas d'erreur grave, on tente de fermer pour forcer une réouverture propre au prochain appel
        try:
            ser_client.close()
        except: pass
        ser_client = None