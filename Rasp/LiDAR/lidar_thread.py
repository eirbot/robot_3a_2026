import threading
import socket
import struct
import time

# On importe ton shared pour accéder à robot_pos et state
import ihm.shared as shared
from LiDAR.localise import calculer_pose_intelligente

class LidarCollisionThread(threading.Thread):
    def __init__(self, robot, seuil_mm=300.0):
        """
        Initialise le thread d'écoute LiDAR.
        :param robot: L'objet ESPMotors qui contrôle tes moteurs
        :param seuil_mm: La distance de déclenchement (en mm)
        """
        super().__init__()
        self.robot = robot
        self.seuil_mm = seuil_mm
        self.running = True
        self.daemon = True

        # Configuration UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 8080))
        self.sock.settimeout(2.0) 
        
        # Init des états
        shared.state['obstacle_detected'] = False
        shared.state['obstacle_type'] = 0

    def run(self):
        print(f"[LIDAR THREAD] Démarrage de la surveillance. Seuil = {self.seuil_mm} mm")
        last_log_time = time.time()

        last_obstacle_time = 0.0
        clear_delay = 1.0
        
        while self.running:
            try:
                # Lecture des 64 octets (format 4 balises : 3 floats + 1 int + 12 floats)
                data, addr = self.sock.recvfrom(64)
                
                if len(data) == 64:
                    unpacked = struct.unpack('<fff i ffffffffffff', data)
                    
                    angle, dist, intensity = unpacked[0:3]
                    num_beacons = unpacked[3]
                    
                    if time.time() - last_log_time > 2.0:
                        if dist < 90000:  
                            print(f"[LIDAR THREAD] Ping... (Obstacle à {dist:.0f} mm, Angle: {angle:.1f}°)")
                        last_log_time = time.time()
                        
                    mode = shared.state.get("lidar_mode", "OFF")

                    if mode == "OFF":
                        if shared.state.get("obstacle_detected", False):
                            print("[LIDAR] Désactivation (Mode OFF)")
                            shared.state["obstacle_detected"] = False
                            shared.state["obstacle_type"] = 0
                            self.robot.set_lidar_state(0)
                        continue

                    # ====================================================
                    # --- 1. GESTION ANTI-COLLISION (Envoi vers ESP32) ---
                    # ====================================================
                    this_point_obs = False
                    this_point_type = 0 # 0: Libre, 1: 360, 2: Front, 3: Back

                    if mode == "HOMOLOGATION":
                        if 0 < dist < 500:
                            this_point_obs = True
                            this_point_type = 1
                    elif mode == "MATCH":
                        if 0 < dist < self.seuil_mm:
                            # Normalisation angle en [-180, 180]
                            a = angle
                            if a > 180: a -= 360
                            
                            if -22.5 <= a <= 22.5:
                                this_point_obs = True
                                this_point_type = 2 # FRONT
                            elif a <= -157.5 or a >= 157.5:
                                this_point_obs = True
                                this_point_type = 3 # BACK

                    if this_point_obs:
                        last_obstacle_time = time.time()
                        
                        # Si l'obstacle change de type ou qu'on ne l'avait pas encore vu
                        if shared.state.get("obstacle_type", 0) != this_point_type:
                            print(f"[🛑 OBSTACLE] Type {this_point_type} à {dist:.0f} mm (Mode: {mode})")
                            shared.state["obstacle_detected"] = True
                            shared.state["obstacle_type"] = this_point_type
                            self.robot.set_lidar_state(this_point_type)
                            
                    else:
                        # Délai de sécurité avant de relancer l'ESP32
                        if shared.state.get("obstacle_detected", False):
                            if time.time() - last_obstacle_time > clear_delay:
                                print(f"[✅ LIBRE] Voie libre confirmée !")
                                shared.state["obstacle_detected"] = False
                                shared.state["obstacle_type"] = 0
                                self.robot.set_lidar_state(0)
                                
                    # ====================================================
                    # --- 2. LOCALISATION INTELLIGENTE (LOGS SEULS) ---
                    # ====================================================
                    if num_beacons >= 3:
                        mesures = []
                        for i in range(num_beacons):
                            idx = 4 + (i * 3) # L'angle est à idx, la distance à idx+1
                            mesures.append((unpacked[idx], unpacked[idx+1]))
                            
                        # On récupère la position estimée par l'ESP32 !
                        # (.get avec valeurs par défaut pour éviter un crash si l'ESP n'a pas encore répondu)
                        est_x = shared.robot_pos.get('x', 0.0)
                        est_y = shared.robot_pos.get('y', 0.0)
                        est_cap = shared.robot_pos.get('theta', 0.0)
                        
                        result, status = calculer_pose_intelligente(mesures, est_x, est_y, est_cap)
                        
                        if status.startswith("OK"):
                            x_lidar, y_lidar, theta_lidar, err_lidar = result
                            print(f"📍 [POS LiDAR] X={x_lidar:4.0f} | Y={y_lidar:4.0f} | Cap={theta_lidar:5.1f}° (Bruit: {err_lidar:.0f}mm)")
                        else:
                            # --- LE PRINT MAGIQUE POUR COMPRENDRE LE PROBLÈME ---
                            print(f"📡 [DEBUG] Vues: {num_beacons} balises | {status} | Odom ESP32: X={est_x:.0f} Y={est_y:.0f} Cap={est_cap:.0f}°")
                    
                    elif num_beacons > 0:
                        # S'il voit 1 ou 2 balises, on veut le savoir aussi !
                        print(f"📡 [DEBUG] Pas assez de balises vues ({num_beacons}/3)")
                        
            except socket.timeout:
                print("[⚠️ ALERTE] Perte de com LiDAR. Arrêt par sécurité.")
                # Si le C++ crash vraiment, tu pourras envisager de couper les moteurs ici
                # self.robot.set_lidar_state(1) 
            except Exception as e:
                if self.running:
                    print(f"[LIDAR THREAD] Erreur : {e}")
                
    def stop(self):
        self.running = False
        self.sock.close()