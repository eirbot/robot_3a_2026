import os
import pygame # type: ignore
import threading

class AudioManager:
    def __init__(self, cfg_audio: dict):
        self.enabled = bool(cfg_audio.get("enabled", True))
        self.tracks = cfg_audio.get("tracks", {})
        self.volume = float(cfg_audio.get("volume", 0.8))

        # Chemin de base : dossier audio à côté du script
        self.base_dir = os.path.join(os.path.dirname(__file__), "audio")

        if not self.enabled:
            print("[AUDIO] Désactivé dans la config.")
            return

        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            print(f"[AUDIO] Initialisé (volume={self.volume}). Dossier : {self.base_dir}")
        except Exception as e:
            print(f"[AUDIO] Erreur init mixer : {e}")
            self.enabled = False

    def play(self, key: str, loop=False):
        if not self.enabled:
            print("[AUDIO] Ignoré (désactivé ou init échouée).")
            return

        rel_path = self.tracks.get(key)
        if not rel_path:
            print(f"[AUDIO] Aucun fichier défini pour la clé '{key}'")
            return

        # Crée le chemin absolu (toujours basé sur le dossier du script)
        abs_path = rel_path if os.path.isabs(rel_path) else os.path.join(self.base_dir, rel_path)

        if not os.path.exists(abs_path):
            print(f"[AUDIO] Fichier introuvable : {abs_path}")
            return

        threading.Thread(target=self._play, args=(abs_path, loop), daemon=True).start()

    def _play(self, path, loop):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1 if loop else 0)
            print(f"[AUDIO] Lecture : {os.path.basename(path)} (loop={loop})")
        except Exception as e:
            print(f"[AUDIO] Erreur lecture {path} : {e}")

    def stop(self):
        if self.enabled:
            pygame.mixer.music.stop()
            print("[AUDIO] Arrêt de la lecture.")
