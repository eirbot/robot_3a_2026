import os
import subprocess
import signal

class AudioManager:
    def __init__(self, cfg_audio: dict):
        self.enabled = bool(cfg_audio.get("enabled", True))
        self.tracks = cfg_audio.get("tracks", {})
        # mpg123 gère le volume via l'échelle système ou gain, 
        # mais ici on va gérer le volume système via amixer pour être sûr.
        self.volume_percent = int(float(cfg_audio.get("volume", 0.8)) * 100)
        self.base_dir = os.path.join(os.path.dirname(__file__), "audio")
        self.current_process = None

        if self.enabled:
            # On règle le volume global du RPi (PCM) une bonne fois pour toutes
            try:
                subprocess.run(["amixer", "sset", "PCM", f"{self.volume_percent}%"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[AUDIO] Mode léger (mpg123). Volume système : {self.volume_percent}%")
            except Exception:
                print("[AUDIO] Attention: Impossible de régler le volume via amixer.")

    def play(self, key: str, loop=False):
        if not self.enabled: return

        # Si un son joue déjà, on le coupe (ou on peut le laisser si tu veux du mixage, 
        # mais mpg123 ne mixe pas nativement, il faut lancer plusieurs process)
        self.stop()

        rel_path = self.tracks.get(key)
        if not rel_path: return

        abs_path = rel_path if os.path.isabs(rel_path) else os.path.join(self.base_dir, rel_path)

        if not os.path.exists(abs_path):
            print(f"[AUDIO] Fichier introuvable : {abs_path}")
            return

        cmd = ["mpg123", "-q"] # -q pour quiet (pas de logs dans la console)
        if loop:
            cmd.append("--loop")
            cmd.append("-1") # Loop infini
        
        cmd.append(abs_path)

        try:
            # Popen lance le processus et rend la main IMMÉDIATEMENT à Python.
            # Ton EKF continue de tourner sans savoir que la musique joue.
            self.current_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"[AUDIO] Erreur lancement mpg123 : {e}")

    def stop(self):
        if self.current_process:
            try:
                # On tue le processus mpg123 proprement
                self.current_process.terminate()
                self.current_process.wait() # On attend qu'il soit bien mort pour éviter les zombies
                self.current_process = None
            except Exception:
                pass