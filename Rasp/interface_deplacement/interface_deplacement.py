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

def envoyer(message):
    if len(message) == 0:
        return

    try:
        with serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=1) as ser:
            # Pause pour laisser le temps au Reset/Boot de la Pi
            time.sleep(2.0) 

            if not isinstance(message, str):
                # --- ENVOI TRAJECTOIRE ---
                trajectoire_bezier_mm = np.array(message)
                nb_points = len(trajectoire_bezier_mm) # On compte les points (ex: 50)
                
                # Envoi SET POSE
                y_mm = shared.robot_pos['y']
                x_mm = shared.robot_pos['x']
                theta_rad = shared.robot_pos['theta'] * (np.pi/180.0)
                cmd_pose = f"SET POSE {y_mm:.2f} {x_mm:.2f} {theta_rad:.4f}\n"
                ser.write(cmd_pose.encode())
                time.sleep(0.1)

                # Envoi JSON
                json_str = json.dumps(trajectoire_bezier_mm.tolist())
                ser.write((json_str + '\n').encode())
                print(f"[COM] Trajectoire ({nb_points} pts) envoyée.")
                
                # --- ATTENTE INTELLIGENTE ---
                msg = ""
                
                # 1. Attente BEZ OK
                start_wait = time.time()
                while "BEZ OK" not in msg:
                    if time.time() - start_wait > 5:
                        print("[COM] Timeout: Pas de BEZ OK")
                        return
                    line = ser.readline().decode(errors="ignore").strip()
                    if line: msg = line

                print("[COM] Trajectoire validée.")

                # 2. Suivi du mouvement
                last_idx = 0
                while True:
                    line = ser.readline().decode(errors="ignore").strip()
                    if line:
                        # Si l'ESP dit qu'il a fini
                        if "trajectoryFinished" in line:
                            print("[COM] Fin explicite reçue.")
                            break

                        # Si on voit passer l'index courant
                        if "currentIdx" in line:
                            try:
                                # On extrait le numéro : "Point suivant, currentIdx : 45"
                                parts = line.split(':')
                                if len(parts) > 1:
                                    current_idx = int(parts[-1].strip())
                                    
                                    # --- LE FIX EST ICI ---
                                    # Si l'ESP dépasse le nombre de points total (ex: 51 pour 50 pts)
                                    # On considère que c'est fini !
                                    if current_idx >= nb_points:
                                        print(f"[COM] Dernier point atteint (Idx {current_idx}). Fin forcée.")
                                        break
                            except: pass

                        # Mise à jour position [x,y,theta]
                        if line.startswith('[') and line.endswith(']'):
                            try:
                                msg_list = ast.literal_eval(line)
                                shared.robot_pos['x'] = msg_list[0] * 1000
                                shared.robot_pos['y'] = msg_list[1] * 1000
                                shared.robot_pos['theta'] = msg_list[2] * 180 / np.pi
                            except: pass

            # Cas commande texte simple
            elif isinstance(message, str):
                ser.write((message + '\n').encode())
                print(f"[COM] Commande : {message}")

    except Exception as e:
        print(f"[COM] Erreur : {e}")