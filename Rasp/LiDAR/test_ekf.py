#!/usr/bin/env python3
from ekf_localizer import EKFLocalizer
import time

ekf = EKFLocalizer("/dev/ttyUSB0")

ekf.start_scan()
time.sleep(0.2)

while True:
    pose, nb, obs = ekf.locate_once()

    if pose:
        x, y, th = pose
        print(f"[POSE] x={x:.1f} mm  y={y:.1f} mm  th={th*180/3.1416:.1f}°  (balises vues: {nb})")

    time.sleep(0.5)
