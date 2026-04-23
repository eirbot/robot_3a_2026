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
    # L'instanciation de l'EKF se fera dynamiquement dans la boucle principale
    pass

    # --- 2. BOUCLE PRINCIPALE ---
    last_time = time.time()
    
    while True:
        try:
            # Gestion du Delta Time (dt)
            now = time.time()
            dt = now - last_time
            last_time = now

            if shared.state.get("ekf_enabled", True) and shared.state.get("lidar_enabled", True):
                if ekf is None and EKFLocalizer:
                    try:
                        lidar_cfg = shared.cfg.get('lidar', {})
                        if isinstance(lidar_cfg, bool):
                            port_lidar = '/dev/lidar'
                        else:
                            port_lidar = lidar_cfg.get('port', '/dev/lidar')
                        print(f"[HARDWARE] (Re)démarrage de l'EKF sur {port_lidar}...")
                        ekf = EKFLocalizer(port_lidar)
                        ekf.start_scan()
                        time.sleep(1) # Lidar warm-up
                        ekf.clean_input()
                    except Exception as e:
                        print(f"[HARDWARE] Erreur init EKF: {e}")
                        time.sleep(2)
                
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
            else:
                # EKF is disabled or Lidar is disabled
                if ekf:
                    print("[HARDWARE] Arrêt de l'EKF...")
                    ekf.close()
                    ekf = None
                
                # Mode Simulation ou Odometrie pure : On ne met plus à jour la position depuis le lidar
                if shared.state["match_running"] and shared.state.get("lidar_simu", False):
                    shared.robot_pos['x'] = (shared.robot_pos['x'] + 2) % 3000
                time.sleep(0.05)

            # Pause pour laisser respirer le CPU (20Hz - 50Hz est suffisant)
            time.sleep(0.02)

        except Exception as e:
            print(f"[HARDWARE] Erreur boucle : {e}")
            time.sleep(1) # On attend avant de réessayer pour pas spammer les logs