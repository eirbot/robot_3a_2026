import serial
import threading
import time
import ihm.shared as shared  # On importe ton shared pour y stocker X, Y, Theta

class ESPActionneurs:
    def __init__(self, port='/dev/esp_action', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
        # Le Lock permet d'éviter que 2 threads parlent à l'ESP en même temps
        self.tx_lock = threading.Lock() 
        self.running = False
        self.rx_thread = None
        self.cmd_done_event = threading.Event()
        self.cmd_aborted = False

    def start(self):
        """Initialise la connexion et lance le thread d'écoute."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            # Désactive DTR et RTS pour éviter que l'ESP32 ne reste bloqué en mode Reset ou Bootloader
            self.ser.setDTR(False)
            self.ser.setRTS(False)
            self.ser.reset_input_buffer()
            print(f"[ACTIONNEURS] ✅ Connexion établie sur {self.port}")
            
            # Lancement du Thread de réception
            self.running = True
            self.rx_thread = threading.Thread(target=self._receive_loop, daemon=True, name="ESP_Rx_Thread")
            self.rx_thread.start()
            
        except serial.SerialException as e:
            print(f"[ACTIONNEURS] ❌ Erreur critique : Impossible d'ouvrir {self.port} -> {e}")

    def stop(self):
        """Arrête proprement le thread et ferme le port."""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send(self, cmd):
        """Envoie une commande à l'ESP de manière Thread-Safe."""
        if not self.ser or not self.ser.is_open:
            return
        
        # On s'assure qu'un seul thread peut écrire sur le port série à la fois
        with self.tx_lock:
            try:
                msg = f"{cmd}\n"
                self.ser.write(msg.encode('utf-8'))
                # print(f"[ACTIONNEURS] -> {cmd}") # Décommenter pour le debug
            except Exception as e:
                print(f"[ACTIONNEURS] ❌ Erreur d'envoi : {e}")

    def init_robot(self):
        self.send("I")
        # Attend que l'ESP ait fini et que le flag soit levé
        self.cmd_done_event.wait(timeout=5.0)
        if not self.cmd_done_event.is_set():
             print("[ACTIONNEURS] ❌ Timeout - L'ESP n'a pas répondu à temps.")
             return False

        # On reset le flag pour la prochaine commande
        self.cmd_done_event.clear()
        return True

    # --- Tâche de fond (Thread) ---
    
    def _receive_loop(self):
        """Boucle tournant en arrière-plan pour traiter les retours de l'ESP."""
        print("[ACTIONNEURS] 🎧 Thread d'écoute démarré.")
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    ligne = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if ligne:
                        self._process_message(ligne)
            except Exception as e:
                print(f"[ACTIONNEURS] Exception in rx loop: {e}")
                # Évite que le thread ne crash silencieusement en cas de bruit série
                pass 
                
            time.sleep(0.005) # Petite pause pour ne pas manger 100% du CPU

    def _process_message(self, msg):
        """Déchiffre le message et met à jour l'état partagé du robot."""
        print(f"[ACTIONNEURS] <- {msg}") # Décommenter pour le debug
        if msg == "D":
            self.cmd_done_event.set()
        elif msg == "E":
            self.cmd_done_event.set()
            self.cmd_aborted = True
            print("[ACTIONNEURS] ❌ Erreur d'init")
        pass