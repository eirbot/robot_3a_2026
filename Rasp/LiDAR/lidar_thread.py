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
                    
                    if dist > 0 and dist < self.seuil_mm:
                        # On voit un obstacle : on remet le chronomètre à zéro !
                        last_obstacle_time = time.time()
                        
                        if not shared.state.get("obstacle_detected"):
                            print(f"[🛑 OBSTACLE] Obstacle à {dist:.0f} mm ! Pause de la trajectoire !")
                            shared.state["obstacle_detected"] = True
                            
                            if hasattr(self.robot, 'toggle_lidar'):
                                self.robot.toggle_lidar()
                            else:
                                self.robot.stop()
                            
                    else:
                        # Le LiDAR ne voit rien sur CE tour. 
                        # Est-ce que le robot était en pause ?
                        if shared.state.get("obstacle_detected"):
                            
                            # On vérifie si la voie est libre depuis ASSEZ LONGTEMPS (1 seconde)
                            if time.time() - last_obstacle_time > clear_delay:
                                print(f"[✅ LIBRE] Voie libre confirmée (dist: {dist:.0f}mm) ! Reprise...")
                                shared.state["obstacle_detected"] = False
                                
                                if hasattr(self.robot, 'toggle_lidar'):
                                    self.robot.toggle_lidar()
                                
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