#!/usr/bin/env python3
import sys
import os
import time
import threading

# Import de l'IHM
from ihm import run_ihm
import shared as shared
from main_strat import strat_loop

# Import des logiques
from hardware_thread import hardware_loop

# --- MAIN ---
if __name__ == "__main__":
    print("--- ROBOT 2026 : Démarrage ---")
    
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