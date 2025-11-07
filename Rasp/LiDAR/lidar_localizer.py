#!/usr/bin/env python3
import numpy as np
from sklearn.cluster import DBSCAN # type: ignore
from rplidar_c1m1 import RPLidarC1M1

class LidarLocalizer(RPLidarC1M1):
    """
    Sous-classe de RPLidarC1M1 ajoutant la détection de balises réfléchissantes
    et la triangulation (localisation absolue sur la table).
    """

    def __init__(self, port="/dev/ttyUSB0", baud=460800, timeout=0.05, balises=None):
        super().__init__(port, baud, timeout)
        # Coordonnées des balises connues (en mm)
        self.balises = balises or {
            "A": (0, 0),
            "B": (3000, 0),
            "C": (3000, 2000),
            "D": (0, 2000),
        }

    # ---------------------------
    # Étape 1 : filtrage des points réfléchissants
    # ---------------------------
    @staticmethod
    def detect_reflective_points(scan, qual_min=40):
        mask = scan[:, 2] > qual_min
        angles = np.radians(scan[mask, 0])
        dists = scan[mask, 1]
        x = dists * np.cos(angles)
        y = dists * np.sin(angles)
        return np.column_stack((x, y))

    # ---------------------------
    # Étape 2 : clustering des reflets
    # ---------------------------
    @staticmethod
    def cluster_points(points, eps=100, min_samples=5):
        if len(points) == 0:
            return []
        labels = DBSCAN(eps=eps, min_samples=min_samples).fit(points).labels_
        clusters = []
        for label in set(labels):
            if label == -1:
                continue
            cluster = points[labels == label]
            clusters.append(np.mean(cluster, axis=0))
        return clusters

    # ---------------------------
    # Étape 3 : trilatération géométrique
    # ---------------------------
    @staticmethod
    def trilateration(beacons, distances):
        A, b = [], []
        x0, y0 = beacons[0]
        d0 = distances[0]
        for (xi, yi), di in zip(beacons[1:], distances[1:]):
            A.append([2*(xi - x0), 2*(yi - y0)])
            b.append([d0**2 - di**2 + xi**2 - x0**2 + yi**2 - y0**2])
        A, b = np.array(A), np.array(b)
        pos, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        return pos.flatten()

    # ---------------------------
    # Étape 4 : localisation complète
    # ---------------------------
    def locate_robot(self, qual_min=40, eps=100, min_samples=5):
        scan = self.get_scan()
        points = self.detect_reflective_points(scan, qual_min)
        clusters = self.cluster_points(points, eps, min_samples)

        if len(clusters) < 3:
            print("[WARN] Moins de 3 balises visibles.")
            return None

        # distances lidar→balises détectées
        distances = [np.linalg.norm(c) for c in clusters[:4]]
        beacons = list(self.balises.values())[:len(distances)]
        pos = self.trilateration(beacons, distances)
        print(f"[POS] Robot estimé à (x={pos[0]:.1f}, y={pos[1]:.1f}) mm")
        return pos, clusters, points

    # ---------------------------
    # Optionnel : visualisation rapide
    # ---------------------------
    @staticmethod
    def plot_localization(scan, clusters, pos, balises):
        import matplotlib.pyplot as plt
        plt.figure(figsize=(6, 4))
        # nuage brut
        plt.scatter(scan[:,1]*np.cos(np.radians(scan[:,0])),
                    scan[:,1]*np.sin(np.radians(scan[:,0])),
                    s=2, c='gray', label='Points LIDAR')
        # clusters détectés
        if clusters:
            plt.scatter(*zip(*clusters), c='red', s=50, label='Balises détectées')
        # balises connues
        plt.scatter(*zip(*balises.values()), c='green', s=80, label='Balises connues')
        # position estimée
        if pos is not None:
            plt.scatter(*pos, c='blue', s=100, marker='x', label='Robot estimé')
        plt.axis('equal')
        plt.xlabel("x [mm]"); plt.ylabel("y [mm]")
        plt.legend(); plt.title("Localisation LIDAR")
        plt.show()
