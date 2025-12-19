# camera.py
import cv2
import time
from threading import Thread

class ThreadedCamera:
    def __init__(self, src=0, width=320, height=240, fps=15):
        self.src = src
        # Configuration V4L2 + MJPEG
        self.capture = cv2.VideoCapture(src, cv2.CAP_V4L2)
        
        # Configuration optimisée
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, fps)
        
        self.status = False
        self.frame = None
        self.stopped = False

        # Lecture de la première image pour vérifier
        if self.capture.isOpened():
            self.status, self.frame = self.capture.read()
            print(f"[CAMERA] Démarrée sur ID {src} ({width}x{height} @ {fps}fps)")
        else:
            print("[ERREUR CAMÉRA] Impossible d'ouvrir le périphérique vidéo.")
            self.status = False

    def start(self):
        if self.status:
            Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if self.capture.isOpened():
                (status, frame) = self.capture.read()
                if status:
                    self.status = status
                    self.frame = frame
                else:
                    # Si on perd la cam, on attend un peu pour éviter de spammer le CPU
                    time.sleep(0.1)
            else:
                time.sleep(0.5)

    def read(self):
        # Retourne la dernière image disponible
        return self.status, self.frame

    def stop(self):
        self.stopped = True
        if self.capture.isOpened():
            self.capture.release()