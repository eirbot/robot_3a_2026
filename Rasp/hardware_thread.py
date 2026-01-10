# hardware_thread.py
import time
import sys
import os

# Imports pour communiquer avec le reste
import ihm.shared as shared

# Tente d'importer ton EKF (Gère le cas où le fichier n'est pas là)
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'LiDAR'))
    from ekf_localizer import EKFLocalizer
except ImportError:
    print("[HARDWARE] Attention: 'ekf_localizer' non trouvé (Mode Simulation ?)")
    EKFLocalizer = None

def hardware_loop():
    print("[HARDWARE] Démarrage du thread capteurs...")

    # --- 1. INITIALISATION ---
    ekf = None
    if EKFLocalizer and shared.cfg.get("lidar_enabled", True):
        try:
            ekf = EKFLocalizer("/dev/lidar") 
            ekf.start_scan()
            print("[HARDWARE] Lidar & EKF connectés.")
        except Exception as e:
            print(f"[HARDWARE] Erreur init EKF: {e}")

    # --- 2. BOUCLE PRINCIPALE ---
    last_time = time.time()
    
    while True:
        try:
            # Gestion du Delta Time (dt)
            now = time.time()
            dt = now - last_time
            last_time = now

            if ekf:
                # A. Lecture & Calcul EKF
                ekf.clean_input() # Vider le buffer pour être temps réel
                
                # Prédiction (Odométrie - A récupérer via ESP32 plus tard)
                # Pour l'instant on met 0,0 si on a pas l'info moteurs
                ekf.predict(dt=dt, v=0.0, w=0.0)
                
                # Correction (Lidar)
                pose, nb_balises, _ = ekf.locate_once()
                
                # B. Mise à jour de l'ETAT PARTAGÉ (Le point clé !)
                # C'est ici qu'on dit à l'IHM et à la Stratégie où on est
                if pose:
                    x, y, theta = pose
                    shared.robot_pos['x'] = x
                    shared.robot_pos['y'] = y
                    shared.robot_pos['theta'] = theta
                    
                    # (Optionnel) Tu peux logger si perdu
                    # if nb_balises < 2: print("[HARDWARE] Perdu (1 balise)...")

            else:
                # Mode Simulation : On fait bouger le robot fake pour tester l'IHM
                if shared.state["match_running"]:
                    shared.robot_pos['x'] = (shared.robot_pos['x'] + 2) % 3000
                time.sleep(0.05) 

            # Pause pour laisser respirer le CPU (20Hz - 50Hz est suffisant)
            time.sleep(0.02)

        except Exception as e:
            print(f"[HARDWARE] Erreur boucle : {e}")
            time.sleep(1) # On attend avant de réessayer pour pas spammer les logs