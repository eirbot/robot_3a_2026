#!/usr/bin/env python3
import numpy as np
from rplidar_c1m1 import RPLidarC1M1

# Outils
def wrap_pi(a):
    a = (a + np.pi) % (2*np.pi)
    return a - np.pi

class EKFLocalizer(RPLidarC1M1):
    """
    EKF pose-only: Prediction par odométrie, correction par balises fixes (range+bearing).
    - Etat: x = [x, y, theta]^T (mm, mm, rad)
    - Commande: u = [v, omega] (mm/s, rad/s) OU deltas (voir predict()).
    - Mesure: z_i = [r_i, b_i] de chaque balise i visible depuis le LIDAR.
    """

    def __init__(self, port="/dev/ttyUSB0", baud=460800, timeout=0.05, balises=None):
        super().__init__(port, baud, timeout)
        self.balises = balises or {
            "A": (0.0, 0.0),
            "B": (3000.0, 0.0),
            "C": (3000.0, 2000.0),
            "D": (0.0, 2000.0),
        }
        # Etat & covariance init
        self.x = np.array([1500.0, 1000.0, 0.0])  # (mm, mm, rad) — à initialiser si tu as mieux
        self.P = np.diag([400**2, 400**2, (5*np.pi/180)**2])  # incertitudes initiales

        # Bruits (à TUNER sur ton robot)
        # Process (odom): sigma_v ~ 10-50 mm/s, sigma_w ~ 0.02-0.1 rad/s selon ton asserv
        self.sigma_v = 30.0
        self.sigma_w = 0.05
        # Mesure LIDAR (balises): r ~ 10-40 mm, bearing ~ 0.5-2 deg
        self.sigma_r = 30.0
        self.sigma_b = np.deg2rad(1.0)

        # Fenêtres de recherche autour des mesures attendues
        self.bearing_window = np.deg2rad(6.0)   # ±6°
        self.range_window   = 150.0             # ±150 mm

        # Gestion d’obstruction (miss counters par balise)
        self.miss_max = 8
        self.miss_cnt = {k: 0 for k in self.balises.keys()}

    # ---------------- PREDICTION (odométrie) ----------------
    def predict(self, dt, v=None, w=None, dx=None, dy=None, dtheta=None):
        """
        Deux modes:
        - (v,w,dt): modèle unicycle.
        - (dx,dy,dtheta): deltas déjà intégrés (mm,mm,rad) dans repère monde.
        """
        x, y, th = self.x

        if dx is not None and dy is not None and dtheta is not None:
            # Deltas monde (déjà transformés)
            self.x = np.array([x + dx, y + dy, wrap_pi(th + dtheta)])
            # Process noise approximatif
            Q = np.diag([ (abs(dx)*0.2 + 5)**2, (abs(dy)*0.2 + 5)**2, (abs(dtheta)*0.2 + 0.01)**2 ])
            self.P = self.P + Q
            return

        assert v is not None and w is not None and dt > 0
        # Modèle unicycle (petite vitesse ou petit dt)
        if abs(w) < 1e-5:
            dxr = v * dt
            dyr = 0.0
        else:
            dxr = (v / w) * np.sin(w * dt)
            dyr = (v / w) * (1 - np.cos(w * dt))

        # Passage au monde
        c, s = np.cos(th), np.sin(th)
        dxm = c*dxr - s*dyr
        dym = s*dxr + c*dyr
        th_new = wrap_pi(th + w*dt)
        self.x = np.array([x + dxm, y + dym, th_new])

        # Jacobien F wrt état
        F = np.eye(3)
        F[0,2] = -s*dxr - c*dyr
        F[1,2] =  c*dxr - s*dyr

        # Bruit de commande → bruit process Q (linéarisation simple)
        G = np.array([
            [c*dt, 0.0],
            [s*dt, 0.0],
            [ 0.0,  dt],
        ])
        Qu = np.diag([self.sigma_v**2, self.sigma_w**2])
        Q = G @ Qu @ G.T
        self.P = F @ self.P @ F.T + Q

    # ------------- EXTRACTION mesures depuis un scan -------------
    def _extract_beacon_measurements(self, scan):
        """
        Pour chaque balise connue j, on prédit (r_hat, b_hat),
        puis on cherche dans le scan un point (ou petit groupe) proche de cette prédiction.
        Retourne une liste de (key, z=[r,b], R) observées.
        """
        x, y, th = self.x
        obs = []

        # Pré-calcul: on transforme le scan en (r, b) directs
        angles = np.radians(scan[:,0])    # [rad]
        dists  = scan[:,1]                # [mm]
        qual   = scan[:,2]

        # (Optionnel) On peut ignorer les points trop proches/bruités
        valid = (dists > 80) & (dists < 6000)
        angles = angles[valid]
        dists  = dists[valid]
        qual   = qual[valid]

        for key, (bx, by) in self.balises.items():
            # Prévision mesure: position balise dans repère robot
            dx = bx - x
            dy = by - y
            r_hat = np.hypot(dx, dy)
            b_hat = wrap_pi(np.arctan2(dy, dx) - th)

            # Fenêtre de gating
            ang_min = wrap_pi(b_hat - self.bearing_window)
            ang_max = wrap_pi(b_hat + self.bearing_window)

            # filtrage angulaire (prend en compte le wrap)
            if ang_min <= ang_max:
                ang_mask = (angles >= ang_min) & (angles <= ang_max)
            else:
                ang_mask = (angles >= ang_min) | (angles <= ang_max)

            rng_mask = (dists >= (r_hat - self.range_window)) & (dists <= (r_hat + self.range_window))
            mask = ang_mask & rng_mask

            if not np.any(mask):
                # pas vue → on incrémente le miss counter
                self.miss_cnt[key] = min(self.miss_cnt[key] + 1, self.miss_max)
                continue

            # Choix du point le plus proche de la prédiction (coût Mahalanobis approx)
            cand_angles = angles[mask]
            cand_dists  = dists[mask]
            # On peut pondérer par la qualité, mais on n’en fait pas une condition dure
            # Sélection: min de (|dr|/sigma_r + |db|/sigma_b)
            dr = cand_dists - r_hat
            db = np.array([wrap_pi(a - b_hat) for a in cand_angles])
            score = (np.abs(dr)/self.sigma_r) + (np.abs(db)/self.sigma_b)
            i = np.argmin(score)
            z = np.array([cand_dists[i], wrap_pi(cand_angles[i])])

            # Mise à jour du miss counter (vue → décrémente)
            self.miss_cnt[key] = max(self.miss_cnt[key] - 1, 0)

            # Matrice de bruit de mesure R (on peut l’ouvrir un peu si la balise est souvent manquée)
            miss_factor = 1.0 + 0.25*self.miss_cnt[key]
            R = np.diag([(self.sigma_r*miss_factor)**2, (self.sigma_b*miss_factor)**2])

            obs.append((key, z, R))
        return obs

    # ------------------- UPDATE EKF (toutes balises vues) -------------------
    def _update_with_measurements(self, obs):
        """
        obs: liste de tuples (key, z=[r,b], R), où r en mm, b en rad.
        Applique séquentiellement des updates EKF.
        """
        for key, z, R in obs:
            bx, by = self.balises[key]
            x, y, th = self.x

            dx = bx - x
            dy = by - y
            q = dx*dx + dy*dy
            r_hat = np.sqrt(q)
            b_hat = wrap_pi(np.arctan2(dy, dx) - th)

            # Innovation
            z_hat = np.array([r_hat, b_hat])
            yk = np.array([z[0] - z_hat[0], wrap_pi(z[1] - z_hat[1])])

            # Jacobien H wrt [x,y,theta]
            H = np.array([
                [ -dx/r_hat,     -dy/r_hat,        0.0 ],
                [  dy/q,         -dx/q,           -1.0 ],
            ])

            S = H @ self.P @ H.T + R
            K = self.P @ H.T @ np.linalg.inv(S)
            self.x = self.x + (K @ yk)
            self.x[2] = wrap_pi(self.x[2])
            I = np.eye(3)
            self.P = (I - K @ H) @ self.P

    # ------------------- PIPELINE COMPLET PAR PAS -------------------
    def step(self, dt, v=None, w=None, dx=None, dy=None, dtheta=None):
        """
        1) Predict avec odom (v,w,dt) OU (dx,dy,dtheta).
        2) Lire un scan, extraire les balises réellement visibles autour des mesures attendues.
        3) Update EKF avec ces mesures (s’il y en a).
        4) Retourner (x,y,theta) estimés + infos de visibilité.
        """
        # 1) PREDICT
        self.predict(dt, v=v, w=w, dx=dx, dy=dy, dtheta=dtheta)

        # 2) SCAN + extractions
        scan = self.get_scan(min_dist=60, max_dist=6000)
        obs = self._extract_beacon_measurements(scan)

        # 3) UPDATE si on a au moins 1 balise
        if len(obs) > 0:
            self._update_with_measurements(obs)

        # 4) Résumé
        pose = (float(self.x[0]), float(self.x[1]), float(self.x[2]))
        vis = {k: (self.miss_cnt[k]==0) for k in self.balises.keys()}
        return pose, vis, scan
