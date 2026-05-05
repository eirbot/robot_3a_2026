import math
import itertools

# --- RAJOUTE TA 4ÈME BALISE ICI ---
BALISES = [
    (50, -1550),    # Balise 1 : Haut Gauche
    (1950, -1550),      # Balise 2 : Bas Gauche
    (1000, 1550),   # Balise 3 : Milieu Droit
    (-125, -225)    # Balise 4 : <--- REMPLACE PAR TES VRAIES COORDONNÉES !
]

RAYON_BALISE = 50.0 
RAYON_BALISE_ADVERSE = 45.0 

def trilateration(b1, r1, b2, r2, b3, r3):
    """Calcule mathématiquement le croisement de 3 cercles."""
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


def calculer_pose_intelligente(mesures_lidar, est_x, est_y, est_cap_deg):
    if len(mesures_lidar) < 3: 
        return None, "Pas assez de balises envoyées par C++"

    est_cap_rad = math.radians(est_cap_deg)
    
    # NOUVEAU : Un dictionnaire pour s'assurer qu'une balise n'est matchée qu'une seule fois !
    associations = {}

    for angle_brut, dist in mesures_lidar:
        if dist < 10: continue # On ignore les mesures vides du C++
        
        dist_centre = dist + RAYON_BALISE
        angle_lidar_trigo = (360.0 - angle_brut) % 360.0
        angle_absolu = est_cap_rad + math.radians(angle_lidar_trigo)
        
        point_x = est_x + dist_centre * math.cos(angle_absolu)
        point_y = est_y + dist_centre * math.sin(angle_absolu)
        
        meilleure_balise = None
        min_dist = float('inf')
        
        for bx, by in BALISES:
            d = math.hypot(point_x - bx, point_y - by)
            if d < min_dist:
                min_dist = d
                meilleure_balise = (bx, by)
                
        # NOUVEAU : Tolérance réduite à 25 cm pour ignorer les faux reflets
        if min_dist < 250.0:
            # On ne garde que la mesure la PLUS PROCHE du centre théorique de la balise
            if meilleure_balise not in associations or min_dist < associations[meilleure_balise]['min_dist']:
                associations[meilleure_balise] = {
                    'rayon': dist_centre,
                    'angle_lidar_trigo': angle_lidar_trigo,
                    'min_dist': min_dist
                }

    # Si on a bien trouvé au moins 3 balises UNIQUES sur la table
    if len(associations) >= 3:
        cles = list(associations.keys())
        b1, r1 = cles[0], associations[cles[0]]['rayon']
        b2, r2 = cles[1], associations[cles[1]]['rayon']
        b3, r3 = cles[2], associations[cles[2]]['rayon']
        
        pos = trilateration(b1, r1, b2, r2, b3, r3)
        if not pos: return None, "Trilatération impossible (Points alignés)"
        
        x_calc, y_calc = pos
        
        dx = b1[0] - x_calc
        dy = b1[1] - y_calc
        angle_theorique_rad = math.atan2(dy, dx)
        
        cap_corrige_rad = angle_theorique_rad - math.radians(associations[cles[0]]['angle_lidar_trigo'])
        cap_corrige_deg = math.degrees((cap_corrige_rad + math.pi) % (2 * math.pi) - math.pi)
        
        erreur_totale = 0
        for bx, by in associations:
            erreur_totale += abs(math.hypot(x_calc - bx, y_calc - by) - associations[(bx, by)]['rayon'])
            
        # NOUVEAU : On rejette si la figure est trop déformée par une fausse balise
        if erreur_totale > 150.0:
            return None, f"Rejet : Figure trop déformée (Bruit {erreur_totale:.0f}mm)"
            
        return (x_calc, y_calc, cap_corrige_deg, erreur_totale), f"OK"
        
    return None, f"Rejet : Seulement {len(associations)} balises uniques associées"


def calculer_position_adversaire(mon_x, mon_y, mon_cap_deg, obs_angle_brut, obs_dist_mm):
    """
    (Fonction d'esquive pour plus tard)
    Calcule la position absolue (X, Y) du robot adverse sur la table.
    """
    if obs_dist_mm > 4000.0: return None

    obs_angle_relatif = (360.0 - obs_angle_brut) % 360.0
    angle_absolu_rad = math.radians(mon_cap_deg + obs_angle_relatif)
    dist_centre = obs_dist_mm + RAYON_BALISE_ADVERSE
    
    adv_x = mon_x + dist_centre * math.cos(angle_absolu_rad)
    adv_y = mon_y + dist_centre * math.sin(angle_absolu_rad)
    
    # Filtre Terrain Eurobot (À ajuster avec ton nouveau repère si tu veux t'en servir un jour)
    # if -50 <= adv_x <= 3050 and -2050 <= adv_y <= 2050:
    #     return (adv_x, adv_y)
        
    return (adv_x, adv_y)