import pygame, threading

class AudioManager:
    def __init__(self, cfg_audio: dict):
        self.enabled = bool(cfg_audio.get("enabled", True))
        self.tracks = cfg_audio.get("tracks", {})
        self.volume = float(cfg_audio.get("volume", 0.8))
        if self.enabled:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)

    def play(self, key: str, loop=False):
        if not self.enabled: return
        path = self.tracks.get(key)
        if not path: return
        threading.Thread(target=self._play, args=(path, loop), daemon=True).start()

    def _play(self, path, loop):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1 if loop else 0)

    def stop(self):
        if self.enabled: pygame.mixer.music.stop()