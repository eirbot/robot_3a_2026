# strat/actions.py
import time
import ihm.shared as shared

class RobotActions:
    def __init__(self):
        self.team_color = shared.state["team"] # "BLEUE" ou "JAUNE"

    def _check_abort(self):
        """Vérifie si le match est toujours en cours, sinon lève une erreur pour arrêter la strat"""
        if not shared.state["match_running"]:
            raise Exception("Match Interrompu")

    # --- DEPLACEMENT ---
    def goto(self, x, y, theta=None):
        self._check_abort()
        print(f"[ACTION] Déplacement vers ({x}, {y}, {theta})")
        
        # TODO: Envoyer commande à l'ESP32 Moteurs ici
        # ex: serial_motors.send(f"GOTO {x} {y} {theta}")
        
        # Simulation du temps de trajet (bloquant pour la strat)
        time.sleep(2) 
        
        # Mise à jour triche position (pour voir sur la map)
        shared.robot_pos['x'] = x
        shared.robot_pos['y'] = y
        if theta: shared.robot_pos['theta'] = theta

    def stop(self):
        print("[ACTION] STOP URGENCE")
        # TODO: Envoyer STOP aux moteurs
    
    # --- ACTIONNEURS KAPLA ---
    def testKapla(self):
        self._check_abort()
        print("[ACTION] Test présence Kapla...")
        time.sleep(0.5)
        return True # Simule qu'il y en a un

    def prendreKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Prise Kapla (Hauteur: {hauteur}mm)")
        # TODO: Commande ESP32 Bras
        time.sleep(1)

    def retourneKapla(self, liste_kapla):
        self._check_abort()
        print(f"[ACTION] Retournement des Kaplas : {liste_kapla}")
        time.sleep(1.5)

    def poseKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Dépose Kapla (Hauteur: {hauteur}mm)")
        time.sleep(1)
        # On ajoute des points au score pour le fun
        shared.state["score_current"] += 5