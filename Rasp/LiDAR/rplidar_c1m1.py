#!/usr/bin/env python3
import serial, time
import numpy as np

class RPLidarC1M1:
    """Gestion bas-niveau du LIDAR RPLiDAR C1M1 (mode standard 0x20)."""

    CMD_SCAN = b"\xA5\x20"
    CMD_STOP = b"\xA5\x25"
    DESC_SCAN = bytes.fromhex("A5 5A 05 00 00 40 81")

    def __init__(self, port="/dev/ttyUSB0", baud=460800, timeout=0.05):
        """
        Initialise la communication avec le LIDAR.
        :param port: chemin du port série (ex: /dev/ttyUSB0)
        :param baud: vitesse de communication
        :param timeout: délai max de lecture série (s)
        """
        self.ser = serial.Serial(port, baud, timeout=timeout)
        self.buf = bytearray()
        self.last_S = 0
        print(f"[INIT] LIDAR connecté sur {port} @ {baud} bauds")

    # ---------------------
    # Fonctions bas-niveau
    # ---------------------

    def close(self):
        """Arrête le scan et ferme proprement le port série."""
        try:
            self.ser.write(self.CMD_STOP)
            self.ser.flush()
            time.sleep(0.05)
        except Exception:
            pass
        self.ser.close()
        print("[CLOSE] LIDAR arrêté et port fermé.")

    def _read_exactly(self, n, timeout=1.0):
        """Lit exactement n octets, ou None si délai dépassé."""
        start = time.time()
        data = bytearray()
        while len(data) < n and time.time() - start < timeout:
            chunk = self.ser.read(n - len(data))
            if chunk:
                data.extend(chunk)
        return bytes(data) if len(data) == n else None

    @staticmethod
    def _decode_sample(b):
        """Décodage d’un paquet de 5 octets selon la spec officielle."""
        if len(b) != 5:
            return None
        b0, b1, b2, b3, b4 = b

        # Bits S et S̅ (doivent être complémentaires)
        S = b0 & 0x01
        S_bar = (b0 >> 1) & 0x01
        if (S ^ S_bar) != 1:
            return None

        # Qualité (6 bits)
        qual = (b0 >> 2) & 0x3F

        # Bit C (constamment à 1)
        C = b1 & 0x01
        if C != 1:
            return None

        # Angle (Q6)
        angle_q6 = (b2 << 7) | (b1 >> 1)
        angle_deg = (angle_q6 / 64.0) % 360.0

        # Distance (Q2)
        dist_q2 = (b4 << 8) | b3
        dist_mm = dist_q2 / 4.0

        return angle_deg, dist_mm, qual, S

    # ---------------------
    # Commandes principales
    # ---------------------

    def start_scan(self):
        """Envoie la commande de scan standard et attend le descripteur."""
        print("[SEND] Stop + Start scan")
        self.ser.write(self.CMD_STOP)
        self.ser.flush()
        time.sleep(0.05)

        self.ser.write(self.CMD_SCAN)
        self.ser.flush()

        desc = self._read_exactly(7)
        print("[DESC]", desc.hex() if desc else "None")

        if desc != self.DESC_SCAN:
            print("[WARN] Descripteur inattendu — poursuite du scan.")
        else:
            print("[OK] Scan standard confirmé.")
        self.buf.clear()
        self.last_S = 0

    def get_scan(self, min_dist=50, max_dist=6000):
        """
        Lit un tour complet et renvoie un tableau Nx3 [angle_deg, dist_mm, qual].
        """
        revolution = []
        while True:
            self.buf.extend(self.ser.read(256))
            while len(self.buf) >= 5:
                pkt = bytes(self.buf[:5])
                del self.buf[:5]
                decoded = self._decode_sample(pkt)
                if not decoded:
                    continue

                angle, dist, qual, S = decoded

                # Détection d'une révolution complète (S : 0→1)
                if S == 1 and self.last_S == 0 and len(revolution) > 100:
                    return np.array(revolution)
                self.last_S = S

                # Enregistrement point valide
                if min_dist < dist < max_dist:
                    revolution.append((angle, dist, qual))
