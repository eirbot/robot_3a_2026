# strat/actions.py
import time
import math
import ihm.shared as shared

# --- CORRECTION DES IMPORTS ---
try:
    # On essaie d'importer le module Bezier
    import interface_deplacement.bezier as Bezier
    
    # On essaie d'importer directement la fonction 'envoyer' depuis interface_deplacement.py
    # (Assure-toi que la fonction s'appelle bien 'envoyer' dans ce fichier, sinon change le nom ici)
    from interface_deplacement.interface_deplacement import envoyer

except ImportError as e:
    print(f"⚠️ Attention : Modules de déplacement non trouvés ({e}) -> Mode Simulation pur")
    Bezier = None
    envoyer = None  # On définit envoyer à None pour que les 'if envoyer:' fonctionnent

# --- CONSTANTES ---
TABLE_WIDTH = 3000
TIME_TO_RETURN = 90

class EndOfMatchException(Exception):
    pass

class RobotActions:
    def __init__(self):
        self.is_returning = False

    @property
    def is_yellow(self):
        return shared.state["team"] == "JAUNE"

    def _check_time(self):
        if self.is_returning: return
        if shared.state["match_running"] and shared.state["start_time"]:
            if time.time() - shared.state["start_time"] >= TIME_TO_RETURN:
                raise EndOfMatchException("Time to go home")

    def _check_abort(self):
        if not shared.state["match_running"]: raise Exception("Stop")
        self._check_time()

    def _apply_sym(self, x, y, theta=None):
        """Symétrie axiale pour l'équipe JAUNE"""
        if self.is_yellow:
            new_x = TABLE_WIDTH - x
            new_y = y
            new_theta = (180 - theta) % 360 if theta is not None else None
            return new_x, new_y, new_theta
        return x, y, theta
    
    def set_pos(self, x, y, theta):
        """
        Définit la position du robot (Triche / Recalage).
        Met à jour l'IHM Web ET l'odométrie de l'ESP32.
        """
        # 1. Calcul de la position réelle (Symétrie équipe)
        real_x, real_y, real_theta = self._apply_sym(x, y, theta)
        
        # 2. Mise à jour Interface Web (Shared)
        shared.robot_pos.update({'x': real_x, 'y': real_y, 'theta': real_theta})
        print(f"[ACTION] SET_POS -> ({real_x}, {real_y}, {real_theta}°)")

        # 3. Envoi à l'ESP32 (Reset Odométrie)
        # On utilise la variable 'envoyer' définie dans les imports
        if envoyer:
            envoyer("SET POSE") # Adapter selon le format attendu par ton interface
        else:
            print("[SIMU] SET_POS virtuel (Pas de com)")

    # --- LE COEUR DU SUJET : GOTO BEZIER ---
    def goto(self, x, y, theta, force=500):
        """
        Déplacement via Courbe de Bézier + Envoi ESP32
        """
        self._check_abort()
        
        # 1. Position actuelle (P0) et Angle départ
        p0_x = shared.robot_pos['x']
        p0_y = shared.robot_pos['y']
        theta_start = shared.robot_pos['theta']

        # 2. Cible (P3) avec Symétrie
        p3_x, p3_y, theta_end = self._apply_sym(x, y, theta)

        print(f"[ACTION] Bezier -> ({p3_x:.0f}, {p3_y:.0f}, {theta_end:.0f}°) Force={force}")

        # 3. Calcul P1 et P2
        rad_start = math.radians(theta_start)
        rad_end = math.radians(theta_end)

        p1_x = p0_x + force * math.cos(rad_start)
        p1_y = p0_y + force * math.sin(rad_start)

        p2_x = p3_x - force * math.cos(rad_end)
        p2_y = p3_y - force * math.sin(rad_end)

        # 4. GÉNÉRATION DES POINTS ET ENVOI
        # Correction ici : on utilise 'envoyer' uniformément
        if Bezier and envoyer:
            try:
                # Génération d'une liste de points (ex: 50 points)
                points_bezier = Bezier.bezier_cubique_discret(
                    10, 
                    (p0_x, p0_y), 
                    (p1_x, p1_y), 
                    (p2_x, p2_y), 
                    (p3_x, p3_y)
                )
                
                # Envoi via Série
                envoyer(points_bezier)
            except Exception as e:
                print(f"[ERREUR] Échec envoi trajectoire : {e}")
            
        else:
            # 5. MODE SIMULATION (Si pas de driver ou pas d'ESP)
            print("[SIMU] Pas de connexion ESP, simulation du temps de trajet...")
            dist = math.sqrt((p3_x - p0_x)**2 + (p3_y - p0_y)**2)
            # Vitesse arbitraire pour la simulation (300mm/s)
            simulated_duration = dist / 300.0 
            steps = int(simulated_duration * 10)
            
            for _ in range(max(1, steps)):
                time.sleep(0.1)
                self._check_abort()

            # Mise à jour finale triche
            shared.robot_pos['x'] = p3_x
            shared.robot_pos['y'] = p3_y
            shared.robot_pos['theta'] = theta_end

    def stop(self):
        print("[ACTION] STOP")
        # Si on a la com, on envoie un arrêt
        if envoyer:
            # Adapter selon ton protocole (ex: envoyer([0,0]) ou string "STOP")
            pass 

    def prendreKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Prise Kapla H={hauteur}")
        time.sleep(1)

    def retournerKapla(self):
        self._check_abort()
        print("[ACTION] Retourne Kapla")
        time.sleep(1)

    def poseKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Pose Kapla H={hauteur}")
        time.sleep(1)

    def GoBase(self):
        self.is_returning = True
        print("⚡ RETOUR BASE")
        # Retour base avec une grosse force pour une belle courbe large
        self.goto(250, 1000, 180, force=800)
        time.sleep(1)