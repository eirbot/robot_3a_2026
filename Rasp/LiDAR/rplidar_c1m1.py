#!/usr/bin/env python3
import serial
import time
import numpy as np

class RPLidarC1M1:
    """
    Driver bas niveau pour le LIDAR RPLiDAR C1M1.
    Responsabilité : Communication série brute et décodage des trames.
    """

    CMD_SCAN = b"\xA5\x20"
    CMD_STOP = b"\xA5\x25"
    DESC_SCAN = bytes.fromhex("A5 5A 05 00 00 40 81")

    def __init__(self, port="/dev/lidar", baud=460800, timeout=0.05):
        """
        :param port: Lien symbolique fixe (ex: /dev/lidar)
        """
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser = None
        self.buf = bytearray()
        self.last_S = 0
        
        self.connect()

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            print(f"[LIDAR] Connecté sur {self.port}")
        except Exception as e:
            print(f"[LIDAR] Erreur de connexion sur {self.port} : {e}")
            self.ser = None

    def close(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(self.CMD_STOP)
                self.ser.flush()
                time.sleep(0.05)
                self.ser.close()
            except Exception:
                pass
        print("[LIDAR] Port fermé.")

    def start_scan(self):
        if not self.ser: return
        
        # Reset propre
        self.ser.write(self.CMD_STOP)
        self.ser.flush()
        time.sleep(0.05)
        self.ser.reset_input_buffer()

        self.ser.write(self.CMD_SCAN)
        self.ser.flush()

        # Lecture descripteur (optionnelle mais recommandée pour vérifier)
        # On lit 7 octets max
        start = time.time()
        desc = bytearray()
        while len(desc) < 7 and time.time() - start < 1.0:
            desc.extend(self.ser.read(7 - len(desc)))
        
        if desc != self.DESC_SCAN:
            print(f"[LIDAR] WARN: Descripteur inattendu ({desc.hex()})")
        
        self.buf.clear()
        self.last_S = 0

    def clean_input(self):
        if self.ser:
            self.ser.reset_input_buffer()
        self.buf.clear()
        self.last_S = 0

    def _decode_sample(self, b):
        if len(b) != 5: return None
        b0, b1, b2, b3, b4 = b

        S = b0 & 0x01
        S_bar = (b0 >> 1) & 0x01
        C = b1 & 0x01

        if (S ^ S_bar) != 1 or C != 1:
            return None

        qual = (b0 >> 2) & 0x3F
        angle_q6 = (b2 << 7) | (b1 >> 1)
        dist_q2 = (b4 << 8) | b3
        
        return (angle_q6 / 64.0) % 360.0, dist_q2 / 4.0, qual, S

    def get_scan(self, min_dist=50, max_dist=6000):
        """
        Récupère un tour complet (révolution).
        Retourne np.array([[angle, dist, qual], ...]) ou None.
        """
        if not self.ser: return None
        
        revolution = []
        loops = 0
        max_loops = 20000 

        while loops < max_loops:
            loops += 1
            if self.ser.in_waiting:
                self.buf.extend(self.ser.read(self.ser.in_waiting))
            
            # Attente si buffer vide
            if len(self.buf) < 5:
                chunk = self.ser.read(32)
                if chunk: self.buf.extend(chunk)
                else: continue

            # Recherche header 0xA5
            if self.buf[0] != 0xA5:
                try:
                    idx = self.buf.index(0xA5)
                    del self.buf[:idx]
                except ValueError:
                    self.buf.clear()
                    continue

            if len(self.buf) < 5: continue

            # Décodage
            decoded = self._decode_sample(self.buf[:5])
            if not decoded:
                del self.buf[0] # Faux positif
                continue
            
            del self.buf[:5]
            angle, dist, qual, S = decoded

            # Gestion tour complet
            if S == 1 and self.last_S == 0:
                self.last_S = S
                if len(revolution) > 50:
                    return np.array(revolution)
                else:
                    revolution = [] # Tour incomplet
            
            self.last_S = S

            if min_dist < dist < max_dist:
                revolution.append((angle, dist, qual))
        
        return None