#!/usr/bin/env python3
# from rplidar_c1m1 import RPLidarC1M1

# lidar = RPLidarC1M1("/dev/ttyUSB0")

# try:
#     lidar.plot_live_pygame_threaded(rmax=4000, fps=15)
# except KeyboardInterrupt:
#     lidar.close()

from rplidar_c1m1 import RPLidarC1M1
import time
import numpy as np

lidar = RPLidarC1M1("/dev/ttyUSB0")
lidar.start_scan()
lidar.clean_input()

print("--- MODE CALIBRATION ---")
print("Place un objet DEVANT le robot, puis à GAUCHE.")

try:
    while True:
        lidar.clean_input()
        scan = lidar.get_scan()
        if scan is None: continue
        
        # On prend le point le plus proche (supposé être l'objet de test)
        dists = scan[:, 1]
        angles = scan[:, 0] # Degrés
        
        valid = (dists > 50) & (dists < 800) # On regarde juste entre 5cm et 80cm
        if np.any(valid):
            i = np.argmin(dists[valid])
            nearest_dist = dists[valid][i]
            nearest_angle = angles[valid][i]
            
            print(f"Objet le plus proche : {nearest_dist:.0f}mm à {nearest_angle:.1f}°")
        else:
            print("Rien vu de proche...")
            
        time.sleep(0.2)
except KeyboardInterrupt:
    lidar.close()
