#!/usr/bin/env python3
from rplidar_c1m1 import RPLidarC1M1

lidar = RPLidarC1M1("/dev/ttyUSB0")

try:
    lidar.plot_live_pygame_threaded(rmax=4000, fps=15)
except KeyboardInterrupt:
    lidar.close()
