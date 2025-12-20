# strat/main_strat.py
import time
import importlib
import shared as shared
from actions import RobotActions

def get_strategy_module(strat_id):
    """Charge dynamiquement le fichier de strat selon l'ID"""
    try:
        # Mapping ID -> Fichier
        strats = {
            1: "strat.strategies.strat_homologation",
            2: "strat.strategies.strat_match_1"
        }
        mod_name = strats.get(strat_id, strats[1]) # Par défaut la 1
        return importlib.import_module(mod_name)
    except Exception as e:
        print(f"[STRAT] Erreur chargement strat {strat_id} : {e}")
        return None

def strat_loop():
    print("[STRAT] Thread démarré. En attente...")
    robot = RobotActions()
    
    state_fsm = "WAIT_START"
    
    while True:
        # --- ETAT 1 : ATTENTE DEPART ---
        if state_fsm == "WAIT_START":
            if shared.state["match_running"]:
                print(f"[STRAT] GO ! Lancement Strat #{shared.state['strat_id']}")
                state_fsm = "RUNNING"
            else:
                time.sleep(0.1)

        # --- ETAT 2 : MATCH EN COURS ---
        elif state_fsm == "RUNNING":
            try:
                # 1. On charge le fichier de strat choisi dans l'IHM
                module = get_strategy_module(shared.state["strat_id"])
                
                if module:
                    # 2. On lance la fonction run() du fichier
                    module.run(robot)
                
                # Si la strat finit avant les 100s, on attend
                print("[STRAT] Stratégie terminée avec succès.")
                state_fsm = "FINISHED"

            except Exception as e:
                # Catch l'exception levée par _check_abort si le match est stoppé
                print(f"[STRAT] Arrêt : {e}")
                robot.stop()
                state_fsm = "WAIT_RESET"

        # --- ETAT 3 : FINI (Attente Reset) ---
        elif state_fsm == "FINISHED" or state_fsm == "WAIT_RESET":
            if not shared.state["match_running"]:
                state_fsm = "WAIT_START"
                print("[STRAT] Réinitialisation. Prêt.")
            time.sleep(0.5)