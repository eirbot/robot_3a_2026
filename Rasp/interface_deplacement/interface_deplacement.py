import serial
import time
import json
import ast
import numpy as np
import math
from serial.serialutil import SerialException

# On importe les données partagées
import ihm.shared as shared

# --- CONFIGURATION ---
PORT = '/dev/esp32_motors'
BAUDRATE = 115200

# Variable globale (initialement vide)
ser = None

def init():
    """
    Tente d'ouvrir la connexion série avec l'ESP32.
    À appeler une seule fois au démarrage du robot.
    Retourne True si succès, False sinon.
    """
    global ser
    
    # Si déjà ouvert, on ne fait rien
    if ser is not None:
        print("[COM] Port déjà ouvert.")
        return True

    try:
        print(f"[COM] Tentative de connexion sur {PORT}...")
        ser = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=1)
        
        # --- Séquence de démarrage propre ---
        ser.dtr = False
        time.sleep(0.1)
        ser.dtr = True
        time.sleep(1.0) # On laisse 1sec à l'ESP pour booter
        
        # On vide les logs de démarrage
        ser.reset_input_buffer()
        print("[COM] Connexion ESP32 Moteurs : OK ✅")
        return True

    except SerialException as e:
        print(f"[COM] ÉCHEC Connexion ESP32 : {e}")
        print("[COM] Passage en mode SIMULATION (pas d'envoi physique).")
        ser = None
        return False

def envoyer(message):
    """
    Envoie une trajectoire ou une commande.
    Compatible avec main_motor.cpp (attend 'trajectoryFinished').
    """
    global ser
    
    # MODE SIMULATION : Si init() a échoué ou n'a pas été appelé
    if ser is None:
        print(f"[SIMU] Commande virtuelle : {str(message)[:50]}...")
        # On simule le mouvement pour l'interface web (optionnel)
        if isinstance(message, str) and message.startswith("SET POSE"):
             pass # Déjà fait dans actions.py
        elif not isinstance(message, str):
             # Si c'est une traj, on pourrait simuler le déplacement du robot ici
             # pour l'instant on fait juste semblant d'attendre
             time.sleep(1)
        return

    if len(message) != 0:
        try:
            # --- CAS 1 : ENVOI TRAJECTOIRE (Liste de points) ---
            if not isinstance(message, str):
                # Conversion en numpy array pour être sûr
                trajectoire_bezier_mm = np.array(message)
                trajectoire_ints = np.rint(trajectoire_array).astype(int)
                
                # Cible finale pour double vérification
                cible_x = trajectoire_bezier_mm[-1][0]
                cible_y = trajectoire_bezier_mm[-1][1]
                
                # Envoi du JSON
                json_str = json.dumps(trajectoire_bezier_mm.tolist())
                ser.write((json_str + '\n').encode())
                print(f"[COM] Trajectoire envoyée ({len(trajectoire_bezier_mm)} pts).")
                
                # Boucle bloquante jusqu'à l'arrivée (Lecture réponse)
                while True:
                    line = ser.readline().decode(errors="ignore").strip()
                    
                    if line:
                        # 1. Retour Position : "[x, y, theta]" (Mètres)
                        if line.startswith('[') and line.endswith(']'):
                            try:
                                pos = ast.literal_eval(line)
                                x_mm = pos[0] * 1000
                                y_mm = pos[1] * 1000
                                theta_deg = pos[2] * 180 / np.pi

                                shared.robot_pos['x'] = x_mm
                                shared.robot_pos['y'] = y_mm
                                shared.robot_pos['theta'] = theta_deg
                                
                                # Check distance d'arrivée (< 2cm)
                                dist = math.sqrt((x_mm - cible_x)**2 + (y_mm - cible_y)**2)
                                if dist < 20:
                                    break # Arrivé

                            except Exception as e:
                                print(f"[COM] Erreur parse pos: {e}")

                        # 2. Signal de fin explicite
                        elif line == "trajectoryFinished":
                            print("[COM] Fin trajectoire reçue.")
                            break
                        
                        # 3. Logs ESP
                        else:
                            print(f"[ESP] {line}")

            # --- CAS 2 : COMMANDE TEXTE (SET POSE) ---
            elif message.startswith("SET POSE"):
                x_mm = shared.robot_pos['x']
                y_mm = shared.robot_pos['y']
                th_deg = shared.robot_pos['theta']
                th_rad = th_deg * np.pi / 180.0

                cmd = f"SET POSE {x_mm:.2f} {y_mm:.2f} {th_rad:.4f}\n"
                ser.write(cmd.encode())
                print(f"[COM] Reset Odom : {cmd.strip()}")

        except SerialException as e:
            print(f"[COM] Erreur Série critique : {e}")
            ser = None # On coupe la connexion pour éviter d'insister
        except KeyboardInterrupt:
            print("[COM] Interruption.")