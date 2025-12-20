# strat/actions.py
import time
import ihm.shared as shared

# --- CONSTANTES ---
TABLE_WIDTH = 3000   # Largeur de la table en mm
TIME_TO_RETURN = 90  # Temps (s) où le robot doit tout lâcher pour rentrer

# --- EXCEPTION PERSONNALISÉE ---
class EndOfMatchException(Exception):
    """Levée quand il est temps de rentrer à la base"""
    pass

class RobotActions:
    def __init__(self):
        self.is_returning = False # Sécurité pour ne pas vérifier le temps PENDANT le retour

    @property
    def is_yellow(self):
        """Retourne True si l'équipe est JAUNE"""
        return shared.state["team"] == "JAUNE"

    # --- VERIFICATIONS SECURITE ---
    def _check_time(self):
        """Vérifie le timer et lève une alerte si > 90s"""
        # Si on est déjà en train de rentrer, on ignore (sinon on boucle à l'infini)
        if self.is_returning:
            return

        if shared.state["match_running"] and shared.state["start_time"]:
            elapsed = time.time() - shared.state["start_time"]
            if elapsed >= TIME_TO_RETURN:
                print(f"[ACTION] 🚨 TEMPS LIMITE ATTEINT ({elapsed:.1f}s) ! ABANDON !")
                raise EndOfMatchException("Time to go home")

    def _check_abort(self):
        """Vérifie si le match est stoppé OU si c'est l'heure de rentrer"""
        # 1. Vérification Stop Urgence / Fin match manuelle
        if not shared.state["match_running"]:
            raise Exception("Match Interrompu par l'utilisateur")
        
        # 2. Vérification du Chrono
        self._check_time()

    def _apply_sym(self, x, y, theta=None):
        """Convertit les coordonnées BLEUES en coordonnées REELLES (Jaune/Bleu)"""
        if self.is_yellow:
            # --- SYMETRIE AXIALE (Miroir) ---
            new_x = TABLE_WIDTH - x
            new_y = y # Pas de changement en Y
            
            new_theta = None
            if theta is not None:
                new_theta = (180 - theta) % 360
            
            return new_x, new_y, new_theta
        else:
            # --- BLEU (Référence) ---
            return x, y, theta

    # --- DEPLACEMENTS ---
    def goto(self, x, y, theta=None):
        """Aller à un point (Coordonnées BLEUES)"""
        self._check_abort()
        
        # 1. Calcul de la vraie position cible
        real_x, real_y, real_theta = self._apply_sym(x, y, theta)
        
        team_str = "JAUNE" if self.is_yellow else "BLEU"
        print(f"[ACTION] {team_str} | Goto Virtuel({x}, {y}) -> Réel({real_x}, {real_y})")
        
        # TODO: Envoyer ici la commande au vrai robot (Serial)
        # serial_motors.send(f"GOTO {real_x} {real_y} {real_theta}")

        # 2. Simulation du mouvement (avec vérification du temps PENDANT le trajet)
        # On découpe l'attente en petits morceaux pour être réactif
        steps = 20 # 2 secondes total (20 * 0.1)
        for _ in range(steps):
            time.sleep(0.1)
            self._check_abort() # Vérifie si on dépasse 90s pendant qu'on roule

        # 3. Mise à jour position sur la carte (Triche IHM)
        shared.robot_pos['x'] = real_x
        shared.robot_pos['y'] = real_y
        if real_theta is not None:
            shared.robot_pos['theta'] = real_theta

    def stop(self):
        """Arrêt d'urgence"""
        print("[ACTION] STOP MOTEURS")
        # serial_motors.send("STOP")

    # --- ACTIONNEURS SPECIFIQUES ---
    def prendreKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Prise Kapla (Hauteur: {hauteur}mm)")
        # Simulation délai
        time.sleep(1)
        self._check_abort()

    def poseKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Pose Kapla (Hauteur: {hauteur}mm)")
        time.sleep(1)
        shared.state["score_current"] += 5 # On marque des points

    # --- RETOUR BASE AUTO ---
    def GoBase(self):
        """Rentre à la base (Appelé automatiquement à 90s)"""
        self.is_returning = True # On désactive la vérification du temps
        print("⚡ ACTIVATION PROTOCOLE RETOUR BASE ⚡")
        
        # Coordonnées de la BASE BLEUE (à adapter selon ta table)
        base_x = 250
        base_y = 1000
        base_theta = 180
        
        try:
            # On utilise goto (la symétrie se fera toute seule)
            self.goto(base_x, base_y, base_theta)
            
            # Action de fin (Funny Action)
            print("[BASE] Arrivé ! Déploiement drapeau / Funny Action...")
            time.sleep(1)
            shared.state["score_current"] += 20 # Points de fin
            
        except Exception as e:
            print(f"[BASE] Erreur critique pendant le retour : {e}")