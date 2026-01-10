#!/usr/bin/env python3
import sys
import os
import time
import threading

# Import de l'IHM
from ihm import run_ihm
import ihm.shared as shared
from strat.main_strat import strat_loop

# Import des communications avec les moteurs
from interface_deplacement.interface_deplacement import init as init_motors

# Import des logiques
from hardware_thread import hardware_loop

# --- MAIN ---
if __name__ == "__main__":
    print("--- ROBOT 2026 : Démarrage ---")
    
    init_motors()
    
    try:
        # 1. Thread HARDWARE (Lidar, EKF)
        hw_thread = threading.Thread(target=hardware_loop, daemon=True)
        hw_thread.start()

        # 2. Thread STRATEGIE (IA, Décisions)
        strat_thread = threading.Thread(target=strat_loop, daemon=True)
        strat_thread.start()
        
        # 3. Thread IHM (Serveur Web - Bloquant)
        run_ihm()
        
    except KeyboardInterrupt:
        print("\n[MAIN] Arrêt demandé.")
        sys.exit(0)