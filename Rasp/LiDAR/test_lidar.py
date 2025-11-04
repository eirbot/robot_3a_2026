#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from rplidar_c1m1 import RPLidarC1M1

lidar = RPLidarC1M1("/dev/ttyUSB0")

try:
    lidar.start_scan()
    print("[INFO] Lecture d’un tour complet...")
    scan = lidar.get_scan()
    print(f"[OK] {len(scan)} points reçus.")

    # --- Affichage polar ---
    angles = np.radians(scan[:, 0])
    dists = scan[:, 1]
    qual = scan[:, 2]

    plt.figure(facecolor='black')
    ax = plt.subplot(111, projection='polar')
    ax.set_facecolor('black')
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    sc = ax.scatter(angles, dists, s=6, c=qual, cmap='turbo', vmin=0, vmax=63)
    ax.set_rmax(4000)
    plt.colorbar(sc, pad=0.1, label="Qualité")
    plt.show()

except KeyboardInterrupt:
    print("\n[STOP] utilisateur.")
finally:
    lidar.close()
