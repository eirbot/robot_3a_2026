import math
import itertools

# --- CONFIGURATION DU TERRAIN ---
BALISES = [
    (-50, 1950),    # Balise 1 : Haut Gauche
    (-50, 50),      # Balise 2 : Bas Gauche
    (2950, 1000)    # Balise 3 : Milieu Droit
]

RAYON_BALISE = 50.0         # mm (Balises fixes du terrain)
RAYON_BALISE_ADVERSE = 45.0 # mm (Mât de l'adversaire)

def trilateration(b1, r1, b2, r2, b3, r3):
    x1, y1 = b1; x2, y2 = b2; x3, y3 = b3
    A = 2 * (x2 - x1)
    B = 2 * (y2 - y1)
    C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
    D = 2 * (x3 - x1)
    E = 2 * (y3 - y1)
    F = r1**2 - r3**2 - x1**2 + x3**2 - y1**2 + y3**2

    det = A * E - B * D
    if abs(det) < 1e-6: return None 

    x = (C * E - B * F) / det
    y = (A * F - C * D) / det
    return x, y

def calculer_pose(mesures_lidar):
    """
    Déduit la position X, Y et Cap (Degrés) via Trilateration et filtrages.
    Rejette les solutions mathématiques miroirs ou farfelues hors table.
    """
    if len(mesures_lidar) < 3: return None, "Pas assez de balises"

    best_x, best_y, best_theta = 0, 0, 0
    min_error = float('inf')
    found_valid_permutation = False
    
    for perm in itertools.permutations(mesures_lidar):
        r1, a1_brut = perm[0][1] + RAYON_BALISE, perm[0][0]
        r2, a2_brut = perm[1][1] + RAYON_BALISE, perm[1][0]
        r3, a3_brut = perm[2][1] + RAYON_BALISE, perm[2][0]

        # Inversion de l'angle (Horaire -> Anti-horaire trigonométrique)
        a1 = (360.0 - a1_brut) % 360.0
        a2 = (360.0 - a2_brut) % 360.0

        pos = trilateration(BALISES[0], r1, BALISES[1], r2, BALISES[2], r3)
        if not pos: continue
        x, y = pos

        # --- FILTRE : ZONE DE JEU (Bounding Box) ---
        if not (-300.0 <= x <= 3300.0) or not (-300.0 <= y <= 2300.0):
            continue 

        # --- FILTRE : ANTI-MIROIR ---
        expected_ang1 = math.atan2(BALISES[0][1] - y, BALISES[0][0] - x)
        expected_ang2 = math.atan2(BALISES[1][1] - y, BALISES[1][0] - x)
        
        expected_diff = (expected_ang2 - expected_ang1) % (2*math.pi)
        actual_diff = math.radians(a2 - a1) % (2*math.pi)
        
        err_angle = abs(expected_diff - actual_diff)
        if err_angle > math.pi: err_angle = 2*math.pi - err_angle
        
        if err_angle > 1.0: 
            continue

        # --- CALCUL ERREUR GÉOMÉTRIQUE GLOBALE ---
        err1 = abs(math.hypot(x - BALISES[0][0], y - BALISES[0][1]) - r1)
        err2 = abs(math.hypot(x - BALISES[1][0], y - BALISES[1][1]) - r2)
        err3 = abs(math.hypot(x - BALISES[2][0], y - BALISES[2][1]) - r3)
        total_error = err1 + err2 + err3

        found_valid_permutation = True

        if total_error < min_error:
            min_error = total_error
            best_x, best_y = x, y
            theta_rad = expected_ang1 - math.radians(a1)
            best_theta = math.degrees((theta_rad + math.pi) % (2 * math.pi) - math.pi)

    if not found_valid_permutation:
        return None, "Rejet : Fantôme Hors Table ou Image Miroir"

    # Tolérance élargie (Le Kalman gèrera le lissage de l'erreur en mouvement)
    if min_error > 600.0:
        return None, f"Rejet : Erreur mathématique trop haute ({min_error:.0f}mm)"
        
    return (best_x, best_y, best_theta, min_error), "OK"

def calculer_position_adversaire(mon_x, mon_y, mon_cap_deg, obs_angle_brut, obs_dist_mm):
    """
    Calcule la position absolue (X, Y) du robot adverse sur la table.
    """
    if obs_dist_mm > 4000.0: return None

    # Inversion du sens de rotation du LiDAR
    obs_angle_relatif = (360.0 - obs_angle_brut) % 360.0
    
    # Angle absolu sur la table
    angle_absolu_rad = math.radians(mon_cap_deg + obs_angle_relatif)
    
    # Distance jusqu'au CENTRE du mât adverse
    dist_centre = obs_dist_mm + RAYON_BALISE_ADVERSE
    
    # Projection Trigonométrique
    adv_x = mon_x + dist_centre * math.cos(angle_absolu_rad)
    adv_y = mon_y + dist_centre * math.sin(angle_absolu_rad)
    
    # FILTRE : L'obstacle doit être sur la table (ignore les arbitres en dehors)
    if -50 <= adv_x <= 3050 and -50 <= adv_y <= 2050:
        return (adv_x, adv_y)
        
    return None