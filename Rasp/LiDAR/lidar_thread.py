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
        self.sock.settimeout(0.5) # Sécurité : si le C++ plante, on s'en rend compte
        
        # Init de l'état obstacle
        import ihm.shared as shared
        shared.state['obstacle_detected'] = False

    def run(self):
        print(f"[LIDAR THREAD] Démarrage de la surveillance. Seuil = {self.seuil_mm} mm")
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(12)
                
                if len(data) == 12:
                    angle, dist, intensity = struct.unpack('<fff', data)
                    
                    import ihm.shared as shared
                    
                    if dist < self.seuil_mm:
                        if not shared.state.get("obstacle_detected"):
                            print(f"[🛑 OBSTACLE] Obstacle à {dist:.0f} mm ! Pause de la trajectoire !")
                            shared.state["obstacle_detected"] = True
                            
                            # Arrêt physique des moteurs via l'instance de RobotActions
                            self.robot.stop()  
                            
                            # Mise à jour IHM visuelle uniquement
                            shared.send_led_cmd("COLOR:255,165,0") # Orange pour avertissement
                    else:
                        # Si le point est plus loin, ça veut dire que l'obstacle est parti
                        if shared.state.get("obstacle_detected"):
                            print(f"[✅ LIBRE] Obstacle parti (dist: {dist:.0f}mm) ! Reprise...")
                            shared.state["obstacle_detected"] = False
                            
                            # On restaure la couleur de la team
                            if shared.state.get("team") == "JAUNE":
                                shared.send_led_cmd("COLOR:255,160,0")
                            else:
                                shared.send_led_cmd("COLOR:0,0,255")
                        
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