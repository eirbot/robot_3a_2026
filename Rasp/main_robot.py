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

# Fonction pour vérifier si le serveur est prêt
def wait_for_server(window):
    print("En attente du serveur web...", flush=True)
    max_retries = 20
    for i in range(max_retries):
        try:
            # On tente de se connecter au serveur (changez le port 5000 si besoin)
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:5000")
            
            # Si ça marche, on charge la vraie page !
            print("Serveur prêt ! Chargement de l'interface...", flush=True)
            window.load_url("http://127.0.0.1:5000")
            return
        except:
            # Si ça rate, on attend 1 seconde
            time.sleep(1)
    
    print("Erreur : Le serveur n'a pas démarré à temps.", flush=True)

# --- MAIN ---
if __name__ == "__main__":
    print("--- ROBOT 2026 : Démarrage ---")
    
    init_motors()
    
    try:
        # 1. Thread HARDWARE (Lidar, EKF)
        # hw_thread = threading.Thread(target=hardware_loop, daemon=True)
        # hw_thread.start()

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
        window = webview.create_window('Eirbot 2026', html='<h1>Démarrage du robot en cours...</h1>')
        webview.start(func=wait_for_server, args=(window,))
        
    except KeyboardInterrupt:
        print("\n[MAIN] Arrêt demandé.")
        sys.exit(0)