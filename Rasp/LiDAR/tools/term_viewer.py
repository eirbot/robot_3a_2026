#!/usr/bin/env python3
import sys
import os
import time
import math
import shutil
import numpy as np

# Gestion des imports pour rplidar_c1m1
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

try:
    if "--python" in sys.argv:
        raise ImportError("Force Python")
    from rplidar_c1m1 import RPLidarC1M1
except ImportError:
    try:
        from rplidar_c1m1_py import RPLidarC1M1
        print("Utilisation du driver Python (LENT) 🐍")
    except ImportError:
        print("Erreur : Impossible de trouver 'rplidar_c1m1.py' ou 'rplidar_c1m1_py.py'.")
        sys.exit(1)

def clear_screen():
    print("\033[2J\033[H", end="")

def run_term_viewer(port="/dev/lidar", max_dist=4000):
    """
    Affiche les points LIDAR dans le terminal.
    """
    lidar = None
    try:
        lidar = RPLidarC1M1(port=port)
        lidar.start_scan()
        lidar.clean_input()
        print(f"LIDAR connecté sur {port}. Ctrl+C pour quitter.")
        time.sleep(1) # Laisser le temps au lidar de démarrer

        while True:
            # Taille du terminal
            cols, rows = shutil.get_terminal_size((80, 24))
            rows -= 2 # Marge pour infos

            # Centre de l'écran
            cx = cols // 2
            cy = rows // 2
            
            # Échelle : max_dist mm -> cy lignes (ou cx/2 colonnes car carac rectangulaire)
            # 1 char haut ~ 2 char large
            scale_y = cy / max_dist
            scale_x = scale_y * 0.5 # Correction ratio d'aspect approximatif

            # Buffer d'écran
            screen_buf = [[' ' for _ in range(cols)] for _ in range(rows)]
            
            # Grille / Croix centrale
            screen_buf[cy][cx] = '+'

            # Lecture scan
            scan = lidar.get_scan(min_dist=10, max_dist=max_dist*1.2)
            
            pt_count = 0
            if scan is not None and len(scan) > 0:
                pt_count = len(scan)
                angles_rad = np.radians(scan[:, 0])
                dists = scan[:, 1]
                
                # Conversion polaire -> cartésien écran
                # Y vers le haut sur l'écran terminal ? Non, ligne 0 en haut.
                # X vers la droite.
                # Robot frame: X devant, Y gauche ? 
                # Lidar frame standard: 0° devant ou à droite.
                # On suppose 0° à droite (X+), 90° devant (Y+).
                # Terminal : X+ droite, Y+ bas (lignes augmentent).
                
                for i in range(len(dists)):
                    r = dists[i]
                    theta = angles_rad[i]
                    
                    # Projeté
                    x = r * math.cos(theta)
                    y = r * math.sin(theta)
                    
                    # Vers coordonnées écran (Y inversé car ligne 0 en haut)
                    px = int(cx + x * scale_x)
                    py = int(cy - y * scale_y)
                    
                    if 0 <= px < cols and 0 <= py < rows:
                        screen_buf[py][px] = '●'

            # Rendu
            output = []
            output.append(f"LIDAR Live | {pt_count} points | Max: {max_dist}mm | Port: {port}")
            for row in screen_buf:
                output.append("".join(row))
            
            # Affichage "rapide"
            print("\033[H", end="") # Curseur home
            print("\n".join(output), end="", flush=True)
            
            # Petit délai pour ne pas scintiller trop
            # time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    except Exception as e:
        print(f"\nErreur : {e}")
    finally:
        if lidar:
            lidar.close()
            print("LIDAR fermé.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = "/dev/lidar"
        # Fallback
        if not os.path.exists(port) and os.path.exists("/dev/ttyUSB0"):
            port = "/dev/ttyUSB0"
            
    # clear_screen()
    run_term_viewer(port)
