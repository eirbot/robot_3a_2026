import time
from threading import Thread

# Import sécurisé de la librairie
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

class LibCamera:
    def __init__(self, resolution=(320, 240), framerate=20):
        # Initialisation des variables par défaut pour éviter les crashs
        self.status = False
        self.frame = None
        self.running = False
        self.picam2 = None
        self.thread = None

        if Picamera2 is None:
            print("[ERREUR CAM] Librairie 'picamera2' manquante (sudo apt install python3-picamera2).")
            return

        try:
            print(f"[CAM] Init Picamera2 {resolution} @ {framerate}fps...")
            self.picam2 = Picamera2()
            
            # --- CORRECTION MAJEURE ICI ---
            # On utilise 'create_video_configuration' au lieu de 'create_configuration'
            config = self.picam2.create_video_configuration(
                main={"size": resolution, "format": "BGR888"}
            )
            self.picam2.configure(config)
            
            # Démarrage de la caméra
            self.picam2.start()
            
            # Réglage du framerate (via FrameDurationLimits en microsecondes)
            try:
                if framerate > 0:
                    duration_us = int(1000000 / framerate)
                    # On fixe min et max à la même valeur pour forcer le FPS
                    self.picam2.set_controls({"FrameDurationLimits": (duration_us, duration_us)})
            except Exception as e:
                print(f"[CAM Warning] Impossible de forcer le framerate : {e}")

            self.running = True
            print("[CAM] Hardware démarré avec succès !")
            
        except Exception as e:
            print(f"\n[ERREUR CRITIQUE CAM] Impossible de démarrer : {e}")
            # On nettoie si l'init a échoué à moitié
            if self.picam2:
                self.picam2.stop()
                self.picam2.close()
            self.picam2 = None
            self.running = False

    def start(self):
        # On ne lance le thread que si le hardware est prêt
        if self.running and self.picam2:
            self.thread = Thread(target=self.update, args=(), daemon=True)
            self.thread.start()
        return self

    def update(self):
        while self.running and self.picam2:
            try:
                # Capture_array retourne l'image directement en format NumPy (BGR)
                frame = self.picam2.capture_array("main")
                if frame is not None:
                    self.frame = frame
                    self.status = True
                else:
                    self.status = False
            except Exception as e:
                print(f"[CAM Warning] Erreur capture : {e}")
                self.status = False
                time.sleep(0.1)

    def read(self):
        # Cette fonction est safe : elle renvoie False/None si ça ne marche pas
        return self.status, self.frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
            except: pass
        self.picam2 = None