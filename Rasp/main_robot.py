#!/usr/bin/env python3
import sys
import os
import time
import threading

# Import de l'IHM
from ihm import run_ihm
import ihm.shared as shared

# Import des logiques
from hardware_thread import hardware_loop  # <--- LE NOUVEAU
# (Tu peux aussi mettre ta strategy_loop dans un fichier strategy_thread.py pour faire propre)

# --- STRATEGIE (Simplifiée pour l'exemple) ---
def strategy_loop():
    print("[STRAT] Démarrage logique...")
    while True:
        # La stratégie lit simplement la position mise à jour par le Hardware !
        x = shared.robot_pos['x']
        y = shared.robot_pos['y']
        
        if shared.state["match_running"]:
            # Logique de match...
            pass
            
        time.sleep(0.1)

# --- MAIN ---
if __name__ == "__main__":
    print("--- ROBOT 2026 : Démarrage ---")
    
    try:
        # 1. Thread HARDWARE (Lidar, EKF)
        hw_thread = threading.Thread(target=hardware_loop, daemon=True)
        hw_thread.start()

        # 2. Thread STRATEGIE (IA, Décisions)
        strat_thread = threading.Thread(target=strategy_loop, daemon=True)
        strat_thread.start()
        
        # 3. Thread IHM (Serveur Web - Bloquant)
        run_ihm()
        
    except KeyboardInterrupt:
        print("\n[MAIN] Arrêt demandé.")
        sys.exit(0)