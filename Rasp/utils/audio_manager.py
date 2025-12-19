import os
import subprocess
import signal

class AudioManager:
    def __init__(self, cfg_audio: dict):
        self.base_dir = os.path.join(os.path.dirname(__file__), "audio")
        self.current_process = None
        self.load_config(cfg_audio)

    def load_config(self, cfg_audio: dict):
        """Recharge la configuration (volume, pistes)"""
        self.enabled = bool(cfg_audio.get("enabled", True))
        self.tracks = cfg_audio.get("tracks", {})
        self.volume_percent = int(float(cfg_audio.get("volume", 0.8)) * 100)
        
        if self.enabled:
            try:
                subprocess.run(["amixer", "sset", "PCM", f"{self.volume_percent}%"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[AUDIO] Volume réglé à : {self.volume_percent}%")
            except Exception:
                pass

    def play(self, key: str, loop=False):
        if not self.enabled: return

        self.stop() # Coupe le son précédent

        rel_path = self.tracks.get(key)
        if not rel_path: return

        # Gestion chemin absolu ou relatif
        if os.path.isabs(rel_path):
            abs_path = rel_path
        else:
            abs_path = os.path.join(self.base_dir, rel_path)

        if not os.path.exists(abs_path):
            print(f"[AUDIO] Fichier introuvable : {abs_path}")
            return

        cmd = ["mpg123", "-q"]
        if loop:
            cmd.append("--loop")
            cmd.append("-1")
        
        cmd.append(abs_path)

        try:
            self.current_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"[AUDIO] Erreur mpg123 : {e}")

    def stop(self):
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait()
                self.current_process = None
            except Exception:
                pass