import threading
import time
import serial
import ast
import numpy as np
from .ekf_localizer import EKFLocalizer

class NavigationManager:
    def __init__(self, port_esp='/dev/esp32_motors', baudrate_esp=115200, port_lidar='/dev/lidar'):
        self.ekf = EKFLocalizer(port=port_lidar)
        
        try:
            self.ser_esp = serial.Serial(port=port_esp, baudrate=baudrate_esp, timeout=0.1)
        except Exception as e:
            print(f"[NAV] Attention, ESP32 non connectée ({e}). Mode simulation/dégradé.")
            self.ser_esp = None
            
        self.lock = threading.Lock()
        self.odom_raw = np.array([0.0, 0.0, 0.0]) 
        self.last_odom_raw = np.array([0.0, 0.0, 0.0])
        self.robot_pose_fused = np.array(self.ekf.x) # Init avec la pose de l'EKF
        self.last_vis = {}
        self.last_scan = None
        
        self.running = False
        self.thread_uart = threading.Thread(target=self._uart_loop, daemon=True)
        self.thread_ekf = threading.Thread(target=self._ekf_loop, daemon=True)

    def start(self):
        self.running = True
        
        # Démarrage physique du scan Lidar
        try:
            print("[NAV] Allumage du moteur LiDAR...")
            self.ekf.start_scan()
            import time
            time.sleep(1) # Temps pour que le moteur atteigne sa vitesse de rotation
            self.ekf.clean_input()
        except Exception as e:
            print(f"[NAV] Attention, erreur au démarrage du LiDAR : {e}")

        if self.ser_esp:
            self.thread_uart.start()
        self.thread_ekf.start()
        print("[NAV] Système de navigation démarré.")

    def stop(self):
        self.running = False
        if self.ser_esp:
            self.thread_uart.join()
        self.thread_ekf.join()
        self.ekf.close()
        if self.ser_esp:
            self.ser_esp.close()

    def _uart_loop(self):
        while self.running and self.ser_esp:
            try:
                line = self.ser_esp.readline().decode(errors="ignore").strip()
                if line.startswith('[') and line.endswith(']'):
                    msg_list = ast.literal_eval(line)
                    with self.lock:
                        # Adaptation aux unités envoyées par ton ESP32
                        self.odom_raw = np.array([
                            msg_list[0] * 1000.0, 
                            msg_list[1] * 1000.0, 
                            msg_list[2] # Angle en radians
                        ])
            except Exception:
                pass
            time.sleep(0.01)

    def _ekf_loop(self):
        last_time = time.time()
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            with self.lock:
                delta_odom = self.odom_raw - self.last_odom_raw
                self.last_odom_raw = self.odom_raw.copy()
            
            # Gestion du passage -pi / pi
            delta_odom[2] = (delta_odom[2] + np.pi) % (2 * np.pi) - np.pi

            # Step EKF : Prédiction (odom) + Correction (Lidar)
            pose, vis, scan = self.ekf.step(
                dt=dt, 
                dx=delta_odom[0], 
                dy=delta_odom[1], 
                dtheta=delta_odom[2]
            )
            
            with self.lock:
                self.robot_pose_fused = np.array(pose)
                self.last_vis = vis
                if scan is not None and len(scan) > 0:
                    self.last_scan = scan
            
            time.sleep(0.05) # Boucle à 20Hz

    def get_pose(self):
        with self.lock:
            return self.robot_pose_fused.copy()
            
    def get_covariance(self):
        with self.lock:
            return self.ekf.P.copy()

    def get_visibility(self):
        with self.lock:
            return self.last_vis.copy()

    def get_scan(self):
        with self.lock:
            return self.last_scan.copy() if self.last_scan is not None else None