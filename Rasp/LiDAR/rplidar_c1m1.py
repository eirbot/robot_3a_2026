#!/usr/bin/env python3
import time
import numpy as np

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Tente d'importer le module Rust
try:
    from robot_lidar import RPLidarC1M1 as RPLidarC1M1_Rust
except ImportError as e:
    RPLidarC1M1_Rust = None
    print(f"[LiDAR] Module Rust 'robot_lidar' introuvable. Installation nécessaire. Détails: {e}")


# Import de backup (l'ancienne version Python pure)
try:
    from .rplidar_c1m1_py import RPLidarC1M1 as RPLidarC1M1_Py
except ImportError:
    from rplidar_c1m1_py import RPLidarC1M1 as RPLidarC1M1_Py

class RPLidarC1M1:
    """
    Wrapper compatible avec l'ancienne classe RPLidarC1M1.
    Utilise le driver Rust si disponible, sinon fallback sur Python.
    """
    def __init__(self, port="/dev/lidar", baud=460800, timeout=0.05):
        if RPLidarC1M1_Rust:
            print(f"[LiDAR] Utilisation du driver Rust optimisé 🦀")
            self.driver = RPLidarC1M1_Rust(port, baud, timeout)
            self.driver.connect()  # Le constructeur Rust ne connecte pas automatiquement
            self.is_rust = True
        else:
            print(f"[LiDAR] Utilisation du driver Python (LENT) 🐍")
            self.driver = RPLidarC1M1_Py(port, baud, timeout)
            self.is_rust = False

    def connect(self):
        # Le driver Rust se connecte dans le constructeur ou via connect()
        # Mon implémentation Rust a une méthode connect()
        if self.is_rust:
            self.driver.connect()
        else:
            self.driver.connect()

    def close(self):
        self.driver.close()

    def start_scan(self):
        self.driver.start_scan()

    def clean_input(self):
        self.driver.clean_input()

    def get_scan(self, min_dist=50, max_dist=6000):
        """
        Retourne np.array([[angle, dist, qual], ...]) ou None.
        """
        if self.is_rust:
            # Le driver Rust retourne une liste de tuples [(angle, dist, qual), ...] ou None
            scan = self.driver.get_scan(float(min_dist), float(max_dist))
            if scan is not None:
                # Conversion en numpy array pour compatibilité
                return np.array(scan, dtype=np.float32)
            return None
        else:
            return self.driver.get_scan(min_dist, max_dist)
