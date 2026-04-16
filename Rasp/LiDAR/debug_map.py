import pygame
import math
import threading
import numpy as np

class MapVisualizer:
    def __init__(self, nav_manager, image_path="table_coupe_2026.png"):
        self.nav = nav_manager
        self.running = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        
        # --- CONFIGURATION AFFICHAGE ---
        self.TABLE_WIDTH_MM = 3000.0
        self.TABLE_HEIGHT_MM = 2000.0
        # Echelle (ex: 3000mm -> 900 pixels)
        self.SCALE = 0.3 
        
        self.MAP_W = int(self.TABLE_WIDTH_MM * self.SCALE)
        self.SCREEN_W = self.MAP_W * 2 # Double largeur pour scinder en deux
        self.SCREEN_H = int(self.TABLE_HEIGHT_MM * self.SCALE)
        
        try:
            # On charge l'image et on la met à la bonne échelle (seulement la moitié gauche)
            img = pygame.image.load(image_path)
            self.bg_image = pygame.transform.scale(img, (self.MAP_W, self.SCREEN_H))
        except Exception as e:
            print(f"[VISU] Erreur de chargement de l'image {image_path}. Fond noir par défaut.")
            self.bg_image = None

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def mm_to_px(self, x_mm, y_mm):
        """
        Convertit les coordonnées repère table (selon ekf_localizer.py) en pixels Pygame.
        Attention : Ton EKF dit : Origine (0,0) haut milieu, Axe X vers le bas, Axe Y vers la droite.
        Pygame : Origine (0,0) en haut à gauche, X vers la droite, Y vers le bas.
        """
        # Translation de l'origine de l'EKF vers le centre haut de l'écran Pygame
        px_x = int((self.TABLE_HEIGHT_MM / 2.0 + y_mm) * self.SCALE)
        px_y = int(x_mm * self.SCALE)
        return px_x, px_y

    def _run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.SCREEN_W, self.SCREEN_H))
        pygame.display.set_caption("EKF Lidar Debugger")
        clock = pygame.time.Clock()
        
        # Historique pour tracer la ligne du parcours
        path_history = []

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # Récupération des données depuis le NavigationManager
            pose = self.nav.get_pose()
            cov_matrix = self.nav.get_covariance()
            balises = self.nav.ekf.balises
            vis = self.nav.get_visibility()
            scan = self.nav.get_scan()
            
            x_mm, y_mm, theta_rad = pose[0], pose[1], pose[2]
            px, py = self.mm_to_px(x_mm, y_mm)
            
            # Ajout à l'historique
            if len(path_history) == 0 or math.hypot(path_history[-1][0]-px, path_history[-1][1]-py) > 2:
                path_history.append((px, py))

            # --- DESSIN ---
            if self.bg_image:
                screen.blit(self.bg_image, (0, 0))
            else:
                pygame.draw.rect(screen, (30, 30, 30), (0, 0, self.MAP_W, self.SCREEN_H))

            # Fond pour le Lidar (moitié droite)
            pygame.draw.rect(screen, (10, 10, 10), (self.MAP_W, 0, self.MAP_W, self.SCREEN_H))
            
            # --- Lidar Brut (Droite) ---
            CENTER_X = self.MAP_W + self.MAP_W // 2
            CENTER_Y = self.SCREEN_H // 2
            pygame.draw.circle(screen, (100, 100, 100), (CENTER_X, CENTER_Y), 4)

            LIDAR_SCALE = self.SCALE * 0.8
            if scan is not None and len(scan) > 0:
                angles_rad = np.radians(scan[:, 0])
                dists = scan[:, 1]
                
                x_mm = dists * np.cos(angles_rad)
                y_mm = -dists * np.sin(angles_rad)
                
                for i in range(len(dists)):
                    px = int(CENTER_X + x_mm[i] * LIDAR_SCALE)
                    py = int(CENTER_Y + y_mm[i] * LIDAR_SCALE)
                    if self.MAP_W < px < self.SCREEN_W and 0 < py < self.SCREEN_H:
                        qual = scan[i, 2]
                        color = (255, 255, 255) if qual > 40 else (0, 150, 255)
                        screen.set_at((px, py), color)

            # 1. Dessiner les balises
            for name, (bx, by) in balises.items():
                bpx, bpy = self.mm_to_px(bx, by)
                pygame.draw.circle(screen, (0, 255, 0), (bpx, bpy), int(50 * self.SCALE)) # Rayon 50mm
                
            # 2. Dessiner l'historique de la trajectoire
            if len(path_history) > 1:
                pygame.draw.lines(screen, (0, 150, 255), False, path_history, 2)

            # 3. Dessiner l'ellipse d'incertitude (Covariance)
            # On prend 3 fois l'écart-type (99.7% de confiance)
            std_x_mm = math.sqrt(cov_matrix[0, 0]) * 3
            std_y_mm = math.sqrt(cov_matrix[1, 1]) * 3
            
            rect_w = int(std_y_mm * self.SCALE * 2) # Inversion X/Y pour l'affichage Pygame
            rect_h = int(std_x_mm * self.SCALE * 2)
            
            # Empêcher Pygame de crasher si l'ellipse est trop grande/négative
            if rect_w > 0 and rect_h > 0:
                ellipse_rect = pygame.Rect(0, 0, rect_w, rect_h)
                ellipse_rect.center = (px, py)
                # Surface transparente pour l'ellipse
                s = pygame.Surface((self.SCREEN_W, self.SCREEN_H), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (255, 165, 0, 100), ellipse_rect) # Orange transparent
                screen.blit(s, (0,0))

            # 4. Dessiner le robot (Cercle + Ligne de direction)
            robot_radius_px = int(150 * self.SCALE) # Rayon robot (ex: 150mm)
            pygame.draw.circle(screen, (255, 50, 50), (px, py), robot_radius_px)
            
            # Calcul du vecteur de direction. 
            # Dans ton repère : X en bas, Y à droite. Angle 0 = vers le bas (X)
            dir_px = px + int(robot_radius_px * math.sin(theta_rad)) 
            dir_py = py + int(robot_radius_px * math.cos(theta_rad))
            pygame.draw.line(screen, (255, 255, 255), (px, py), (dir_px, dir_py), 3)

            # UI Text (Visibilité)
            if pygame.font:
                try:
                    font = pygame.font.SysFont("Arial", 18, bold=True)
                    y_offset = 10
                    for name, is_visible in vis.items():
                        color = (0, 255, 0) if is_visible else (255, 50, 50)
                        text = font.render(f"Balise {name}: {'VUE' if is_visible else 'PERDUE'}", True, color)
                        screen.blit(text, (10, y_offset))
                        y_offset += 25
                except:
                    pass

            pygame.display.flip()
            clock.tick(30) # 30 FPS

        pygame.quit()