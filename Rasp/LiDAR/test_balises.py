#!/usr/bin/env python3
import socket
import struct

UDP_IP = "127.0.0.1"
UDP_PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("[TEST BALISES] En attente des données LiDAR...")

try:
    while True:
        data, addr = sock.recvfrom(52) # On écoute 52 octets
        
        if len(data) == 52:
            # Format: 
            # < : Little-endian
            # fff : Obstacle (Angle, Dist, Qual)
            # i : Nombre de balises
            # fff fff fff : Les 3 balises (Angle, Dist, Qual)
            unpacked = struct.unpack('<fff i fffffffff', data)
            
            obs_angle, obs_dist, obs_qual = unpacked[0:3]
            num_beacons = unpacked[3]
            
            # Affichage de l'anti-collision (si obstacle proche)
            if obs_dist < 300.0:
                 print(f"[🛑 COLLISION] Obstacle à {obs_dist:.0f} mm !")
            
            # Affichage des balises détectées
            if num_beacons > 0:
                print(f"--- {num_beacons} Balise(s) détectée(s) ---")
                
                # On boucle sur le nombre de balises trouvées (max 3)
                for i in range(num_beacons):
                    b_angle = unpacked[4 + i*3]
                    b_dist = unpacked[5 + i*3]
                    b_qual = unpacked[6 + i*3]
                    print(f"📍 Balise {i+1} : {b_dist:.0f} mm à {b_angle:.1f}° (Intensité: {b_qual:.0f})")
                    
except KeyboardInterrupt:
    print("\nArrêt.")
    sock.close()