#!/usr/bin/env python3
import socket
import struct
from localise import calculer_pose

if __name__ == '__main__':
    # --- Écoute UDP ---
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 8080))
    
    print("[LOCALISATION] En attente de 3 balises...")
    
    try:
        while True:
            data, _ = sock.recvfrom(52)
            if len(data) == 52:
                unpacked = struct.unpack('<fff i fffffffff', data)
                num_beacons = unpacked[3]
                
                if num_beacons == 3:
                    mesures = [(unpacked[4], unpacked[5]), (unpacked[7], unpacked[8]), (unpacked[10], unpacked[11])]
                    result, status = calculer_pose(mesures)
                    
                    if status == "OK":
                        x, y, theta, err = result
                        print(f"✅ POSITION : X={x:4.0f} | Y={y:4.0f} | Cap={theta:5.1f}°  (Bruit: {err:.0f}mm)")
                    else:
                        # On affiche la raison du rejet (utile pour le debug)
                        pass 
                        # Décommente la ligne du dessous si tu veux voir les rejets
                        # print(f"⚠️ {status}")
                
    except KeyboardInterrupt:
        sock.close()