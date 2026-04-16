import time
from LiDAR import NavigationManager, MapVisualizer

def main():
    print("--- Démarrage de l'environnement de Test EKF ---")
    
    # 1. Initialiser le gestionnaire (Odom + Lidar)
    # Met les bons ports tty pour ta Raspberry
    nav = NavigationManager(port_esp='/dev/esp32_motors', baudrate_esp=115200, port_lidar='/dev/ttyUSB0')
    
    # 2. Initialiser la carte Pygame
    visu = MapVisualizer(nav, image_path="ihm/static/img/table_coupe_2026.png")
    
    # 3. Démarrer les threads
    nav.start()
    visu.start()
    
    try:
        # Boucle principale (Simulation de ta stratégie)
        while True:
            # Récupère la pose pour l'afficher dans la console toutes les secondes
            pose = nav.get_pose()
            scan = nav.get_scan()
            scan_size = len(scan) if scan is not None else 0
            print(f"Pose robot : X={pose[0]:.0f}mm, Y={pose[1]:.0f}mm, Theta={pose[2]:.2f}rad | Points LiDAR: {scan_size}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur...")
    finally:
        visu.stop()
        nav.stop()
        print("Fin du programme.")

if __name__ == "__main__":
    main()