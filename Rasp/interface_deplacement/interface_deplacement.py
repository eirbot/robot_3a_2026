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
            self.ser = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=0.1)
            print(f"[COM] Port série {PORT} ouvert avec succès.")
            self.is_connected = True
            # Quand on ouvre l'ESP reboot. On attend 2 secondes.
            print("[COM] Attente du redémarrage de l'ESP32...")
            time.sleep(2.0)
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
                
                # --- MISE A JOUR POSITION (Odométrie) ---
                elif line.startswith('[') and line.endswith(']'):
                    try:
                        msg_list = ast.literal_eval(line)
                        if len(msg_list) >= 3:
                            shared.robot_pos['x'] = msg_list[0] * 1000
                            shared.robot_pos['y'] = msg_list[1] * 1000
                            shared.robot_pos['theta'] = msg_list[2] * 180 / np.pi
                    except:
                        pass
                
                # --- LOGS / DEBUG ESP32 ---
                elif "BEZ OK" in line:
                    print("[COM] ESP32 a validé la trajectoire Bezier.")
                elif "currentIdx" in line:
                    # Ne spamme pas la console, mais on peut le lire
                    pass
                else:
                    # Autres logs venant de l'ESP
                    # print(f"[ESP32] {line}")
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
                self.ser.write((message + '\n').encode())
                print(f"[COM->ESP] {message}")
                # Les commandes simples sont considérées comme instantanées
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
                
                # 1. Envoi de la position actuelle pour recaler l'ESP avant le trajet
                y_mm = shared.robot_pos['y']
                x_mm = shared.robot_pos['x']
                theta_rad = shared.robot_pos['theta'] * (np.pi/180.0)
                cmd_pose = f"SET POSE {y_mm:.2f} {x_mm:.2f} {theta_rad:.4f}\n"
                self.ser.write(cmd_pose.encode())
                
                # Petit délai pour que l'ESP digère le SET POSE avant le JSON
                time.sleep(0.05) 
                
                # 2. Envoi JSON
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