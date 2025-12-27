# strat/main_strat.py
import time
import importlib
import os
import glob
import threading
import ihm.shared as shared
from strat.actions import RobotActions, EndOfMatchException

# Dossier des stratégies (relatif au main)
STRAT_DIR = "strat/strategies"

def discover_strategies():
    """
    Scanne les fichiers .py, charge les METADATA et retourne une liste.
    """
    strats = {}
    # On cherche tous les fichiers .py dans strat/strategies
    files = glob.glob(os.path.join(STRAT_DIR, "*.py"))
    
    print(f"[STRAT] Recherche de stratégies dans {STRAT_DIR}...")
    
    for filepath in files:
        filename = os.path.basename(filepath)
        if filename == "__init__.py": continue
        
        # Nom du module pour l'import (ex: strat.strategies.strat_match_1)
        mod_name = filename[:-3] # Enlève .py
        full_mod_path = f"strat.strategies.{mod_name}"
        
        try:
            # On importe temporairement pour lire les METADATA
            mod = importlib.import_module(full_mod_path)
            meta = getattr(mod, "METADATA", {"name": mod_name, "score": 0})
            
            # On stocke avec comme clé le nom de fichier sans 'strat_' si possible
            # ID unique = le nom du fichier (c'est plus simple que des numéros)
            strats[mod_name] = meta
            print(f"   -> Trouvé : {meta['name']} ({meta['score']} pts)")
            
        except Exception as e:
            print(f"   [ERREUR] Impossible de charger {filename}: {e}")

    return strats

# On charge la liste au démarrage du script
AVAILABLE_STRATS = discover_strategies()
# On envoie cette liste à l'IHM via shared
shared.strategies_list = AVAILABLE_STRATS 

def strat_loop():
    print("[STRAT] Thread démarré.")
    robot = RobotActions()
    
    # On initialise l'état dans le partagé pour l'affichage Web
    shared.state["fsm_state"] = "WAIT_START"
    
    while True:
        # On synchronise l'état local avec l'IHM à chaque tour de boucle
        current_state = shared.state["fsm_state"]

        # --- ETAT 1 : ATTENTE ---
        if current_state == "WAIT_START":
            if shared.state["match_running"]:
                print(f"[STRAT] GO ! Lancement : {shared.state['strat_id']}")
                robot.is_returning = False
                shared.state["fsm_state"] = "RUNNING" # Update Etat
            else:
                time.sleep(0.1)

        # --- ETAT 2 : MATCH ---
        elif current_state == "RUNNING":
            try:
                # On récupère l'ID (qui est maintenant le nom du fichier, ex: "strat_match_1")
                strat_name = shared.state["strat_id"]
                
                # Import dynamique
                if strat_name in AVAILABLE_STRATS:
                    mod = importlib.import_module(f"strat.strategies.{strat_name}")
                    # Mise à jour du score théorique
                    shared.state["score_current"] = AVAILABLE_STRATS[strat_name].get("score", 0)
                    mod.run(robot)
                else:
                    print(f"[STRAT] Erreur : Stratégie '{strat_name}' inconnu !")
                
                print("[STRAT] Fini.")

            except EndOfMatchException:
                print("[STRAT] ⚠️ TIMEOUT -> RETOUR BASE")
                robot.GoBase()
            except Exception as e:
                print(f"[STRAT] Erreur : {e}")
                robot.stop()
            finally:
                shared.state["fsm_state"] = "FINISHED"

        # --- ETAT 3 : FINI ---
        elif current_state == "FINISHED":
            if not shared.state["match_running"]:
                shared.state["fsm_state"] = "WAIT_START"
            time.sleep(0.5)