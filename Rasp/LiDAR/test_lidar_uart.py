#!/usr/bin/env python3
"""
Affichage fluide des mesures LiDAR C1M1-R2 via le SDK Slamtec.
Lit le flux texte de ultra_simple et trace les points en direct.
"""

import subprocess
import numpy as np
import matplotlib.pyplot as plt
import re
import time
import os
import signal

# --- Config utilisateur ---
ULTRA_SIMPLE_PATH = "/root/rplidar_sdk/output/Linux/Release/ultra_simple"
PORT = "/dev/ttyUSB0"
BAUD = "460800"
REFRESH_RATE = 0.1  # secondes entre deux mises à jour (≈10 FPS)
MAX_POINTS = 4000   # limite du nuage pour éviter de surcharger matplotlib
# ---------------------------

if not os.path.exists(ULTRA_SIMPLE_PATH):
    raise FileNotFoundError(f"❌ Binaire introuvable : {ULTRA_SIMPLE_PATH}")

print(f"[INFO] Lancement du LiDAR via {ULTRA_SIMPLE_PATH}")
proc = subprocess.Popen(
    [ULTRA_SIMPLE_PATH, "--channel", "--serial", PORT, BAUD],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
)

pattern = re.compile(r"theta:\s*([\d\.]+)\s*Dist:\s*([\d\.]+)\s*Q:\s*(\d+)")

plt.ion()
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
points, = ax.plot([], [], 'r.', markersize=2)
ax.set_rmax(4000)
ax.set_rticks([500, 1000, 2000, 3000, 4000])
ax.grid(True)
ax.set_title("RPLIDAR C1M1-R2 – affichage en direct")

angles, dists = [], []
last_refresh = time.time()

try:
    while True:
        line = proc.stdout.readline()
        if not line:
            continue
        match = pattern.search(line)
        if not match:
            continue

        angle = np.radians(float(match.group(1)))
        dist = float(match.group(2))
        q = int(match.group(3))

        # on ignore les mesures invalides (distance = 0 ou qualité faible)
        if dist <= 0 or q == 0:
            continue

        angles.append(angle)
        dists.append(dist)

        # rafraîchissement du graphique toutes les REFRESH_RATE secondes
        if time.time() - last_refresh > REFRESH_RATE:
            # on ne garde qu'un nombre limité de points
            if len(angles) > MAX_POINTS:
                angles = angles[-MAX_POINTS:]
                dists = dists[-MAX_POINTS:]

            points.set_data(angles, dists)
            plt.draw()
            plt.pause(0.001)

            # reset buffers pour un affichage "en direct"
            angles.clear()
            dists.clear()
            last_refresh = time.time()

except KeyboardInterrupt:
    print("\n[STOP] Arrêt demandé par l'utilisateur.")
    proc.send_signal(signal.SIGTERM)
    proc.wait()
    print("[INFO] LiDAR arrêté proprement.")
    plt.ioff()
    plt.show()
