# strat/main_strat.py
import time
import importlib
import threading
import ihm.shared as shared

# Import des actions et de l'exception
from strat.actions import RobotActions, EndOfMatchException

def get_strategy_module(strat_id):
    """Charge le fichier de stratégie correspondant à l'ID"""
    try:
        # Mapping ID -> Nom du fichier (sans .py)
        # Assure-toi d'avoir créé le fichier 'strat/strategies/strat_homologation.py'
        strats = {
            1: "strat.strategies.strat_homologation",
            2: "strat.strategies.strat_match_1",
            # Ajoute tes autres strats ici
        }
        mod_name = strats.get(strat_id, strats.get(1)) # ID 1 par défaut
        return importlib.import_module(mod_name)
    except ImportError as e:
        print(f"[STRAT] Erreur : Fichier de stratégie introuvable ({e})")
        return None
    except Exception as e:
        print(f"[STRAT] Erreur chargement module : {e}")
        return None

def strat_loop():
    print("[STRAT] Thread démarré. Prêt.")
    
    # On instancie les actions (connexion hardware virtuelle ou réelle)
    robot = RobotActions()
    
    # Machine à état simple
    state_fsm = "WAIT_START"
    
    while True:
        # --- ETAT 1 : ATTENTE DEPART ---
        if state_fsm == "WAIT_START":
            if shared.state["match_running"]:
                print(f"[STRAT] GO ! Lancement Stratégie #{shared.state['strat_id']}")
                # Important : On remet le flag de retour à zéro
                robot.is_returning = False 
                state_fsm = "RUNNING"
            else:
                time.sleep(0.1)

        # --- ETAT 2 : MATCH EN COURS ---
        elif state_fsm == "RUNNING":
            try:
                # 1. Chargement dynamique de la stratégie
                module = get_strategy_module(shared.state["strat_id"])
                
                if module:
                    # 2. Exécution de la stratégie
                    # C'est ici que ça tourne pendant 90s
                    module.run(robot)
                
                print("[STRAT] Stratégie terminée en avance. On attend la fin.")
                # Si tu veux qu'il rentre dès qu'il a fini, décommente la ligne dessous :
                # robot.GoBase()

            except EndOfMatchException:
                # 3. INTERCEPTION DU TEMPS (90s)
                print("[STRAT] ⚠️ TIMEOUT 90s -> FORCAGE RETOUR BASE")
                robot.GoBase()
                
            except Exception as e:
                # 4. Gestion des erreurs (Stop bouton, crash code...)
                print(f"[STRAT] Arrêt ou Erreur : {e}")
                robot.stop()
            
            finally:
                # Quoi qu'il arrive, le match est considéré comme fini pour la strat
                state_fsm = "FINISHED"

        # --- ETAT 3 : FIN DE MATCH ---
        elif state_fsm == "FINISHED":
            # On attend que l'utilisateur fasse "Reset" sur l'IHM
            if not shared.state["match_running"]:
                print("[STRAT] Reset reçu. Retour en attente.")
                state_fsm = "WAIT_START"
            time.sleep(0.5)