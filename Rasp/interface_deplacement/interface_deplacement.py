import serial
import time
import json
import ast
import numpy as np
import threading
import queue
import ihm.shared as shared

# --- CONFIGURATION ---
PORT = '/dev/esp32_motors'
BAUDRATE = 115200

# File d'attente globale pour envoyer des commandes à l'ESP32
_cmd_queue = queue.Queue()
_server_instance = None

def envoyer(message):
    """
    Envoie un message (texte ou trajectoire) à la file d'attente du thread de déplacement.
    Cette fonction est NON-BLOQUANTE pour la stratégie.
    """
    if len(message) == 0:
        return
    
    if isinstance(message, str) and message.startswith("SET POSE"):
        try:
            parts = message.split()
            # On met à jour shared.robot_pos avant même que le message parte !
            shared.robot_pos['y'] = float(parts[2])
            shared.robot_pos['x'] = float(parts[3])
            shared.robot_pos['theta'] = float(parts[4]) * (180.0 / np.pi)
        except Exception as e:
            pass

    if _server_instance:
        if isinstance(message, (list, np.ndarray)):
            # On indique qu'un mouvement va démarrer, on bloque le wait_idle
            print("[DEBUG] CLEARING event for Bezier")
            _server_instance.move_completed_event.clear()
            print(f"[DEBUG] Event is set ? {_server_instance.move_completed_event.is_set()}")
        elif isinstance(message, str) and "STOP" in message:
            print("[DEBUG] SETTING event for STOP")
            _server_instance.move_completed_event.set()

    _cmd_queue.put(message)

def wait_idle(timeout=10.0):
    """
    Bloque la stratégie jusqu'à ce que l'ESP32 signale qu'il a terminé son mouvement,
    ou jusqu'à ce que le timeout soit atteint.
    """
    if _server_instance:
        return _server_instance.wait_for_completion(timeout)
    print("[DEBUG] _server_instance is None in wait_idle!")
    return False

def is_ready():
    """Vérifie si la connexion série est établie et prête."""
    if _server_instance:
        return _server_instance.is_connected
    return False

class DeplacementServer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.ser = None
        self.is_connected = False
        self.running = True
        
        # Un Event pour signaler à la stratégie qu'un mouvement est terminé.
        self.move_completed_event = threading.Event()
        # Par défaut, on considère qu'on est au repos.
        self.move_completed_event.set()

    def wait_for_completion(self, timeout=10.0):
        print(f"[DEBUG] BEFORE wait({timeout}), event is set? {self.move_completed_event.is_set()}")
        # Attend que l'événement soit "set" (signalant la fin d'un mouvement)
        success = self.move_completed_event.wait(timeout)
        print(f"[DEBUG] AFTER wait, success={success}, event is set? {self.move_completed_event.is_set()}")
        return success

    def _connect(self):
        try:
            # 1. On initialise l'objet SANS l'ouvrir immédiatement
            self.ser = serial.Serial()
            self.ser.port = PORT
            self.ser.baudrate = BAUDRATE
            self.ser.timeout = 0.1
            
            # 2. LE BOUCLIER ANTI-RESET 
            self.ser.dtr = False
            self.ser.rts = False
            
            # 3. On ouvre le port en toute sécurité
            self.ser.open()
            self.ser.dtr = False
            self.ser.rts = False
            
            print(f"[COM] Port série {PORT} ouvert avec succès sans Reset.")
            self.is_connected = True
            time.sleep(1.0) # Moins besoin d'attendre si ça ne reboot pas
            return True
        except serial.SerialException as e:
            print(f"[COM] Erreur ouverture port {PORT} : {e}")
            self.is_connected = False
            return False

    def _read_data(self):
        """Lit les données entrantes de l'ESP32 (odométrie, statuts) de manière non bloquante."""
        if not self.ser or not self.is_connected:
            return
            
        try:
            while self.ser.in_waiting > 0:
                line = self.ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                
                # --- FIN EXPLICITE DU TRAJET ---
                if "trajectoryFinished" in line:
                    print("[COM] ESP32 : Fin de trajectoire reçue.")
                    self.move_completed_event.set() # Libère le wait_idle() de la strat
                
                # --- MISE A JOUR POSITION (Odométrie brute de l'ESP32) ---
                elif line.startswith('[') and line.endswith(']'):
                    try:
                        # Exemple reçu de l'ESP32 : [1.8000, 2.7500, -1.5708]
                        msg_list = ast.literal_eval(line)
                        if len(msg_list) >= 3:
                            # Conversion des Mètres/Radians (ESP32) en Millimètres/Degrés (Python)
                            raw_x = msg_list[0] * 1000.0
                            raw_y = msg_list[1] * 1000.0
                            raw_theta = msg_list[2] * 180.0 / np.pi
                            
                            # On sauvegarde la raw_odom pour l'afficher sur le Web (Debug)
                            shared.raw_odom = {'x': raw_x, 'y': raw_y, 'theta': raw_theta}
                            
                            # --- LE BYPASS DE SÉCURITÉ ---
                            # Si le subprocess EKF est "killé" ou désactivé, on injecte
                            # l'odométrie brute directement dans la variable officielle de la stratégie !
                            if getattr(shared, 'ekf_enabled', False) == False:
                                shared.robot_pos['x'] = raw_x
                                shared.robot_pos['y'] = raw_y
                                shared.robot_pos['theta'] = raw_theta
                                
                    except Exception as e:
                        # print(f"[DEBUG] Erreur parsing odométrie brute : {e}")
                        pass
                
                # --- GESTION DES LOGS DE L'ESP32 ---
                elif "BEZ OK" in line:
                    print("[COM] ESP32 a validé la trajectoire Bezier.")
                elif "BEZ ERR" in line:
                    print("[COM] ERREUR : ESP32 a rejeté la trajectoire JSON !")
                elif "TargetIdx" in line or "DESTINATION ATTEINTE" in line:
                    # On affiche les beaux logs de suivi de trajectoire qu'on a codés en C++
                    print(line)
                elif line.startswith("[ESP32]"):
                    # Pour attraper tous les autres logs C++ qui commencent par [ESP32]
                    print(line)
                else:
                    # On ignore silencieusement le reste pour ne pas spammer
                    pass
                    
        except OSError as e:
            print(f"[COM] Déconnexion brutale : {e}")
            self.is_connected = False

    def _process_queue(self):
        """Dépile une commande de la queue et l'envoie à l'ESP32."""
        if not self.is_connected:
            return
            
        try:
            message = _cmd_queue.get_nowait()
        except queue.Empty:
            return

        try:
            # On indique qu'un mouvement est en cours, donc on "clear" le signal de fin.
            # (Sauf si c'est juste un SET POSE ou STOP, mais dans le doute on clear avant chaque grosse cmd)
            
            if isinstance(message, str):
                # TEXTE (ex: SET POSE, STOP)
                if message.startswith("SET POSE"):
                    self.ser.write(b'\n') # Vide le buffer de l'ESP32
                    time.sleep(0.05)

                self.ser.write((message + '\n').encode())
                print(f"[COM->ESP] {message}")
                
                if message.startswith("SET POSE"):
                    # 1. On vide les vieux messages d'odométrie coincés dans le tuyau
                    self.ser.reset_input_buffer()
                    
                    time.sleep(0.2)
                    # 2. On force la mise à jour immédiate de la mémoire interne
                    try:
                        parts = message.split()
                        shared.robot_pos['y'] = float(parts[2])
                        shared.robot_pos['x'] = float(parts[3])
                        shared.robot_pos['theta'] = float(parts[4]) * (180.0 / np.pi)
                    except Exception as e:
                        print(f"[DEBUG] Erreur parsing SET POSE interne : {e}")
                # ------------------------

                if "STOP" in message:
                    self.move_completed_event.set()
                
            elif isinstance(message, np.ndarray) or isinstance(message, list):
                # TRAJECTOIRE DE BEZIER
                # (L'event a déjà été 'clear' dans envoyer() pour bloquer la stratégie instantanément)
                
                trajectoire_bezier_mm = np.array(message)
                nb_points = len(trajectoire_bezier_mm)
                
                # --- CORRECTION DU REPERE ---
                # Le repère de la map Web (X, Y) est transposé par rapport à l'ESP32 (Y, X).
                # SET POSE a bien affecté y_mm à la variable interne X, et x_mm à la variable interne Y.
                # Il faut donc inverser les colonnes de la trajectoire pour que l'ESP32 reçoive [y, x] !
                if trajectoire_bezier_mm.shape[1] >= 2:
                    trajectoire_bezier_mm[:, [0, 1]] = trajectoire_bezier_mm[:, [1, 0]]
                
                # Envoi JSON
                json_str = json.dumps(trajectoire_bezier_mm.tolist())
                self.ser.write((json_str + '\n').encode())
                print(f"[COM->ESP] Trajectoire ({nb_points} pts) envoyée.")
                
            _cmd_queue.task_done()
            
        except Exception as e:
            print(f"[COM] Erreur d'envoi réseau : {e}")
            self.is_connected = False

    def run(self):
        print("[COM] Thread DeplacementServer démarré.")
        while self.running:
            if not self.is_connected:
                # Tente de se connecter en boucle
                if not self._connect():
                    time.sleep(2) # Attend avant de réessayer
                    continue
            
            # 1. Lire ce qui vient de l'ESP32
            self._read_data()
            
            # 2. Envoyer les commandes en attente
            self._process_queue()
            
            # Boucle rapide pour réactivité, mais pas trop pour ne pas griller le CPU
            time.sleep(0.01)
            
        if self.ser and self.ser.is_open:
            self.ser.close()

def init():
    """Initialise et lance le thread de communication en tâche de fond."""
    global _server_instance
    if _server_instance is None:
        _server_instance = DeplacementServer()
        _server_instance.start()
    return _server_instance