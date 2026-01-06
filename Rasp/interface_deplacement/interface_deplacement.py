import serial
import time
import json
import ast
import glob
import sys
import numpy as np
import math
from serial.serialutil import SerialException

# On importe les données partagées pour mettre à jour le site web
import ihm.shared as shared

def find_esp32_port():
    """Cherche le port série de l'ESP32"""
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    else:
        ports = []
    if len(ports) > 0: return ports[0]
    return None

def envoyer(message):
    """
    Envoie une trajectoire ou une commande.
    Compatible avec main_motor.cpp (attend 'trajectoryFinished').
    """
    if len(message) != 0:
        port = find_esp32_port()
        if port:
            # print(f"[COM] ESP32 sur {port}")
            pass
        else:
            print("[COM] Pas d'ESP32 (Mode Simulation).")
            return

        try:
            with serial.Serial(port=port, baudrate=115200, timeout=1) as ser:
                time.sleep(0.1) # Laisser le temps au port

                # --- CAS 1 : ENVOI TRAJECTOIRE (Liste de points) ---
                if not isinstance(message, str):
                    # Conversion en numpy array pour être sûr
                    trajectoire_bezier_mm = np.array(message)
                    
                    # Cible finale pour double vérification
                    cible_x = trajectoire_bezier_mm[-1][0]
                    cible_y = trajectoire_bezier_mm[-1][1]
                    
                    # Envoi du JSON
                    json_str = json.dumps(trajectoire_bezier_mm.tolist())
                    ser.write((json_str + '\n').encode())
                    print(f"[COM] Trajectoire envoyée ({len(trajectoire_bezier_mm)} pts).")
                    
                    # Boucle bloquante jusqu'à l'arrivée
                    while True:
                        line = ser.readline().decode(errors="ignore").strip()
                        if line:
                            # 1. Retour Position : "[x, y, theta]" (Mètres)
                            if line.startswith('[') and line.endswith(']'):
                                try:
                                    # Le C++ envoie des mètres : [0.250, 1.000, 0.0]
                                    pos = ast.literal_eval(line)
                                    
                                    # Mise à jour Web (Conversion m -> mm)
                                    x_mm = pos[0] * 1000
                                    y_mm = pos[1] * 1000
                                    theta_deg = pos[2] * 180 / np.pi # Si C++ envoie des radians

                                    shared.robot_pos['x'] = x_mm
                                    shared.robot_pos['y'] = y_mm
                                    shared.robot_pos['theta'] = theta_deg
                                    
                                    # Sécurité distance (< 2cm)
                                    dist = math.sqrt((x_mm - cible_x)**2 + (y_mm - cible_y)**2)
                                    if dist < 20:
                                        # On est arrivé physiquement
                                        break

                                except Exception as e:
                                    print(f"[COM] Erreur parse pos: {e}")

                            # 2. Signal de fin explicite du C++
                            elif line == "trajectoryFinished":
                                print("[COM] L'ESP32 signale la fin du mouvement.")
                                break
                            
                            # 3. Debug ESP
                            elif line.startswith("BEZ"):
                                # BEZ OK ou BEZ ERR
                                pass 
                            else:
                                # print(f"[ESP] {line}")
                                pass

                # --- CAS 2 : COMMANDE TEXTE (SET POSE) ---
                elif message.startswith("SET POSE"):
                    # Récupération des valeurs actuelles (mises à jour par actions.py)
                    x_mm = shared.robot_pos['x']
                    y_mm = shared.robot_pos['y']
                    th_deg = shared.robot_pos['theta']
                    
                    # Conversion Degrés -> Radians (car ton C++ semble travailler en radians)
                    th_rad = th_deg * np.pi / 180.0

                    # Formatage pour le sscanf du C++ : "SET POSE x y theta"
                    cmd = f"SET POSE {x_mm:.2f} {y_mm:.2f} {th_rad:.4f}\n"
                    
                    ser.write(cmd.encode())
                    print(f"[COM] Reset Odom envoyé : {cmd.strip()}")

        except SerialException as e:
            print(f"[COM] Erreur Série: {e}")
        except KeyboardInterrupt:
            print("[COM] Interruption.")