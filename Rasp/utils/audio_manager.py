import os
import subprocess
import signal

class AudioManager:
    def __init__(self, cfg_audio: dict):
        # --- CORRECTION CHEMIN AUDIO ---
        # On remonte d'un dossier (..) pour aller chercher dans 'ihm/audio'
        # utils/../ihm/audio
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ihm/audio"))
        # -------------------------------
        
        self.current_process = None
        self.load_config(cfg_audio)

    def load_config(self, cfg_audio: dict):
        """Recharge la configuration (volume, pistes)"""
        self.enabled = bool(cfg_audio.get("enabled", True))
        self.tracks = cfg_audio.get("tracks", {})
        
        # Sécurité pour éviter erreur si "volume" est manquant ou mal formaté
        try:
            vol = float(cfg_audio.get("volume", 0.8))
        except: 
            vol = 0.8
        self.volume_percent = int(vol * 100)
        
        if self.enabled:
            try:
                # Commande pour régler le volume système (Alsa)
                subprocess.run(["amixer", "sset", "PCM", f"{self.volume_percent}%"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # print(f"[AUDIO] Volume réglé à : {self.volume_percent}%")
            except Exception:
                pass

    def play(self, key_or_file: str, loop=False):
        if not self.enabled: return

        self.stop() # Coupe le son précédent

        # --- CORRECTION LOGIQUE ---
        # 1. On regarde si c'est une CLÉ connue (ex: "intro")
        if key_or_file in self.tracks:
            rel_path = self.tracks[key_or_file]
        else:
            # 2. Sinon, on suppose que c'est directement un NOM DE FICHIER (ex: "musique.mp3")
            rel_path = key_or_file
        # --------------------------

        # Gestion chemin absolu ou relatif
        if os.path.isabs(rel_path):
            abs_path = rel_path
        else:
            abs_path = os.path.join(self.base_dir, rel_path)

        if not os.path.exists(abs_path):
            print(f"[AUDIO] Fichier introuvable : {abs_path}")
            return

        print(f"[AUDIO] Lecture : {abs_path}") # Debug

        cmd = ["mpg123", "-q"]
        if loop:
            cmd.append("--loop")
            cmd.append("-1")
        
        cmd.append(abs_path)

        try:
            # On laisse stderr ouvert pour voir si mpg123 râle dans la console
            self.current_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL
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