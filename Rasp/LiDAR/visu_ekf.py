#!/usr/bin/env python3
import tkinter as tk
from PIL import Image, ImageTk
import threading
import queue
import time
import numpy as np

# Importer ta classe EKF
from ekf_localizer import EKFLocalizer

# --- CONFIGURATION ---
TABLE_IMAGE = "table_coupe_2026.png"
ROBOT_IMAGE = "robot.png"

# Dimensions réelles de la table (en mm)
TABLE_WIDTH_MM = 3000.0
TABLE_HEIGHT_MM = 2000.0

ROBOT_SIZE_MM = 300.0   

# Position de départ
INIT_X = 500.0   
INIT_Y = 0.0     
INIT_TH = 0.0    

# Positions théoriques des balises
FIXED_BEACONS = {
    "A": (50.0, -1594.0),
    "B": (1950.0, -1594.0),
    "C": (1000.0, 1594.0),
    # "D": (-100.0, 200.0),
}

# --- ZONE MONDE ---
WORLD_MIN_X = -300.0  
WORLD_MAX_X = 2300.0  
WORLD_MIN_Y = -1800.0 
WORLD_MAX_Y = 1800.0  

REAL_WORLD_WIDTH_MM = WORLD_MAX_Y - WORLD_MIN_Y 
REAL_WORLD_HEIGHT_MM = WORLD_MAX_X - WORLD_MIN_X 

CANVAS_WIDTH_PX = 600

class RobotMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualisation EKF + Odom Absolue")
        
        self.data_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        self.running = True

        # --- MEMOIRE ODOMETRIE ---
        # On stocke la dernière position rapportée par les "moteurs"
        # pour calculer le delta à chaque nouvelle entrée.
        self.last_odom = {
            "x": INIT_X,
            "y": INIT_Y,
            "th": INIT_TH # en degrés pour l'interface
        }

        # 1. Assets
        self.load_and_scale_assets()

        # 2. Canvas
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height, bg="#222222")
        self.canvas.pack(side=tk.TOP)
        
        # Table
        table_x_scr, table_y_scr = self.mm_to_screen(0, -1500.0)
        self.canvas.create_image(table_x_scr, table_y_scr, image=self.tk_table_img, anchor="nw")
        
        # Balises
        self.draw_fixed_beacons()

        # Robot
        self.robot_sprite_id = self.canvas.create_image(0, 0, image=None, anchor="center")
        
        # Info Text
        self.text_info = self.canvas.create_text(10, 10, anchor="nw", text="En attente...", fill="white", font=("Arial", 14, "bold"))

        # 3. PANNEAU DE CONTROLE (Entrée Odom Absolue)
        self.create_control_panel()

        # 4. Thread EKF
        self.ekf_thread = threading.Thread(target=self.run_ekf, daemon=True)
        self.ekf_thread.start()

        self.update_gui()

    def create_control_panel(self):
        """Zone pour entrer la position rapportée par l'odométrie moteur."""
        frame = tk.Frame(self.root, bg="#444444", bd=5)
        frame.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(frame, text="Lecture Odom (Moteurs):", bg="#444", fg="cyan").pack(side=tk.LEFT, padx=5)

        # Entrée X
        tk.Label(frame, text="X:", bg="#444", fg="#ddd").pack(side=tk.LEFT)
        self.entry_x = tk.Entry(frame, width=6)
        self.entry_x.insert(0, str(int(INIT_X)))
        self.entry_x.pack(side=tk.LEFT, padx=2)

        # Entrée Y
        tk.Label(frame, text="Y:", bg="#444", fg="#ddd").pack(side=tk.LEFT)
        self.entry_y = tk.Entry(frame, width=6)
        self.entry_y.insert(0, str(int(INIT_Y)))
        self.entry_y.pack(side=tk.LEFT, padx=2)

        # Entrée Theta
        tk.Label(frame, text="Th°:", bg="#444", fg="#ddd").pack(side=tk.LEFT)
        self.entry_th = tk.Entry(frame, width=6)
        self.entry_th.insert(0, str(int(INIT_TH)))
        self.entry_th.pack(side=tk.LEFT, padx=2)

        # Bouton Appliquer
        btn = tk.Button(frame, text="UPDATE ODOM", command=self.send_odom_update, bg="#008800", fg="white")
        btn.pack(side=tk.LEFT, padx=10)
        
        # Bouton Reset
        btn_rst = tk.Button(frame, text="RESET TOUT", command=self.send_reset, bg="#880000", fg="white")
        btn_rst.pack(side=tk.RIGHT, padx=5)

    def send_odom_update(self):
        """Calcule le delta entre la nouvelle odom et l'ancienne, puis envoie."""
        try:
            # 1. Lire la nouvelle "position absolue" des encodeurs
            new_odom_x = float(self.entry_x.get())
            new_odom_y = float(self.entry_y.get())
            new_odom_th_deg = float(self.entry_th.get())
            
            # 2. Calculer le déplacement (Delta) depuis la dernière fois
            dx = new_odom_x - self.last_odom["x"]
            dy = new_odom_y - self.last_odom["y"]
            dth_deg = new_odom_th_deg - self.last_odom["th"]
            
            # 3. Mettre à jour la mémoire
            self.last_odom["x"] = new_odom_x
            self.last_odom["y"] = new_odom_y
            self.last_odom["th"] = new_odom_th_deg

            # 4. Envoyer le delta au filtre
            cmd = {
                "type": "move",
                "dx": dx,
                "dy": dy,
                "dtheta": np.radians(dth_deg)
            }
            self.command_queue.put(cmd)
            print(f"[GUI] Odom passée de {self.last_odom} -> Delta calculé: dx={dx:.1f}, dy={dy:.1f}")
            
        except ValueError:
            print("[GUI] Erreur : Entrez des nombres valides")

    def send_reset(self):
        """Réinitialise l'EKF et la mémoire odom."""
        # On reset l'EKF
        self.command_queue.put({"type": "reset"})
        
        # On reset aussi la mémoire locale de l'interface
        self.last_odom = {"x": INIT_X, "y": INIT_Y, "th": INIT_TH}
        
        # On remet les champs à jour
        self.entry_x.delete(0, tk.END); self.entry_x.insert(0, str(int(INIT_X)))
        self.entry_y.delete(0, tk.END); self.entry_y.insert(0, str(int(INIT_Y)))
        self.entry_th.delete(0, tk.END); self.entry_th.insert(0, str(int(INIT_TH)))

    def load_and_scale_assets(self):
        self.px_per_mm = CANVAS_WIDTH_PX / REAL_WORLD_WIDTH_MM
        self.canvas_width = CANVAS_WIDTH_PX
        self.canvas_height = int(REAL_WORLD_HEIGHT_MM * self.px_per_mm)

        # Table
        pil_table_raw = Image.open(TABLE_IMAGE)
        table_w_px = int(TABLE_WIDTH_MM * self.px_per_mm)
        table_h_px = int(TABLE_HEIGHT_MM * self.px_per_mm)
        pil_table_scaled = pil_table_raw.resize((table_w_px, table_h_px), Image.LANCZOS)
        self.tk_table_img = ImageTk.PhotoImage(pil_table_scaled)
        
        # Robot
        try:
            self.pil_robot = Image.open(ROBOT_IMAGE)
            r_px = int(ROBOT_SIZE_MM * self.px_per_mm)
            self.pil_robot = self.pil_robot.resize((r_px, r_px), Image.LANCZOS)
        except:
            self.pil_robot = Image.new('RGBA', (int(300*self.px_per_mm), int(300*self.px_per_mm)), (255, 0, 0, 255))

    def mm_to_screen(self, x_mm, y_mm):
        screen_x = (y_mm - WORLD_MIN_Y) * self.px_per_mm
        screen_y = (x_mm - WORLD_MIN_X) * self.px_per_mm
        return screen_x, screen_y

    def draw_fixed_beacons(self):
        r = 8 
        for name, (bx, by) in FIXED_BEACONS.items():
            sx, sy = self.mm_to_screen(bx, by)
            self.canvas.create_line(sx-r, sy-r, sx+r, sy+r, fill="#FF00FF", width=3)
            self.canvas.create_line(sx-r, sy+r, sx+r, sy-r, fill="#FF00FF", width=3)
            self.canvas.create_text(sx+15, sy, text=name, fill="#FF00FF", anchor="w", font=("Arial", 12, "bold"))

    def run_ekf(self):
        """Boucle logique EKF."""
        print("Démarrage EKF...")
        init_pose = (INIT_X, INIT_Y, np.radians(INIT_TH))
        ekf = EKFLocalizer("/dev/ttyUSB0", init_pose=init_pose)
        ekf.start_scan()
        time.sleep(1.0)
        
        while self.running:
            try:
                # 1. Gestion des Commandes
                dx_cmd = 0.0
                dy_cmd = 0.0
                dth_cmd = 0.0
                
                while not self.command_queue.empty():
                    cmd = self.command_queue.get_nowait()
                    if cmd["type"] == "move":
                        dx_cmd += cmd["dx"]
                        dy_cmd += cmd["dy"]
                        dth_cmd += cmd["dtheta"]
                    elif cmd["type"] == "reset":
                        ekf.x = np.array([INIT_X, INIT_Y, np.radians(INIT_TH)])
                        ekf.P = np.eye(3) # Reset covariance brut
                        print("[EKF] Reset Position")

                # 2. Vider le buffer LIDAR
                ekf.clean_input()

                # 3. PREDICT : On injecte le DELTA calculé
                ekf.predict(dt=0.1, dx=dx_cmd, dy=dy_cmd, dtheta=dth_cmd)
                
                # 4. LOCATE
                pose, nb, obs = ekf.locate_once()
                
                # 5. Calcul visuel des points
                seen_beacons = []
                if pose and obs:
                    rx, ry, rth = pose
                    for (key, z, _) in obs:
                        dist = z[0]
                        ang = z[1]
                        glob_ang = rth + ang
                        bx = rx + dist * np.cos(glob_ang)
                        by = ry + dist * np.sin(glob_ang)
                        seen_beacons.append((bx, by))

                if pose:
                    self.data_queue.put({"pose": pose, "nb": nb, "seen": seen_beacons})
                else:
                    self.data_queue.put({"error": "Perte tracking"})
                    
            except Exception as e:
                print(f"Erreur EKF: {e}")
                ekf.close()
                break
        ekf.close()

    def update_gui(self):
        try:
            last_data = None
            while not self.data_queue.empty():
                last_data = self.data_queue.get_nowait()
            
            if last_data:
                if "pose" in last_data:
                    x, y, th = last_data["pose"]
                    nb = last_data["nb"]
                    seen = last_data["seen"]
                    
                    self.draw_robot(x, y, th)
                    
                    self.canvas.delete("scan_debug")
                    rx_scr, ry_scr = self.mm_to_screen(x, y)
                    
                    for (bx, by) in seen:
                        sx, sy = self.mm_to_screen(bx, by)
                        self.canvas.create_line(rx_scr, ry_scr, sx, sy, fill="yellow", dash=(2,2), tags="scan_debug", width=2)
                        self.canvas.create_oval(sx-5, sy-5, sx+5, sy+5, fill="cyan", outline="white", tags="scan_debug")

                    msg = f"X: {x:.0f} | Y: {y:.0f} | Th: {np.degrees(th):.1f}° | Vues: {nb}"
                    self.canvas.itemconfig(self.text_info, text=msg, fill="#00FF00")
                
                elif "error" in last_data:
                    self.canvas.itemconfig(self.text_info, text=last_data["error"], fill="red")

        except queue.Empty:
            pass
        self.root.after(50, self.update_gui)

    def draw_robot(self, x_ekf, y_ekf, th_rad):
        screen_x, screen_y = self.mm_to_screen(x_ekf, y_ekf)
        angle_deg = np.degrees(th_rad)
        rotated_img = self.pil_robot.rotate(-angle_deg, expand=True, resample=Image.BICUBIC)
        self.tk_robot_current = ImageTk.PhotoImage(rotated_img)
        self.canvas.coords(self.robot_sprite_id, screen_x, screen_y)
        self.canvas.itemconfig(self.robot_sprite_id, image=self.tk_robot_current)
        self.canvas.lift(self.robot_sprite_id)

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotMonitor(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.running = False