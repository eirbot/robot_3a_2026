import sys
import time
import multiprocessing
import os
import logging

# On ajoute les chemins de tes dossiers pour que Python trouve tes fichiers
sys.path.append(os.path.join(os.path.dirname(__file__), 'ihm'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'LiDAR'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'interface_deplacement'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'strat'))

# --- PROCESSUS 1 : HARDWARE (Critique) ---
# Gère : Lidar, EKF, Communication ESP32
def process_hardware(queue_pose_out, queue_cmd_in):
    print("[HARDWARE] Démarrage...")
    
    # Import ici pour éviter de charger ça dans les autres processus
    try:
        from ekf_localizer import EKFLocalizer
        # from ClassDialogue import ... (si besoin pour parler à l'ESP32)
    except ImportError as e:
        print(f"[HARDWARE] Erreur import: {e}")
        return

    # Initialisation EKF & Lidar
    try:
        ekf = EKFLocalizer("/dev/ttyUSB0") 
        ekf.start_scan()
        print("[HARDWARE] Lidar & EKF prêts.")
    except Exception as e:
        print(f"[HARDWARE] Erreur init matériel : {e}")
        # On continue quand même pour tester le reste (mode simu)
        ekf = None

    last_time = time.time()

    while True:
        # 1. Gestion du temps (dt)
        now = time.time()
        dt = now - last_time
        last_time = now

        # 2. Lire les ordres de la Stratégie (ex: "Reset EKF")
        if not queue_cmd_in.empty():
            cmd = queue_cmd_in.get()
            print(f"[HARDWARE] Reçu commande : {cmd}")
            # Traiter la commande ici...

        # 3. Mettre à jour la position (EKF)
        if ekf:
            try:
                # Etape CRUCIALE : vider le buffer avant de lire pour être "temps réel"
                ekf.clean_input() 
                
                # Prédiction (Odométrie) - Ici on met 0,0 mais il faudra lire l'ESP32
                ekf.predict(dt=dt, v=0.0, w=0.0) 
                
                # Correction (Lidar)
                pose, nb_balises, _ = ekf.locate_once()
                
                if pose:
                    # On envoie la position à la Stratégie et à l'IHM
                    # On vide la queue si elle est pleine pour toujours avoir la dernière info
                    if queue_pose_out.full():
                        try: queue_pose_out.get_nowait()
                        except: pass
                    queue_pose_out.put(pose)
                    
            except Exception as e:
                print(f"[HARDWARE] Erreur boucle EKF : {e}")
        
        # Petite pause pour ne pas manger 100% CPU si le Lidar n'est pas là
        time.sleep(0.01)


# --- PROCESSUS 2 : STRATÉGIE (Intelligence) ---
# Gère : Machine à état, A*, Décisions
def process_strategy(queue_pose_in, queue_ui_out):
    print("[STRAT] Démarrage...")
    
    current_pose = (0,0,0)
    score = 0
    state = "WAIT_START" # Machine à état simple

    while True:
        # 1. Mettre à jour ma connaissance du monde
        if not queue_pose_in.empty():
            current_pose = queue_pose_in.get()
        
        # 2. Réfléchir (Machine à états)
        if state == "WAIT_START":
            # On attend... (simulation)
            if time.time() % 5 < 0.1: # Juste pour tester
               # On envoie un score bidon à l'IHM pour voir si ça marche
               score += 1
               if not queue_ui_out.full():
                   queue_ui_out.put({"type": "score", "value": score})
        
        elif state == "GAME":
            # Calcul A*, évitement, etc.
            pass

        time.sleep(0.1) # La stratégie peut tourner moins vite (10Hz)


# --- PROCESSUS 3 : IHM (Interface) ---
# Gère : Tkinter, Audio, LEDs
def process_ui(queue_ui_in):
    print("[UI] Démarrage...")
    
    # Imports IHM (seulement ici car Tkinter n'aime pas le multiprocessing)
    import tkinter as tk
    import json
    from ui_manager import UIManager
    from leds_manager import LedStrip
    from audio_manager import AudioManager
    # On importe ton lien stratégie existant pour injecter les données
    import strategy_link 

    # Charger config
    config_path = os.path.join(os.path.dirname(__file__), "ihm/config.json")
    with open(config_path) as f:
        cfg = json.load(f)

    leds = LedStrip(**cfg.get("leds", {}))
    audio = AudioManager(cfg.get("audio", {}))
    
    root = tk.Tk()
    ui = UIManager(root, leds, audio, cfg)

    # Fonction locale pour vérifier la queue et mettre à jour l'interface
    def check_queue():
        try:
            while not queue_ui_in.empty():
                msg = queue_ui_in.get_nowait()
                # On utilise tes fonctions existantes dans strategy_link
                if msg['type'] == 'score':
                    # Met à jour la variable globale que l'UI surveille
                    strategy_link.update_score(msg['value'])
                elif msg['type'] == 'error':
                    strategy_link.set_error(msg['value'])
        except Exception:
            pass
        # Se rappelle elle-même toutes les 100ms
        root.after(100, check_queue)

    # Lancer la surveillance de la queue
    check_queue()
    
    # Lancer la boucle principale Tkinter
    root.mainloop()


# --- LE MAIN GLOBAL ---
if __name__ == "__main__":
    # Configuration indispensable pour que Tkinter et le Hardware fassent bon ménage
    multiprocessing.set_start_method('spawn')

    # Création des canaux de communication (Queues)
    q_pose = multiprocessing.Queue(maxsize=1)  # Hardware -> Strat
    q_cmd = multiprocessing.Queue(maxsize=5)   # Strat -> Hardware
    q_ui = multiprocessing.Queue(maxsize=10)   # Strat -> IHM

    # Création des Processus
    p_hard = multiprocessing.Process(target=process_hardware, args=(q_pose, q_cmd))
    p_strat = multiprocessing.Process(target=process_strategy, args=(q_pose, q_ui))
    p_ui = multiprocessing.Process(target=process_ui, args=(q_ui,))

    print("--- LANCEMENT DU ROBOT 3A ---")
    
    p_hard.start()
    p_strat.start()
    p_ui.start()

    # Le script principal attend que l'IHM se ferme pour tout arrêter
    try:
        p_ui.join()
    except KeyboardInterrupt:
        print("Arrêt demandé...")

    # Nettoyage brutal mais efficace
    p_hard.terminate()
    p_strat.terminate()
    p_ui.terminate()
    
    print("--- ROBOT ÉTEINT ---")