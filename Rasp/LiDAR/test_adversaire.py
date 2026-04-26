#!/usr/bin/env python3
import socket
import struct
import math

# --- LA FONCTION DE TON LIDAR_LOCALIZER ---
RAYON_BALISE_ADVERSE = 45.0 

def calculer_position_adversaire(mon_x, mon_y, mon_cap_deg, obs_angle_brut, obs_dist_mm):
    if obs_dist_mm > 4000.0: 
        return None
        
    obs_angle_relatif = (360.0 - obs_angle_brut) % 360.0
    angle_absolu_rad = math.radians(mon_cap_deg + obs_angle_relatif)
    dist_centre = obs_dist_mm + RAYON_BALISE_ADVERSE
    
    adv_x = mon_x + dist_centre * math.cos(angle_absolu_rad)
    adv_y = mon_y + dist_centre * math.sin(angle_absolu_rad)
    
    # Filtre de zone (Table Eurobot)
    if -50 <= adv_x <= 3050 and -50 <= adv_y <= 2050:
        return (adv_x, adv_y)
    return None

# --- CONFIGURATION UDP (Connecté au vrai C++) ---
UDP_IP = "127.0.0.1"
UDP_PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# --- POSITION FIXE DU ROBOT POUR LE TEST ---
# On fait comme si le robot ne bougeait pas de sa zone de départ
MON_X_TEST = 2700.0
MON_Y_TEST = 1700.0
MON_CAP_TEST = -90.0

print(f"[TEST ADVERSAIRE] Écoute UDP...")
print(f"Robot théoriquement fixé en X={MON_X_TEST}, Y={MON_Y_TEST}, Cap={MON_CAP_TEST}°")
print("-> Passe ta main ou un obstacle devant le LiDAR !\n")

try:
    while True:
        data, _ = sock.recvfrom(52)
        
        if len(data) == 52:
            unpacked = struct.unpack('<fff i fffffffff', data)
            
            # Récupération de l'obstacle envoyé par le C++
            obs_angle_brut = unpacked[0]
            obs_dist = unpacked[1]
            obs_qual = unpacked[2]

            # On vérifie qu'il y a bien un obstacle (distance < 99999)
            if obs_dist < 4000.0:
                pos_adv = calculer_position_adversaire(
                    MON_X_TEST, MON_Y_TEST, MON_CAP_TEST, 
                    obs_angle_brut, obs_dist
                )
                
                if pos_adv:
                    adv_x, adv_y = pos_adv
                    print(f"🤖 ADVERSAIRE : X={adv_x:4.0f} | Y={adv_y:4.0f}  (Dist brute: {obs_dist:.0f}mm à {obs_angle_brut:.1f}°)")
                else:
                    # L'obstacle est trop loin et sort de la table (ex: tes jambes hors du terrain)
                    # print(f"⚠️ Ignoré (Hors Table) - Dist: {obs_dist:.0f}mm")
                    pass

except KeyboardInterrupt:
    print("\nArrêt du test.")
    sock.close()