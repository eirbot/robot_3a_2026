#!/usr/bin/env python3
import sys
import os
import time
import threading
import queue
import math
import numpy as np

# --- GESTION DES IMPORTS ---
# On ajoute le dossier parent (Rasp/LiDAR) au path pour pouvoir importer rplidar_c1m1
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

try:
    from rplidar_c1m1 import RPLidarC1M1
except ImportError:
    print("Erreur : Impossible de trouver 'rplidar_c1m1.py'.")
    print(f"Vérifiez que le fichier est bien dans : {parent_dir}")
    sys.exit(1)

try:
    import pygame
except ImportError:
    print("Erreur : La librairie 'pygame' n'est pas installée.")
    print("Installez-la avec : pip install pygame")
    sys.exit(1)


def run_lidar_viewer(port="/dev/ttyUSB0", baud=460800, rmax=4000, fps=20, step=500):
    """
    Lance la visualisation temps réel du LIDAR avec PyGame.
    """
    
    # --- Initialisation LIDAR ---
    try:
        lidar = RPLidarC1M1(port=port, baud=baud)
        lidar.start_scan()
        lidar.clean_input()
    except Exception as e:
        print(f"[ERREUR] Impossible d'ouvrir le LIDAR sur {port} : {e}")
        return

    print(f"[VIEWER] Démarrage sur {port} (Max dist: {rmax}mm)")
    print("COMMANDES :")
    print("  [ECHAP] : Quitter")
    print("  [HAUT]  : Augmenter le seuil de qualité")
    print("  [BAS]   : Diminuer le seuil de qualité")
    print("  [A]     : Mode Seuil Auto (Adaptatif)")
    
    # --- Paramètres PyGame ---
    SIZE = 800
    CENTER = SIZE // 2
    SCALE = SIZE / (2 * rmax)
    BG_COLOR = (10, 10, 10)
    GRID_COLOR = (50, 50, 50)
    
    pygame.init()
    screen = pygame.display.set_mode((SIZE, SIZE))
    pygame.display.set_caption("LIDAR Viewer - Eurobot 2026")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 14)

    # --- Communication Thread <-> GUI ---
    q_scans = queue.Queue(maxsize=2)
    running = True
    
    # --- Thread d'acquisition ---
    def acquisition_thread():
        while running:
            try:
                # Lecture d'un tour complet
                scan = lidar.get_scan(min_dist=10, max_dist=rmax + 500)
                if scan is not None and len(scan) > 0:
                    if q_scans.full():
                        try:
                            q_scans.get_nowait()
                        except queue.Empty:
                            pass
                    q_scans.put(scan)
                else:
                    time.sleep(0.005)
            except Exception as e:
                print(f"[THREAD] Erreur lecture : {e}")
                time.sleep(0.1)

    thread = threading.Thread(target=acquisition_thread, daemon=True)
    thread.start()

    # --- Variables d'état ---
    qual_thresh = 40
    auto_mode = False
    last_scan = None
    frame_count = 0

    # --- Boucle principale d'affichage ---
    try:
        while running:
            # 1. Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_UP:
                        qual_thresh = min(qual_thresh + 5, 255)
                        auto_mode = False
                    elif event.key == pygame.K_DOWN:
                        qual_thresh = max(qual_thresh - 5, 0)
                        auto_mode = False
                    elif event.key == pygame.K_a:
                        auto_mode = not auto_mode

            # 2. Récupération des données (sans bloquer)
            if not q_scans.empty():
                last_scan = q_scans.get()

            # 3. Dessin
            screen.fill(BG_COLOR)

            # Grille (Cercles concentriques)
            pygame.draw.circle(screen, (255, 0, 0), (CENTER, CENTER), 4) # Robot center
            for r in range(step, rmax + step, step):
                radius = int(r * SCALE)
                pygame.draw.circle(screen, GRID_COLOR, (CENTER, CENTER), radius, 1)
                # Label distance
                lbl = font.render(f"{r}", True, (100, 100, 100))
                screen.blit(lbl, (CENTER + 2, CENTER - radius - 10))

            # Affichage des points
            if last_scan is not None:
                angles_rad = np.radians(last_scan[:, 0])
                dists = last_scan[:, 1]
                quals = last_scan[:, 2]

                # Calcul auto du seuil (Top 5% des intensités)
                if auto_mode and len(quals) > 10:
                    qual_thresh = float(np.percentile(quals, 95))

                # Conversion Polaire -> Cartésien (Repère écran : Y vers le bas)
                # Note: lidar angle 0 est souvent devant ou sur le coté, à adapter selon montage.
                # Ici : standard mathématique (0 à droite, tourne sens trigo)
                x_mm = dists * np.cos(angles_rad)
                y_mm = -dists * np.sin(angles_rad) # Y inversé pour l'écran

                # On dessine
                for i in range(len(dists)):
                    px = int(CENTER + x_mm[i] * SCALE)
                    py = int(CENTER + y_mm[i] * SCALE)

                    if 0 <= px < SIZE and 0 <= py < SIZE:
                        q = quals[i]
                        # Couleur selon qualité/intensité
                        if q >= qual_thresh:
                            # Point "réfléchissant" (balise potentielle) -> BLANC brillant
                            color = (255, 255, 255)
                            size_pt = 3
                        else:
                            # Point normal -> Couleur dégradée (Bleu -> Vert)
                            # Simple mapping pour l'exemple
                            intensity = min(255, int(q * 4))
                            color = (0, intensity, 100) 
                            size_pt = 1
                        
                        screen.set_at((px, py), color)
                        # Pour les points brillants, on fait un petit carré pour mieux voir
                        if size_pt > 1:
                            pygame.draw.rect(screen, color, (px-1, py-1, 3, 3))

            # HUD (Infos textuelles)
            infos = [
                f"FPS: {clock.get_fps():.1f}",
                f"Points: {len(last_scan) if last_scan is not None else 0}",
                f"Seuil Qualité: {int(qual_thresh)} {'(AUTO)' if auto_mode else '(MANUEL)'}",
                f"Port: {port}"
            ]
            
            for i, info in enumerate(infos):
                txt = font.render(info, True, (0, 255, 0))
                screen.blit(txt, (10, 10 + i * 20))

            pygame.display.flip()
            frame_count += 1
            clock.tick(fps)

    except KeyboardInterrupt:
        pass
    finally:
        running = False
        lidar.close()
        pygame.quit()
        print("[VIEWER] Fermeture.")

if __name__ == "__main__":
    # Petit gestionnaire d'arguments simple
    if len(sys.argv) > 1:
        port_arg = sys.argv[1]
    else:
        port_arg = "/dev/ttyUSB0"
        
    run_lidar_viewer(port=port_arg)