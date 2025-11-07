import socket, threading, time

SOCK_PATH = "/tmp/ledsock"
TEAM_COLORS = {"BLEUE": (0, 80, 255), "JAUNE": (255, 160, 0)}
WHITE, RED, PURPLE = (255,255,255), (255,0,0), (120,0,160)

class LedStrip:
    def __init__(self, enabled=True, **_):
        self.enabled = enabled
        self._base_color = TEAM_COLORS["BLEUE"]
        self._stop = threading.Event()
        self._thread = None
        print("[LED] Client prêt, socket:", SOCK_PATH)

    def _send(self, msg):
        if not self.enabled: return
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.sendto(msg.encode(), SOCK_PATH)
            sock.close()
        except Exception as e:
            print(f"[LED] Erreur envoi: {e}")

    def off(self): self._send("off")
    def set_team(self, team):
        self._base_color = TEAM_COLORS.get(team.upper(), TEAM_COLORS["BLEUE"])
        self._send(f"team {team}")
    def set_debug(self, on): self._send("purple" if on else f"team BLEUE")
    def set_error(self, on): self._send("blink_red" if on else f"team BLEUE")
    def match_start(self): self._send("breathe")
    def match_stop(self): self._send("blink_white")
