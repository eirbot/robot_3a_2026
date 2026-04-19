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
from interface_deplacement.interface_deplacement import init as init_motors

# Import des logiques
from hardware_thread import hardware_loop

# --- MAIN ---
if __name__ == "__main__":
    print("--- ROBOT 2026 : Démarrage ---")
    
    # Détection de l'environnement plus robuste
    import platform
    machine = platform.machine().lower()
    is_pi = "arm" in machine or "aarch64" in machine
    
    # Double check : certains PC linux ont /sys/class/gpio mais ne sont pas des Pi
    if is_pi and not os.path.exists('/proc/device-tree/model'):
        is_pi = False
        
    print(f"[MAIN] Environnement : {'Raspberry Pi (' + machine + ')' if is_pi else 'PC/Simulation (' + machine + ')'}")

    if is_pi:
        try:
            init_motors()
        except Exception as e:
            print(f"[MAIN] Erreur initialisation moteurs : {e}")
    else:
        print("[MAIN] Mode simulation : Moteurs ignorés.")
    
    led_process = None
    try:
        # 0. Start LED Service (Subprocess) - Uniquement sur Pi
        if is_pi:
            led_script = os.path.join(os.path.dirname(__file__), 'utils', 'led_service.py')
            if os.path.exists(led_script):
                print(f"[MAIN] Lancement du service LED : {led_script}")
                led_process = subprocess.Popen([sys.executable, led_script])
        else:
            print("[MAIN] Mode simulation : Service LED ignoré.")

        # 1. Thread HARDWARE (Lidar, EKF)
        if is_pi:
            hw_thread = threading.Thread(target=hardware_loop, daemon=True)
            hw_thread.start()
        else:
            print("[MAIN] Mode simulation : Thread Hardware ignoré.")

        # 2. Thread STRATEGIE (IA, Décisions)
        strat_thread = threading.Thread(target=strat_loop, daemon=True)
        strat_thread.start()
        
        # 3. Thread IHM (Serveur Web)
        ihm_thread = threading.Thread(target=run_ihm, daemon=True)
        ihm_thread.start()

        # 3.5 Thread BOUTONS (GPIO) - Uniquement sur Pi
        if is_pi:
            try:
                from buttons_thread import run_buttons_loop
                btn_thread = threading.Thread(target=run_buttons_loop, daemon=True)
                btn_thread.start()
            except ImportError:
                print("[MAIN] RPi.GPIO non disponible.")
        
        # 3.6 Thread TIMER (Décompte + Sync IHM)
        from timer_thread import start_timer_thread
        start_timer_thread()
        
        time.sleep(1)

        # 4. Interface Graphique
        print(f"[MAIN] Interface disponible sur http://localhost:5000")
        
        if is_pi:
            try:
                webview.create_window('Robot 2026', 'http://127.0.0.1:5000', fullscreen=True)
                webview.start()
            except Exception as e:
                print(f"[MAIN] Impossible de lancer webview : {e}")
                while True: time.sleep(1)
        else:
            print("[MAIN] Mode simulation : Utilisez votre navigateur sur http://localhost:5000")
            print("[MAIN] Appuyez sur Ctrl+C pour arrêter.")
            try:
                # Tentative optionnelle sur PC
                # webview.create_window('Robot 2026 - SIMU', 'http://127.0.0.1:5000', width=800, height=480)
                # webview.start()
                while True: time.sleep(1)
            except (KeyboardInterrupt, Exception):
                pass
        
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