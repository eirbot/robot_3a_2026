#!/usr/bin/env python3
import sys
import os
import time
import threading
import subprocess
import webview

# Import de l'IHM
from ihm import run_ihm
import ihm.shared as shared
from strat.main_strat import strat_loop

# Import des communications avec les moteurs
# from interface_deplacement.interface_deplacement import init as init_motors

# Import des logiques
from hardware_thread import hardware_loop

# --- MAIN ---
if __name__ == "__main__":
    print("--- ROBOT 2026 : Démarrage ---")
    
    # init_motors()
    
    led_process = None
    try:
        # 0. Start LED Service (Subprocess)
        led_script = os.path.join(os.path.dirname(__file__), 'utils', 'led_service.py')
        if os.path.exists(led_script):
            print(f"[MAIN] Lancement du service LED : {led_script}")
            led_process = subprocess.Popen([sys.executable, led_script])
        else:
            print(f"[MAIN] ERREUR: led_service.py introuvable à {led_script}")

        # 1. Thread HARDWARE (Lidar, EKF)
        hw_thread = threading.Thread(target=hardware_loop, daemon=True)
        hw_thread.start()

        # 2. Thread STRATEGIE (IA, Décisions)
        strat_thread = threading.Thread(target=strat_loop, daemon=True)
        strat_thread.start()
        
        # 3. Thread IHM (Serveur Web)
        ihm_thread = threading.Thread(target=run_ihm, daemon=True)
        ihm_thread.start()

        # 3.5 Thread BOUTONS (GPIO)
        from buttons_thread import run_buttons_loop
        btn_thread = threading.Thread(target=run_buttons_loop, daemon=True)
        btn_thread.start()

        # 3.6 Thread TIMER (Décompte + Sync IHM)
        from timer_thread import start_timer_thread
        start_timer_thread()
        
        # Petit délai pour laisser le temps à Flask/SocketIO de démarrer
        time.sleep(2)

        # --- UPDATE LED INITIALE (Couleur Equipe) ---
        # Ne pas écraser si on a une alerte tirette en cours
        if shared.state.get('tirette_msg') != "REMOVE_TO_RESET":
            print(f"[MAIN] Application de la couleur d'équipe : {shared.state['team']}")
            if shared.state['team'] == 'JAUNE':
                 shared.send_led_cmd("COLOR:255,160,0") # Jaune
            else:
                 shared.send_led_cmd("COLOR:0,0,255") # Bleue
        else:
             print("[MAIN] Alerte Tirette active, on ne force pas la couleur d'équipe.")
             # On renvoie la commande car le service LED n'était peut-être pas prêt lors du thread boutons
             shared.send_led_cmd("ANIM:BLINK:255,100,0,350")

        # 4. Interface Graphique (Bloquant le Main) 
        # On lance la fenêtre qui affiche le site local
        # fullscreen=True est recommandé pour l'écran 7" du robot
        print("[MAIN] Lancement de l'affichage local...")
        webview.create_window('Robot 2026', 'http://127.0.0.1:5000', fullscreen=True)
        webview.start()
        
    except KeyboardInterrupt:
        print("\n[MAIN] Arrêt demandé.")
    except Exception as e:
        print(f"\n[MAIN] Erreur critique : {e}")
    finally:
        if led_process:
            print("[MAIN] Arrêt du service LED...")
            led_process.terminate()
            try:
                led_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                led_process.kill()
        
        sys.exit(0)