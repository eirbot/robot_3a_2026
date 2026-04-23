import socket

# C'est l'adresse où le service écoute
SOCKET_PATH = "/tmp/ledsock"

class LedStrip:
    def __init__(self, enabled=True, **kwargs):
        self.enabled = enabled

    def _send(self, cmd):
        """Envoie une commande texte au service LED via socket"""
        if not self.enabled:
            return
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.sendto(cmd.encode('utf-8'), SOCKET_PATH)
            sock.close()
        except Exception as e:
            # On ne veut pas faire planter le robot si les LEDs déconnent
            print(f"[LEDS] Erreur d'envoi : {e}")

    def set_team(self, team_name):
        """Définit la couleur selon l'équipe (BLEUE/JAUNE)"""
        self._send(f"TEAM:{team_name}")

    def match_start(self):
        """Animation de début de match"""
        self._send("MATCH_START")

    def match_stop(self):
        """Animation de fin de match"""
        self._send("MATCH_STOP")

    def off(self):
        """Éteint tout"""
        self._send("OFF")
        
    def set_color(self, r, g, b):
        """Force une couleur spécifique"""
        self._send(f"COLOR:{r},{g},{b}")