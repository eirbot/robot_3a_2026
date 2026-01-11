#!/usr/bin/env python3
import sys
import os
import time
import threading
import webview

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
        
        # 3. Thread IHM (Serveur Web)
        ihm_thread = threading.Thread(target=run_ihm, daemon=True)
        ihm_thread.start()
        
        # Petit délai pour laisser le temps à Flask/SocketIO de démarrer
        time.sleep(2)

        # 4. Interface Graphique (Bloquant le Main) 
        # On lance la fenêtre qui affiche le site local
        # fullscreen=True est recommandé pour l'écran 7" du robot
        print("[MAIN] Lancement de l'affichage local...")
        webview.create_window('Robot 2026', 'http://127.0.0.1:5000', fullscreen=True)
        webview.start()
        
    except KeyboardInterrupt:
        print("\n[MAIN] Arrêt demandé.")
        sys.exit(0)