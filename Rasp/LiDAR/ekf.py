import numpy as np
import math

class RobotEKF:
    def __init__(self, start_x, start_y, start_theta_deg):
        """
        Initialise le filtre à la position de départ du robot (souvent dans la zone de départ).
        """
        # L'état interne du robot : [X (mm), Y (mm), Theta (rad)]
        self.X = np.array([start_x, start_y, math.radians(start_theta_deg)], dtype=float)
        
        # P : Matrice de Covariance (Notre incertitude actuelle)
        # Au départ, on est sûr de notre position à +- 0.1
        self.P = np.eye(3) * 0.1 

        # Q : Bruit du modèle (La dérive intrinsèque de tes roues)
        # Ces valeurs sont à "tuner" : si tes roues glissent beaucoup, augmente ces valeurs.
        self.Q = np.array([
            [2.0, 0, 0],     # Bruit de l'odométrie en X
            [0, 2.0, 0],     # Bruit de l'odométrie en Y
            [0, 0, 0.01]     # Bruit de l'odométrie en Angle (rad)
        ])

    def normalize_angle(self, angle):
        """Garde l'angle strictement entre -PI et PI pour éviter les bugs de rotation"""
        return (angle + math.pi) % (2 * math.pi) - math.pi

    def predict(self, delta_dist, delta_angle_rad):
        """
        ÉTAPE 1 : PRÉDICTION (Basée sur l'odométrie)
        -> À appeler très vite (ex: 50Hz ou 100Hz) dans ta boucle de contrôle moteur.
        delta_dist : distance parcourue par le centre du robot depuis la dernière boucle (mm).
        delta_angle_rad : rotation du robot depuis la dernière boucle (radians).
        """
        theta = self.X[2]
        
        # 1. Mise à jour de la position estimée (Cinématique classique)
        self.X[0] += delta_dist * math.cos(theta + delta_angle_rad / 2.0)
        self.X[1] += delta_dist * math.sin(theta + delta_angle_rad / 2.0)
        self.X[2] = self.normalize_angle(self.X[2] + delta_angle_rad)

        # 2. Mise à jour de l'Incertitude (Les roues dérivent, donc P augmente)
        # Matrice Jacobienne F (Dérivée partielle des équations de mouvement)
        F = np.eye(3)
        F[0, 2] = -delta_dist * math.sin(theta + delta_angle_rad / 2.0)
        F[1, 2] =  delta_dist * math.cos(theta + delta_angle_rad / 2.0)

        self.P = F @ self.P @ F.T + self.Q

        return self.get_state()

    def update_lidar(self, lidar_x, lidar_y, lidar_theta_deg, erreur_mesure):
        """
        ÉTAPE 2 : CORRECTION (Basée sur le LiDAR)
        -> À appeler à ~10Hz uniquement quand le script UDP a trouvé les 3 balises.
        erreur_mesure : L'erreur géométrique (en mm) retournée par ton script de triangulation.
        """
        lidar_theta_rad = math.radians(lidar_theta_deg)
        
        # Z : La mesure absolue retournée par le LiDAR
        Z = np.array([lidar_x, lidar_y, lidar_theta_rad])

        # Y : L'Innovation (La différence entre ce que voit le LiDAR et là où on pensait être)
        Y = Z - self.X
        Y[2] = self.normalize_angle(Y[2]) # Corrige le passage 180° -> -180°

        # R : Bruit de la mesure LiDAR (DYNAMIQUE)
        # Si l'erreur géométrique est énorme (ex: robot en mouvement), la matrice R explose. 
        # L'EKF va donc ignorer le LiDAR et faire confiance aux roues !
        r_noise = max(10.0, erreur_mesure) 
        
        R = np.array([
            [r_noise, 0, 0],
            [0, r_noise, 0],
            [0, 0, math.radians(r_noise / 10.0)] # Si la distance est floue, l'angle l'est aussi
        ])

        # H : Matrice d'Observation (Identité car le LiDAR donne directement x,y,theta)
        H = np.eye(3)

        # S : L'incertitude totale (Incertitude de notre position + Incertitude du LiDAR)
        S = H @ self.P @ H.T + R
        
        # K : LE GAIN DE KALMAN (Le pourcentage de confiance accordé au LiDAR)
        K = self.P @ H.T @ np.linalg.inv(S)

        # 3. Correction de l'état (On tire le robot vers la vraie position LiDAR)
        self.X = self.X + K @ Y
        self.X[2] = self.normalize_angle(self.X[2])

        # 4. Correction de l'incertitude (Le fait d'avoir vu les balises nous rassure, P diminue)
        I = np.eye(3)
        self.P = (I - K @ H) @ self.P

        return self.get_state()

    def get_state(self):
        """
        Retourne la position parfaite et fusionnée pour tes déplacements.
        """
        return self.X[0], self.X[1], math.degrees(self.X[2])