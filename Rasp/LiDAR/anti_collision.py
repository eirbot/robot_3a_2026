#!/usr/bin/env python3
import socket
import struct

UDP_IP = "127.0.0.1"
UDP_PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# J'ai enlevé le timeout strict pour faciliter ton debug
print("[ANTI-COLLISION] Démarrage de la surveillance avec INTENSITÉ...")

try:
    while True:
        data, addr = sock.recvfrom(12)
        
        if len(data) == 12:
            angle, dist, intensity = struct.unpack('<fff', data)
            
            if dist < 300.0:
                print(f"[🛑 COLLISION] Dist: {dist:.0f} mm | Angle: {angle:.1f}° | Intensité: {intensity:.0f}")
                
except KeyboardInterrupt:
    print("\nArrêt du client Python.")
    sock.close()