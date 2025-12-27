# strat/strategies/strat_homologation.py
from strat import RobotActions

# --- METADONNÉES POUR L'IHM ---
METADATA = {
    "name": "Homologation",   # Nom affiché
    "score": 69               # Score estimé
}

def run(robot):
    print("[STRAT] Démarrage Homologation !")
    
    # 1. On sort de la zone de départ
    robot.goto(1000, 1000, 90)
    
    # 2. On fait coucou avec le bras
    robot.prendreKapla(hauteur=0)
    robot.poseKapla(hauteur=10)
    
    # 3. On rentre
    robot.goto(200, 1000, 180)
    
    print("[STRAT] Homologation terminée.")