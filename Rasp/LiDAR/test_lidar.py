#!/usr/bin/env python3
import serial, struct, numpy as np, matplotlib.pyplot as plt, time

PORT = "/dev/ttyUSB0"
BAUD = 460800

print(f"[INIT] Ouverture du port {PORT} à {BAUD} bauds ...")
ser = serial.Serial(PORT, BAUD, timeout=0.05)
ser.reset_input_buffer()
time.sleep(0.2)

print("[SEND] Envoi commande 0xA5 0x82 (mode TOF dense)")
ser.write(b"\xA5\x82")
time.sleep(0.2)

plt.ion()
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
points = ax.scatter([], [], c=[], cmap='turbo', s=6)
ax.set_rmax(4000)
ax.grid(True)
ax.set_title("RPLIDAR C1M1-R2 — Mode TOF Dense (debug)")

buffer = bytearray()
t0 = time.time()
frame_count = 0

try:
    while True:
        chunk = ser.read(1024)
        if chunk:
            buffer.extend(chunk)
            print(f"[DATA] +{len(chunk)} bytes (total buffer={len(buffer)})")

        # Si pas assez de données, on attend
        if len(buffer) < 6:
            continue

        # On traite tous les paquets complets
        n = len(buffer) // 6
        data = buffer[:n * 6]
        buffer = buffer[n * 6:]

        if n > 0:
            frame_count += 1
            print(f"[FRAME {frame_count}] {n} points reçus")

        angles, dists, intens = [], [], []
        for i in range(n):
            dist, ang, inten = struct.unpack_from("<HHH", data, i * 6)
            angle = (ang / 64.0) % 360
            if 50 < dist < 10000:
                angles.append(np.radians(angle))
                dists.append(dist)
                intens.append(inten)

        if len(angles) > 0:
            print(f"  ↳ {len(angles)} points valides, "
                  f"angle≈{np.degrees(np.mean(angles))%360:.1f}°, "
                  f"dist≈{np.mean(dists):.0f} mm, "
                  f"intensité moyenne={np.mean(intens):.0f}")

            points.set_offsets(np.c_[angles, dists])
            points.set_array(np.array(intens))
            plt.pause(0.001)

        # affiche le débit toutes les ~2 secondes
        if time.time() - t0 > 2:
            print(f"[STATS] {frame_count} frames en {time.time()-t0:.1f}s "
                  f"→ {frame_count/(time.time()-t0):.1f} FPS")
            t0 = time.time()
            frame_count = 0

except KeyboardInterrupt:
    print("\n[STOP] arrêt demandé par l'utilisateur.")
finally:
    ser.close()
    plt.ioff()
    plt.show()
