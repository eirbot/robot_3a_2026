#!/usr/bin/env python3
import numpy as np
from rplidar_c1m1 import RPLidarC1M1


# ---------------- Outils divers ---------------- #

def wrap_pi(a: float) -> float:
    """Ramène un angle dans [-pi, pi]."""
    a = (a + np.pi) % (2 * np.pi)
    return a - np.pi


class EKFLocalizer(RPLidarC1M1):
    """
    EKF pose-only: prédiction par odométrie, correction par balises fixes (range + bearing).

    Repère table:
        - Origine (0,0) : haut milieu de la table
        - Axe x : vers le bas (mm)
        - Axe y : vers la droite (mm)
    Tout (balises, état, odométrie) doit être exprimé dans ce même repère.

    Etat:
        x = [x, y, theta]^T (mm, mm, rad)
        theta : orientation du robot, 0 = vers +x (vers le bas sur la table),
                positif dans le sens anti-horaire.

    Mesures LIDAR pour chaque balise i:
        z_i = [r_i, b_i]
        r_i : distance (mm)
        b_i : angle LIDAR (rad) dans le même repère angulaire que theta.
    """

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baud: int = 460800,
        timeout: float = 0.05,
        balises: dict | None = None,
        init_pose: tuple[float, float, float] | None = None,
    ):
        super().__init__(port, baud, timeout)

        # Coordonnées fixes des balises (mm) dans ton repère table
        # (valeurs que tu as mesurées)
        self.balises = balises or {
            "A": (50.0, -1594.0),
            "B": (1950.0, -1594.0),
            "C": (1000.0, 1594.0),
            "D": (-100.0, 200.0),
        }

        # Etat initial (x, y, theta)
        if init_pose is None:
            # à adapter selon ta zone de départ
            self.x = np.array([500.0, 0.0, 0.0], dtype=float)
        else:
            self.x = np.array(init_pose, dtype=float)

        # Covariance initiale
        self.P = np.diag(
            [
                (400.0) ** 2,                 # incertitude sur x (mm²)
                (400.0) ** 2,                 # incertitude sur y (mm²)
                (np.deg2rad(5.0)) ** 2,       # incertitude sur theta (rad²)
            ]
        )

        # Bruits process (odom) — à tuner
        self.sigma_v = 30.0     # mm/s
        self.sigma_w = 0.05     # rad/s

        # Bruits de mesure LIDAR (balises) — à tuner
        self.sigma_r = 30.0     # mm
        self.sigma_b = np.deg2rad(1.0)  # rad

        # Fenêtres de recherche autour de la mesure attendue
        self.bearing_window = np.deg2rad(6.0)   # ±6°
        self.range_window = 150.0               # ±150 mm

        # Gestion d’obstruction (miss counters par balise)
        self.miss_max = 8
        self.miss_cnt = {k: 0 for k in self.balises.keys()}

    # -------------------------------------------------------------
    # PREDICTION (odométrie)
    # -------------------------------------------------------------
    def predict(
        self,
        dt: float,
        v: float | None = None,
        w: float | None = None,
        dx: float | None = None,
        dy: float | None = None,
        dtheta: float | None = None,
    ) -> None:
        """
        Deux modes:
            - (v, w, dt) : modèle unicycle (v en mm/s, w en rad/s).
            - (dx, dy, dtheta) : deltas déjà intégrés (mm, mm, rad) dans le repère monde.
        """
        x, y, th = self.x

        # --- Mode 1: deltas déjà calculés dans le monde ---
        if dx is not None and dy is not None and dtheta is not None:
            self.x = np.array([x + dx, y + dy, wrap_pi(th + dtheta)], dtype=float)

            Q = np.diag(
                [
                    (abs(dx) * 0.2 + 5.0) ** 2,
                    (abs(dy) * 0.2 + 5.0) ** 2,
                    (abs(dtheta) * 0.2 + 0.01) ** 2,
                ]
            )
            self.P = self.P + Q
            return

        # --- Mode 2: commandes (v, w, dt) ---
        assert v is not None and w is not None and dt > 0.0

        # Modèle unicycle dans le repère robot
        if abs(w) < 1e-5:
            dxr = v * dt
            dyr = 0.0
        else:
            dxr = (v / w) * np.sin(w * dt)
            dyr = (v / w) * (1.0 - np.cos(w * dt))

        # Passage repère robot -> repère monde
        c, s = np.cos(th), np.sin(th)
        dxm = c * dxr - s * dyr
        dym = s * dxr + c * dyr
        th_new = wrap_pi(th + w * dt)

        self.x = np.array([x + dxm, y + dym, th_new], dtype=float)

        # Jacobien F wrt état
        F = np.eye(3)
        F[0, 2] = -s * dxr - c * dyr
        F[1, 2] = c * dxr - s * dyr

        # Bruit process (linéarisation simple)
        G = np.array(
            [
                [c * dt, 0.0],
                [s * dt, 0.0],
                [0.0, dt],
            ]
        )
        Qu = np.diag([self.sigma_v**2, self.sigma_w**2])
        Q = G @ Qu @ G.T
        self.P = F @ self.P @ F.T + Q

    # -------------------------------------------------------------
    # EXTRACTION mesures depuis un scan LIDAR
    # -------------------------------------------------------------
    def _extract_beacon_measurements(self, scan: np.ndarray):
        """
        Pour chaque balise j, on prédit (r_hat, b_hat),
        puis on cherche dans le scan un point proche de cette prédiction.
        Retourne une liste de (key, z=[r,b], R) observées.
        """
        x, y, th = self.x
        obs = []

        # Angles en rad, distances en mm, qual en [0..63]
        angles = np.radians(scan[:, 0])
        dists = scan[:, 1]
        qual = scan[:, 2]

        # Optionnel: filtrage brut
        valid = (dists > 80.0) & (dists < 6000.0)
        angles = angles[valid]
        dists = dists[valid]
        qual = qual[valid]

        for key, (bx, by) in self.balises.items():
            # Prévision de la mesure en repère robot
            dx = bx - x
            dy = by - y
            r_hat = np.hypot(dx, dy)
            b_hat = wrap_pi(np.arctan2(dy, dx) - th)

            # Fenêtre de gating
            ang_min = wrap_pi(b_hat - self.bearing_window)
            ang_max = wrap_pi(b_hat + self.bearing_window)

            if ang_min <= ang_max:
                ang_mask = (angles >= ang_min) & (angles <= ang_max)
            else:
                ang_mask = (angles >= ang_min) | (angles <= ang_max)

            rng_mask = (dists >= (r_hat - self.range_window)) & (
                dists <= (r_hat + self.range_window)
            )
            mask = ang_mask & rng_mask

            if not np.any(mask):
                self.miss_cnt[key] = min(self.miss_cnt[key] + 1, self.miss_max)
                continue

            cand_angles = angles[mask]
            cand_dists = dists[mask]

            dr = cand_dists - r_hat
            db = np.array([wrap_pi(a - b_hat) for a in cand_angles])
            score = (np.abs(dr) / self.sigma_r) + (np.abs(db) / self.sigma_b)
            i = np.argmin(score)

            z = np.array(
                [
                    cand_dists[i],
                    wrap_pi(cand_angles[i]),
                ]
            )

            self.miss_cnt[key] = max(self.miss_cnt[key] - 1, 0)

            miss_factor = 1.0 + 0.25 * self.miss_cnt[key]
            R = np.diag(
                [
                    (self.sigma_r * miss_factor) ** 2,
                    (self.sigma_b * miss_factor) ** 2,
                ]
            )

            obs.append((key, z, R))

        return obs

    # -------------------------------------------------------------
    # UPDATE EKF avec les balises visibles
    # -------------------------------------------------------------
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
            q = dx * dx + dy * dy
            r_hat = np.sqrt(q)
            b_hat = wrap_pi(np.arctan2(dy, dx) - th)

            z_hat = np.array([r_hat, b_hat])
            yk = np.array(
                [
                    z[0] - z_hat[0],
                    wrap_pi(z[1] - z_hat[1]),
                ]
            )

            # Jacobien H wrt [x, y, theta]
            H = np.array(
                [
                    [-dx / r_hat, -dy / r_hat, 0.0],
                    [dy / q, -dx / q, -1.0],
                ]
            )

            S = H @ self.P @ H.T + R
            K = self.P @ H.T @ np.linalg.inv(S)

            self.x = self.x + K @ yk
            self.x[2] = wrap_pi(self.x[2])

            I = np.eye(3)
            self.P = (I - K @ H) @ self.P

    # -------------------------------------------------------------
    # PIPELINE COMPLET PAR PAS
    # -------------------------------------------------------------
    def step(
        self,
        dt: float,
        v: float | None = None,
        w: float | None = None,
        dx: float | None = None,
        dy: float | None = None,
        dtheta: float | None = None,
    ):
        """
        1) Predict avec odom (v, w, dt) OU (dx, dy, dtheta).
        2) Lire un scan, extraire les balises visibles autour des mesures attendues.
        3) Update EKF avec ces mesures (s'il y en a).
        4) Retourne (x, y, theta) estimés + infos de visibilité.
        """
        # 1) PREDICTION
        self.predict(dt, v=v, w=w, dx=dx, dy=dy, dtheta=dtheta)

        # 2) SCAN + extractions
        scan = self.get_scan(min_dist=60, max_dist=6000)
        obs = self._extract_beacon_measurements(scan)

        # 3) UPDATE si on a au moins une balise
        if len(obs) > 0:
            self._update_with_measurements(obs)

        # 4) Résumé
        pose = (float(self.x[0]), float(self.x[1]), float(self.x[2]))
        vis = {k: (self.miss_cnt[k] == 0) for k in self.balises.keys()}
        return pose, vis, scan
    
    def locate_once(self):
        """
        Effectue une localisation absolue instantanée du robot
        uniquement depuis un scan LIDAR et les balises fixes.

        Retourne:
            (x, y, theta) estimés
            nb_balises_vues
            obs (liste des mesures utilisées)
        """

        # 1) Lire un seul scan
        scan = self.get_scan(min_dist=60, max_dist=6000)

        # 2) Extraire les mesures valides
        obs = self._extract_beacon_measurements(scan)
        nb = len(obs)

        if nb == 0:
            print("[LOCATE] Aucune balise détectée -> impossible de se localiser.")
            return None, 0, None

        # 3) Effectuer un update EKF uniquement basé sur ce scan
        self._update_with_measurements(obs)

        # 4) Retourner la pose courante
        return (float(self.x[0]), float(self.x[1]), float(self.x[2])), nb, obs

