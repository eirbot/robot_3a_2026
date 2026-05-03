import threading
import socket
import struct
import time

class LidarCollisionThread(threading.Thread):
    def __init__(self, robot, seuil_mm=300.0):
        """
        Initialise le thread d'écoute LiDAR.
        :param robot: L'objet ou l'interface qui contrôle tes moteurs (ex: ClassRobot)
        :param seuil_mm: La distance de déclenchement de l'arrêt d'urgence (en mm)
        """
        super().__init__()
        self.robot = robot
        self.seuil_mm = seuil_mm
        self.running = True
        self.daemon = True  # Le thread s'arrêtera tout seul quand le programme principal se ferme

        # Configuration UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 8080))
        self.sock.settimeout(2.0) # Sécurité : si le C++ plante, on s'en rend compte (2s au lieu de 0.5s pour éviter les faux positifs)
        
        # Init de l'état obstacle
        import ihm.shared as shared
        shared.state['obstacle_detected'] = False

    def run(self):
        print(f"[LIDAR THREAD] Démarrage de la surveillance. Seuil = {self.seuil_mm} mm")
        last_log_time = time.time()

        last_obstacle_time = 0.0
        clear_delay = 1.0
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(52)
                
                if len(data) == 52:
                    unpacked = struct.unpack('<fff i fffffffff', data)
                    
                    angle, dist, intensity = unpacked[0:3]
                    num_beacons = unpacked[3]
                    
                    if time.time() - last_log_time > 2.0:
                        if dist < 90000:  # 99999 is used as 'no obstacle' in CPP
                            print(f"[LIDAR THREAD] Ping... (Obstacle à {dist:.0f} mm, Angle: {angle:.1f}°)")
                        last_log_time = time.time()
                        
                    import ihm.shared as shared
                    mode = shared.state.get("lidar_mode", "OFF")

                    if mode == "OFF":
                        if shared.state.get("obstacle_detected", False):
                            print("[LIDAR] Désactivation (Mode OFF)")
                            shared.state["obstacle_detected"] = False
                            shared.state["obstacle_type"] = 0
                            self.robot.set_lidar_state(0)
                        continue

                    # Détermination si le point actuel est un obstacle selon le mode
                    this_point_obs = False
                    this_point_type = 0 # 0: Libre, 1: 360, 2: Front, 3: Back

                    if mode == "HOMOLOGATION":
                        if 0 < dist < 500:
                            this_point_obs = True
                            this_point_type = 1
                    elif mode == "MATCH":
                        if 0 < dist < 350:
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
                        # Si on avait un obstacle, on attend le délai de sécurité pour libérer
                        if shared.state.get("obstacle_detected", False):
                            if time.time() - last_obstacle_time > clear_delay:
                                print(f"[✅ LIBRE] Voie libre confirmée !")
                                shared.state["obstacle_detected"] = False
                                shared.state["obstacle_type"] = 0
                                self.robot.set_lidar_state(0)
                                
                    # --- INTÉGRATION EKF & TRILATÉRATION ---
                    if num_beacons == 3:
                        from LiDAR.localise import calculer_pose
                        mesures = [(unpacked[4], unpacked[5]), (unpacked[7], unpacked[8]), (unpacked[10], unpacked[11])]
                        result, status = calculer_pose(mesures)
                        
                        if status == "OK":
                            x_lidar, y_lidar, theta_lidar, err_lidar = result
                            
                            ekf_filter = getattr(shared, 'ekf_filter', None)
                            if ekf_filter is not None:
                                # On met à jour le filtre avec les mesures absolues trouvées !
                                ekf_filter.update_lidar(x_lidar, y_lidar, theta_lidar, err_lidar)
                        
            except socket.timeout:
                print("[⚠️ ALERTE] Perte de com LiDAR. Arrêt par sécurité.")
                # self.robot.stop()
            except Exception as e:
                if self.running:
                    print(f"[LIDAR THREAD] Erreur : {e}")
                
    def stop(self):
        """Permet d'arrêter le thread proprement depuis le programme principal"""
        self.running = False
        self.sock.close()