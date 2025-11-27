#!/usr/bin/env python3
from ekf_localizer import EKFLocalizer
import time
import numpy as np

# --- CONFIGURATION DU DEPART ---
# Mesure approximativement où tu poses le robot sur la table.
# Exemple : x=500mm, y=0mm, et robot tourné de 90 degrés (pi/2)
depart_x = 500.0
depart_y = 0.0
depart_theta_deg = 0.0  # 0° = vers le bas de la table (axe X)

# Conversion en radians pour l'EKF
init_pose = (depart_x, depart_y, np.radians(depart_theta_deg))

print(f"Initialisation à : {init_pose}")

# --- INSTANTIATION ---
# On passe init_pose à la création de l'objet
ekf = EKFLocalizer("/dev/ttyUSB0", init_pose=init_pose)

ekf.start_scan()
time.sleep(1.0) # Temps de chauffe

print("--- Démarrage Localisation ---")

try:
    while True:
        ekf.clean_input() # Vider le buffer (Crucial !)
        
        # Prédiction (indispensable pour la covariance)
        ekf.predict(dt=0.1, v=0.0, w=0.0)

        # Localisation
        pose, nb, obs = ekf.locate_once()

        if pose:
            x, y, th = pose
            print(f"[POS] x={x:6.0f} y={y:6.0f} th={np.degrees(th):6.1f}° | Balises: {nb}")
        else:
            print(f"[PERDU] Aucune balise matchée. Le robot est-il bien à {depart_x}, {depart_y} ?")

except KeyboardInterrupt:
    print("Arrêt.")
    ekf.close()