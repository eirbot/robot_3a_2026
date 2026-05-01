# strat/actions.py
import time
import math
import ihm.shared as shared

# --- AJOUT AU PATH GLOBAL POUR LES IMPORTS CROSS-FOLDERS ---
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- COM ACTIONNEURS (via module dédié) ---
try:
    from Actionneur.interface_actionneur import InterfaceActionneur
    actionneurs = InterfaceActionneur()
except Exception as e:
    print(f"⚠️ Attention : Erreur de chargement du module Actionneur ({e}) -> Mode simulation")
    actionneurs = None

# --- VISION KAPLAS (via module dédié) ---
try:
    from utils.sensors.camera_libcamera import LibCamera
    from Vision.vision_kapla import KaplaVision
    print("[VISION] Démarrage Picamera2 (LibCamera)...")
    cam = LibCamera()
    cam.start()
    vision = KaplaVision(cam)
except Exception as e:
    print(f"⚠️ Attention : Erreur de chargement du module Vision/Caméra ({e}) -> Pas de détection auto")
    vision = None

try:
    # On essaie d'importer la classe ESPMotors
    from interface_deplacement.esp_motors import ESPMotors
    esp = ESPMotors()
    esp.start()

except ImportError as e:
    print(f"⚠️ Attention : Modules de déplacement non trouvés ({e}) -> Mode Simulation pur")
    esp = None

# --- CONSTANTES ---
TABLE_WIDTH = 3000
TIME_TO_RETURN = 90

class EndOfMatchException(Exception):
    pass

class RobotActions:
    def __init__(self):
        self.is_returning = False

    @property
    def is_yellow(self):
        return shared.state["team"] == "JAUNE"

    def _check_time(self):
        if self.is_returning: return
        if shared.state["match_running"] and shared.state["start_time"]:
            if time.time() - shared.state["start_time"] >= TIME_TO_RETURN:
                raise EndOfMatchException("Time to go home")

    def _check_abort(self):
        if not shared.state["match_running"]: raise Exception("Stop")
        self._check_time()

    def _apply_sym(self, x, y, theta=None):
        """Symétrie axiale pour l'équipe JAUNE (Axe Y=0 au centre)"""
        if self.is_yellow:
            new_x = x
            new_y = -y
            new_theta = (-theta) % 360 if theta is not None else None
            return new_x, new_y, new_theta
        return x, y, theta
    
    def set_pos(self, x, y, theta):
        """
        Définit la position du robot (Triche / Recalage).
        Met à jour l'IHM Web ET l'odométrie de l'ESP32.
        """
        # 1. Calcul de la position réelle (Symétrie équipe)
        real_x, real_y, real_theta = self._apply_sym(x, y, theta)
        
        # 2. Mise à jour Interface Web (Shared)
        shared.robot_pos.update({'x': real_x, 'y': real_y, 'theta': real_theta})
        print(f"[ACTION] SET_POS -> ({real_x}, {real_y}, {real_theta}°)")

        # 3. Envoi à l'ESP32 (Reset Odométrie)
        if esp:
            esp.set_pos(real_x, real_y, real_theta)
        else:
            print("[SIMU] SET_POS virtuel (Pas de com)")


    # --- LE COEUR DU SUJET : GOTO BEZIER ---
    def goto(self, x, y, theta):
        """
        Déplacement via Courbe de Bézier + Envoi ESP32
        """
        self._check_abort()

        if esp:
            esp.goto(x, y, theta)
        else:
            print("[SIMU] GOTO virtuel (Pas de com)")
        
    def stop(self):
        print("[ACTION] STOP")
        if esp:
            esp.stop()
        else:
            print("[SIMU] STOP virtuel (Pas de com)")

    def approcheKapla(self):
        self._check_abort()
        print("[ACTION] Approche Kapla")
        x_robot, y_robot, theta_robot = shared.robot_pos['x'], shared.robot_pos['y'], shared.robot_pos['theta']
        # On recule par rapport à l'angle du robot pour se recaler bien devant
        x = x_robot - cos(theta_robot) * 100
        y = y_robot - sin(theta_robot) * 100
        self.goto(x, y, theta_robot)
        # TODO : recupération des coo via la camera
        x_kapla, y_kapla, theta_kapla = 0, 0, 0
        self.goto(x_kapla, y_kapla, theta_kapla)

    def prendreKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Prise Kapla H={hauteur}")
        time.sleep(1)

    def retournerKapla(self):
        self._check_abort()
        print("[ACTION] Retourne Kapla")
        time.sleep(1)

    def poseKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Pose Kapla H={hauteur}")
        time.sleep(1)

    def GoBase(self):
        self.is_returning = True
        print("⚡ RETOUR BASE")
        self.goto(250, 0, 180)
        time.sleep(1)

    def play_animation(self, anim_name):
        self._check_abort()
        print(f"[ACTION] Playing Animation: {anim_name}")
        shared.send_led_cmd(f"PLAY:{anim_name}")

    def play_sound(self, sound_name):
        self._check_abort()
        print(f"[ACTION] Playing Sound: {sound_name}")
        shared.audio.play(sound_name)

    def prendre_kaplas_camera(self):
        """
        Utilise la caméra MIPI et OpenCV ArUco pour récupérer 
        l'orientation des 4 Kaplas et actionner avec FLIP ou nFLIP appropriés.
        """
        self._check_abort()
        print(f"[ACTION] Analyse Caméra (ArUco) pour les 4 Kaplas (Equipe JAUNE={self.is_yellow})...")
        
        if vision:
            kaplas_decision = vision.detect_kaplas_orientation(team_yellow=self.is_yellow)
        else:
            print("[VISION/SIMU] Simulation des Kaplas (Caméra non disponible).")
            kaplas_decision = ["nFLIP", "nFLIP", "nFLIP", "nFLIP"]
            
        print(f"[DECISION] Actionneurs : 1={kaplas_decision[0]} | 2={kaplas_decision[1]} | 3={kaplas_decision[2]} | 4={kaplas_decision[3]}")
        
        self.cmd_actionneurs(
            act1=kaplas_decision[0],
            act2=kaplas_decision[1],
            act3=kaplas_decision[2],
            act4=kaplas_decision[3]
        )
        time.sleep(1)

    def cmd_actionneurs(self, command_string=None, act1=None, act2=None, act3=None, act4=None):
        """
        Interface Blockly vers le module Actionneur dédié.
        """
        self._check_abort()
        if actionneurs:
            if command_string is not None:
                actionneurs.send_raw(command_string)
            else:
                actionneurs.send_cmd(act1, act2, act3, act4)
        else:
            print("[SIMU] Pas d'interface Actionneur connectée (Mode sans matériel).")