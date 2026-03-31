import serial

class InterfaceActionneur:
    """
    Gestion des actionneurs locaux via le port série de l'ESP32.
    """
    def __init__(self, port='/dev/espactionneur', baudrate=115200):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
            self.connected = True
            print("[ACTIONNEURS] Connexion ESP réussie.")
        except Exception as e:
            print(f"⚠️ Attention : Port série actionneurs introuvable ({e}) -> Mode simulation actionneurs")
            self.connected = False
            self.ser = None

    def send_cmd(self, act1=None, act2=None, act3=None, act4=None):
        """
        Envoie les instructions via les mots-clés (FLIP, nFLIP, DOWN, INIT, RESET)
        """
        cmds = []
        if act1: cmds.append(f"act1 {act1}")
        if act2: cmds.append(f"act2 {act2}")
        if act3: cmds.append(f"act3 {act3}")
        if act4: cmds.append(f"act4 {act4}")
        
        if not cmds:
            return
            
        full_cmd = " ".join(cmds) + "\n"
        print(f"[ACTIONNEURS] Envoi: {full_cmd.strip()}")
        
        if self.connected and self.ser:
            try:
                self.ser.write(full_cmd.encode('ascii'))
            except Exception as e:
                print(f"[ERREUR] Envoi série actionneurs : {e}")

    def send_raw(self, command_string):
        """
        Envoie une ligne de commande brute (utile pour Blockly)
        """
        if not command_string: return
        full_cmd = command_string.strip() + "\n"
        print(f"[ACTIONNEURS] Envoi brute: {full_cmd.strip()}")
        
        if self.connected and self.ser:
            try:
                self.ser.write(full_cmd.encode('ascii'))
            except Exception as e:
                print(f"[ERREUR] Envoi série actionneurs : {e}")
