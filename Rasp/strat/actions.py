# strat/actions.py
import time
import math
import ihm.shared as shared

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
        """Définit la position de départ (Téléportation logique)"""
        # On convertit les coordonnées Strat (Bleu) en Réel (Selon équipe)
        real_x, real_y, real_theta = self._apply_sym(x, y, theta)
        
        # On met à jour la position connue du robot
        shared.robot_pos['x'] = real_x
        shared.robot_pos['y'] = real_y
        shared.robot_pos['theta'] = real_theta
        
        team_color = "JAUNE" if self.is_yellow else "BLEU"
        print(f"[ACTION] 🏁 DEPART {team_color} défini à ({real_x}, {real_y}, {real_theta}°)")

    # --- LE COEUR DU SUJET : GOTO BEZIER ---
    def goto(self, x, y, theta, force=500):
        """
        Déplacement via Courbe de Bézier.
        x, y, theta : Destination (Coordonnées BLEUES)
        force : Puissance de la tangente (en mm). ~Distance P0-P1 et P3-P2.
        """
        self._check_abort()
        
        # 1. Où est le robot maintenant ? (P0)
        # On récupère la position réelle (déjà symétrisée par l'odométrie)
        p0_x = shared.robot_pos['x']
        p0_y = shared.robot_pos['y']
        theta_start = shared.robot_pos['theta']

        # 2. Où veut-on aller ? (P3)
        # On convertit la cible "Stratégie" (Bleu) en "Réel" (Selon équipe)
        p3_x, p3_y, theta_end = self._apply_sym(x, y, theta)

        print(f"[ACTION] Bezier -> Cible({p3_x:.0f}, {p3_y:.0f}, {theta_end:.0f}°) Force({force})")

        # 3. Calculs Mathématiques des Points de Contrôle (P1 et P2)
        # Conversion degrés -> radians
        rad_start = math.radians(theta_start)
        rad_end = math.radians(theta_end)

        # CALCUL DE P1 (Sortie du point de départ)
        # P1 est projeté "devant" le robot actuel selon son angle
        p1_x = p0_x + force * math.cos(rad_start)
        p1_y = p0_y + force * math.sin(rad_start)

        # CALCUL DE P2 (Entrée dans le point d'arrivée)
        # P2 est projeté "derrière" la cible.
        # Pourquoi (-) ? Parce que pour arriver avec l'angle theta_end, 
        # la courbe doit venir de l'opposé du vecteur direction.
        p2_x = p3_x - force * math.cos(rad_end)
        p2_y = p3_y - force * math.sin(rad_end)

        # --- DEBUG : Affiche les points pour vérifier ---
        # Tu pourras passer ces points (p1_x, p1_y) et (p2_x, p2_y) au code de ton pote
        # print(f"   Points de controle : P1({p1_x:.0f}, {p1_y:.0f}) | P2({p2_x:.0f}, {p2_y:.0f})")

        # 4. ENVOI AU CONTROLE MOTEUR
        # TODO: Remplacer ce print par l'appel réel à ton driver moteur
        # Exemple : self.motor_driver.add_bezier(p1=(p1_x,p1_y), p2=(p2_x,p2_y), p3=(p3_x,p3_y))
        
        # 5. SIMULATION (Pour attendre que le robot ait fini virtuellement)
        dist = math.sqrt((p3_x - p0_x)**2 + (p3_y - p0_y)**2)
        simulated_duration = dist / 300.0 # Supposons 300mm/s
        steps = int(simulated_duration * 10)
        
        for _ in range(max(1, steps)):
            time.sleep(0.1)
            self._check_abort()

        # 6. Mise à jour de la position finale (Triche IHM)
        shared.robot_pos['x'] = p3_x
        shared.robot_pos['y'] = p3_y
        shared.robot_pos['theta'] = theta_end

    def stop(self):
        print("[ACTION] STOP")

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