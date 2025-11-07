#!/usr/bin/env python3
import serial, time # type: ignore
import numpy as np
import matplotlib.pyplot as plt

class RPLidarC1M1:
    """Gestion du LIDAR RPLiDAR C1M1 (mode standard 0x20)."""

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
        """Décodage d’un paquet de 5 octets selon la spec C1M1."""
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

                if min_dist < dist < max_dist:
                    revolution.append((angle, dist, qual))

    # ---------------------
    # Mode affichage temps réel
    # ---------------------

    def plot_live_pygame_threaded(self, rmax=4000, fps=15, step=500):
        """
        Affichage temps réel PyGame (fluide + interactif + auto seuil)
        -----------------------------------------------------------------
        - Thread acquisition LIDAR séparé
        - Orientation corrigée
        - ↑ / ↓ : ajuste le seuil manuel
        - A : seuil automatique (top 5 % des points)
        - Échelle de distance (cercles + labels)
        - Points > seuil = blanc (bande réfléchissante)
        - ESC ou croix pour quitter proprement
        """
        import pygame, math, threading, queue, numpy as np, time

        print("[PYGAME-LIVE] Démarrage du LIDAR (thread séparé)...")
        self.start_scan()

        # --- paramètres d'affichage ---
        size = 600
        scale = size / (2 * rmax)
        center = size // 2
        bg_color = (0, 0, 0)

        pygame.init()
        screen = pygame.display.set_mode((size, size))
        pygame.display.set_caption("RPLidarC1M1 — Live PyGame (threaded)")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 14)

        q_scans = queue.Queue(maxsize=2)
        running = True
        qual_thresh = 50
        auto_mode = False

        # --- thread acquisition LIDAR ---
        def lidar_thread():
            while running:
                try:
                    scan = self.get_scan(min_dist=20, max_dist=rmax)
                    if len(scan) == 0:
                        continue
                    if q_scans.full():
                        q_scans.get_nowait()
                    q_scans.put_nowait(scan)
                except Exception as e:
                    print("[LIDAR-THREAD] erreur:", e)
                    time.sleep(0.05)

        t = threading.Thread(target=lidar_thread, daemon=True)
        t.start()

        def mm_to_px(x_mm, y_mm):
            return int(center + x_mm * scale), int(center - y_mm * scale)

        def draw_scale():
            """Dessine les cercles d’échelle et les labels distance."""
            for r in range(step, rmax + step, step):
                pygame.draw.circle(screen, (50, 50, 50), (center, center), int(r * scale), 1)
                label = font.render(f"{r} mm", True, (150, 150, 150))
                x, y = mm_to_px(0, -r)
                screen.blit(label, (x + 5, y - 10))

        frame = 0
        last_scan = None

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_UP:
                        qual_thresh = min(qual_thresh + 5, 63)
                        auto_mode = False
                        print(f"[QUAL] seuil manuel = {qual_thresh}")
                    elif event.key == pygame.K_DOWN:
                        qual_thresh = max(qual_thresh - 5, 0)
                        auto_mode = False
                        print(f"[QUAL] seuil manuel = {qual_thresh}")
                    elif event.key == pygame.K_a:
                        auto_mode = True
                        print("[AUTO] mode adaptatif activé")

            screen.fill(bg_color)
            draw_scale()

            # lecture du dernier scan dispo
            if not q_scans.empty():
                last_scan = q_scans.get_nowait()

            if last_scan is not None:
                angles = np.radians(last_scan[:, 0])
                dists = last_scan[:, 1]
                qual = last_scan[:, 2]

                # mode auto : top 5 % des valeurs
                if auto_mode and len(qual) > 20:
                    qual_thresh = int(np.percentile(qual, 95))

                x = dists * np.sin(angles)
                y = -dists * np.cos(angles)

                for i in range(len(x)):
                    q = int(qual[i])
                    px, py = mm_to_px(x[i], y[i])
                    if not (0 <= px < size and 0 <= py < size):
                        continue

                    if q >= qual_thresh:
                        color = (255, 255, 255)  # bande réfléchissante
                    else:
                        color = pygame.Color(0)
                        color.hsva = (int(240 - 240 * q / 63), 100, 100, 100)

                    screen.set_at((px, py), color)

            # centre et infos
            pygame.draw.circle(screen, (100, 100, 100), (center, center), 3)
            txt = font.render(
                f"{frame:04d} | Seuil: {qual_thresh} ({'AUTO' if auto_mode else 'MANU'})",
                True, (220, 220, 220),
            )
            screen.blit(txt, (10, 10))

            pygame.display.flip()
            clock.tick(fps)
            frame += 1

        self.close()
        pygame.quit()
        print("[PYGAME-LIVE] Fin de l'affichage propre.")

    
    # ---------------------
    # Mode analyse qualité (interactif)
    # ---------------------

    def plot_reflectivity(self, rmax=6000, qual_min=0):
        """
        Affiche une carte (x, y) de la qualité des mesures.
        Permet d'ajuster dynamiquement le seuil de qualité avec ↑/↓.
        """
        import matplotlib.pyplot as plt

        print("[REFLECTIVITY] Scan en cours...")
        self.start_scan()
        scan = self.get_scan(min_dist=20, max_dist=rmax)
        self.close()

        if len(scan) == 0:
            print("[WARN] Aucun point détecté.")
            return

        angles = np.radians(scan[:, 0])
        dists = scan[:, 1]
        qual = scan[:, 2]
        x = dists * np.cos(angles)
        y = dists * np.sin(angles)

        fig, ax = plt.subplots(figsize=(8, 6))
        sc = ax.scatter(x, y, c=qual, s=10, cmap='turbo', vmin=0, vmax=63)
        cbar = plt.colorbar(sc, label='Qualité (0–63)')
        ax.set_title(f"Carte de qualité LIDAR — seuil {qual_min}")
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")
        ax.set_xlim(-rmax, rmax)
        ax.set_ylim(-rmax, rmax)
        ax.set_aspect('equal', 'box')

        # Filtrage initial
        def update_plot(threshold):
            mask = qual >= threshold
            sc.set_offsets(np.c_[x[mask], y[mask]])
            sc.set_array(qual[mask])
            ax.set_title(f"Carte de qualité LIDAR — seuil {threshold}")
            fig.canvas.draw_idle()

        # Interaction clavier
        current = qual_min

        def on_key(event):
            nonlocal current
            if event.key == "up":
                current = min(current + 1, 63)
                update_plot(current)
            elif event.key == "down":
                current = max(current - 1, 0)
                update_plot(current)
            elif event.key == "escape":
                plt.close(fig)

        fig.canvas.mpl_connect("key_press_event", on_key)
        update_plot(qual_min)
        plt.show()

