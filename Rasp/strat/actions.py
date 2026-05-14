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
    from interface_actionneur.esp_actionneur import ESPActionneurs
    actionneurs = ESPActionneurs()
    actionneurs.start()
except Exception as e:
    print(f"⚠️ Attention : Erreur de chargement du module Actionneur ({e}) -> Mode simulation")
    actionneurs = None

# --- VISION KAPLAS ---
try:
    # On importe ta nouvelle classe cam
    from Vision.cam import cam
    print("[VISION] Lancement de la caméra...")
    # On initialise avec l'état défini dans la config
    cam_enabled = shared.cfg.get('camera', {}).get('enabled', True)
    vision_cam = cam(use_camera=cam_enabled)
except Exception as e:
    print(f"  Attention : Erreur de chargement du module Vision ({e}) -> Mode aveugle")
    vision_cam = None

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
        shared.state["is_returning"] = False
        self.base_pos = None # (x, y, theta) stockés avant symétrie

    @property
    def is_yellow(self):
        return shared.state["team"] == "JAUNE"

    def _check_time(self):
        # On ne lève plus d'exception automatique à 90s
        # On vérifie juste si le match est arrêté (STOP)
        pass

    def _check_abort(self, manual=False):
        if not manual and not shared.state["match_running"]: raise Exception("Stop")
        self._check_time()

    def _apply_sym(self, x, y, theta=None):
        """Symétrie axiale pour l'équipe JAUNE (Y négatif)"""
        if self.is_yellow:
            new_x = x
            new_y = -y
            # Pour une symétrie sur l'axe Y (miroir horizontal), l'angle s'inverse
            new_theta = (-theta) % 360 if theta is not None else None
            return new_x, new_y, new_theta
        return x, y, theta
    
    def set_pos(self, x, y, theta):
        """
        Définit la position du robot (Triche / Recalage).
        Met à jour l'IHM Web ET l'odométrie de l'ESP32.
        """
        # On mémorise la première position comme étant la "Base" pour le retour fin de match
        if self.base_pos is None:
            self.base_pos = (x, y, theta)
            print(f"[ACTION] Base enregistrée : ({x}, {y}, {theta}°)")

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

        # provisoire : pose caméra actionneurs
        if actionneurs:
            actionneurs.pose_camera()
        else:
            print("[SIMU] Actionneurs non connectés, impossible de poser la caméra.")


    def goto(self, x, y, theta, manual=False, real=False):
        """
        Déplacement en ligne droite + Envoi ESP32
        """
        self._check_abort(manual=manual)
        
        if not real:
            real_x, real_y, real_theta = self._apply_sym(x, y, theta)
        else:
            real_x, real_y, real_theta = x, y, theta

        if esp:
            success = esp.goto(real_x, real_y, real_theta)
            while not success:
                print(f"[ACTION] 🔄 GOTO annulé par l'ESP (Obstacle), recalcul et relance vers ({real_x}, {real_y}, {real_theta}°)")
                self._check_abort()
                time.sleep(0.5)
                success = esp.goto(real_x, real_y, real_theta)
        else:
            print("[SIMU] GOTO virtuel (Pas de com)")
        
    def stop(self):
        print("[ACTION] STOP")
        if esp:
            esp.stop()
        else:
            print("[SIMU] STOP virtuel (Pas de com)")

    def set_lidar_state(self, val):
        """Définit l'état du LiDAR sur l'ESP32 (0: Libre, 1: Stop, 2: Front, 3: Back)"""
        if esp:
            esp.set_lidar_state(val)
        else:
            print(f"[SIMU] SET LIDAR STATE {val} virtuel")

    def toggle_lidar(self):
        """Ancienne fonction de toggle (Legacy)"""
        print("[ACTION] TOGGLE LIDAR")
        if esp:
            # On simule un toggle simple 0/1
            new_val = 1 if shared.state.get("obstacle_detected", False) else 0
            esp.set_lidar_state(1 - new_val)
        else:
            print("[SIMU] TOGGLE LIDAR virtuel")

    def approcheKapla(self):
        self._check_abort()
        print("[ACTION] Recalage visuel : Latéral (Y) puis Profondeur (X)...")

        if not vision_cam:
            print("[VISION] Caméra indisponible, mouvement à l'aveugle.")
            x_robot, y_robot, theta_robot = shared.robot_pos['x'], shared.robot_pos['y'], shared.robot_pos['theta']
            x = x_robot - math.cos(math.radians(theta_robot)) * 100
            y = y_robot - math.sin(math.radians(theta_robot)) * 100
            self.goto(x, y, theta_robot)
            self.goto(0, 0, 0)
            return

        # 1. LECTURE INITIALE (Au plus près des Kaplas pour une meilleure visibilité)
        print("[VISION] 1. Stabilisation et Lecture initiale...")
        time.sleep(0.5) # On laisse le robot s'arrêter complètement pour éviter le flou
        vision_cam.check_aruco_position()
        vision_cam.save_debug(prefix="init_approche")
        init_err_x, init_err_y, init_err_angle = vision_cam.get_errors()
        
        # On sauvegarde la position absolue des Kaplas au cas où on les perd de vue après le recul
        target_fallback = None
        deja_aligne = False
        if init_err_x is not None:
            x_actuel, y_actuel, theta_actuel = shared.robot_pos['x'], shared.robot_pos['y'], shared.robot_pos['theta']
            theta_rad = math.radians(theta_actuel)
            tx = x_actuel + (init_err_x * math.cos(theta_rad)) - (init_err_y * math.sin(theta_rad))
            ty = y_actuel + (init_err_x * math.sin(theta_rad)) + (init_err_y * math.cos(theta_rad))
            tt = (theta_actuel + init_err_angle) % 360
            target_fallback = (tx, ty, tt)
            print(f"[VISION] Kaplas repérés ! Prof:{init_err_x:.1f}mm, Lat:{init_err_y:.1f}mm, Angle:{init_err_angle:.1f}°")
            
            # Si on est déjà bien en face, on s'épargne le recul et le recalage !
            if abs(init_err_y) < 5 and abs(init_err_angle) < 2:
                print("[VISION] Robot déjà parfaitement aligné ! On passe direct à l'approche.")
                deja_aligne = True
        else:
            print("[VISION] ArUco non vus de près, on tente quand même le recul...")

        if not deja_aligne:
            # 2. RECUL INITIAL (pour avoir la place de manœuvrer latéralement)
            x_actuel, y_actuel, theta_actuel = shared.robot_pos['x'], shared.robot_pos['y'], shared.robot_pos['theta']
            theta_rad = math.radians(theta_actuel)
            recul = 150
            print(f"[VISION] 2. Manœuvre de dégagement (Recul de {recul}mm)...")
            self.goto(x_actuel - recul * math.cos(theta_rad), y_actuel - recul * math.sin(theta_rad), theta_actuel, real=True)
            time.sleep(0.5)
    
            # 3. BOUCLE D'ALIGNEMENT LATÉRAL (Erreur Y)
            print("[VISION] 3. Alignement Latéral (Gauche/Droite)...")
            for tentative in range(3):
                self._check_abort()
                vision_cam.check_aruco_position()
                vision_cam.save_debug(prefix="approche")
                err_x, err_y, err_angle = vision_cam.get_errors()
                
                if err_x is None:
                    print("[VISION] ArUco perdu, arrêt de l'alignement.")
                    break
    
                print(f"[VISION] Latéral T{tentative+1} -> X(Prof):{err_x:.1f}mm, Y(Lat):{err_y:.1f}mm, Angle:{err_angle:.1f}°")
    
                # Si l'erreur Y (latérale) et l'angle sont faibles, on est bien en face
                if abs(err_y) < 5 and abs(err_angle) < 2:
                    print("[VISION] Alignement Y parfait !")
                    break
    
                # Correction uniquement sur l'axe Y (latéral) et l'Angle
                # On conserve la profondeur actuelle (on ne corrige pas err_x ici)
                x_actuel, y_actuel, theta_actuel = shared.robot_pos['x'], shared.robot_pos['y'], shared.robot_pos['theta']
                theta_rad = math.radians(theta_actuel)
                
                # Correction de Y (gauche/droite par rapport au robot)
                cible_x = x_actuel - (err_y * math.sin(theta_rad))
                cible_y = y_actuel + (err_y * math.cos(theta_rad))
                cible_theta = (theta_actuel + err_angle) % 360
    
                self.goto(cible_x, cible_y, cible_theta, real=True)
                time.sleep(0.5) # Pause pour stabiliser la caméra

        # 4. APPROCHE FINALE (Erreur X - Profondeur)
        self._check_abort()
        vision_cam.check_aruco_position()
        vision_cam.save_debug(prefix="approche")
        err_x, err_y, err_angle = vision_cam.get_errors()
        
        if err_x is not None:
            print(f"[VISION] 4. Approche Finale (Profondeur) de {err_x:.1f}mm...")
            x_actuel, y_actuel, theta_actuel = shared.robot_pos['x'], shared.robot_pos['y'], shared.robot_pos['theta']
            theta_rad = math.radians(theta_actuel)
            
            # On avance tout droit pour corriger err_x
            final_x = x_actuel + (err_x * math.cos(theta_rad))
            final_y = y_actuel + (err_x * math.sin(theta_rad))
            
            self.goto(final_x, final_y, theta_actuel, real=True)
        elif target_fallback is not None:
            print("[VISION] ArUco perdu. Utilisation de la position de secours (sauvegardée au début) !")
            self.goto(target_fallback[0], target_fallback[1], target_fallback[2], real=True)
        else:
            print("[VISION] ÉCHEC : ArUco introuvable, abandon de l'approche !")

    def prendreKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Prise Kapla H={hauteur}")
        time.sleep(1)

    def prendre_kaplas_camera(self):
        self._check_abort()
        print(f"[ACTION] Analyse couleurs pour les 4 Kaplas (Equipe JAUNE={self.is_yellow})...")
        
        if vision_cam:
            # On déclenche une nouvelle capture et analyse
            vision_cam.check_aruco_position()
            vision_cam.save_debug(prefix="prise")
            
            # On récupère le tableau de booléens (True = bonne couleur)
            bonnes_couleurs = vision_cam.get_colors(self.is_yellow)
            
        time.sleep(1)

    def poseKapla(self, hauteur=0):
        self._check_abort()
        print(f"[ACTION] Pose Kapla H={hauteur}")
        time.sleep(1)

    def pousse_kapla(self):
        self._check_abort()
        print("[ACTION] Pousse Kapla")
        if vision_cam:
            # On récupère le tableau de booléens (True = bonne couleur)
            print(vision_cam.check_aruco_position())
            vision_cam.save_debug(prefix="pousse")
            bonnes_couleurs = vision_cam.get_colors_pousse(self.is_yellow)
            if len(bonnes_couleurs) < 3:
                print(f"[VISION] Detection incomplète ({len(bonnes_couleurs)}/3), complétion par défaut.")
                while len(bonnes_couleurs) < 4:
                    bonnes_couleurs.append(True)

        else:
            print("[VISION/SIMU] Simulation des Kaplas (Caméra non dispo).")
            bonnes_couleurs = [True, True, True, True]
        
        x_actuel = shared.robot_pos['x']
        y_actuel = shared.robot_pos['y']
        theta_actuel = shared.robot_pos['theta']
        theta_rad = math.radians(theta_actuel)

        print("bonnes_couleurs = ", bonnes_couleurs)

        avancer_mm = 25
        if bonnes_couleurs[0] == True:
            print("bonnes_couleurs[0] = True")
            avancer_mm += 0
            if bonnes_couleurs[1] == True:
                print("bonnes_couleurs[1] = True")
                avancer_mm += 50 # on met les 2 premier kaplas
            else :
                print("bonnes_couleurs[1] = False")
                if bonnes_couleurs[2] == True:
                    avancer_mm += 100 # on met les 3 premier kaplas
                # pas de else on ne met que le premier kapla
        else :
            print("bonnes_couleurs[0] = False")
            if bonnes_couleurs[1] == True and bonnes_couleurs[2] == True :
                print("bonnes_couleurs[1] = True and bonnes_couleurs[2] = True")
                avancer_mm += 100 # on met les 3 premier kaplas
            else :
                print("bonnes_couleurs[1] = False and bonnes_couleurs[2] = False")
                avancer_mm += 250 # on met les 3 dernier kaplas
        
        print("avancer_mm =", avancer_mm)

        x_kapla = x_actuel + avancer_mm * math.cos(theta_rad)
        y_kapla = y_actuel + avancer_mm * math.sin(theta_rad)

        self.goto(x_kapla, y_kapla, theta_actuel, real=True)
        
    def GoBase(self):
        self.is_returning = True
        shared.state["is_returning"] = True
        print("⚡ RETOUR BASE")
        if self.base_pos:
            bx, by, bt = self.base_pos
            # On revient aux coordonnées de départ avec un angle inversé (180°)
            target_theta = (bt + 180)
            # Normalisation entre -180 et 180 (optionnel mais propre)
            while target_theta > 180: target_theta -= 360
            while target_theta <= -180: target_theta += 360
            
            self.goto(bx + 550, by, target_theta)
            self.goto(bx, by, target_theta)
        else:
            # Fallback historique si set_pos n'a pas été appelé
            self.goto(250, 0, 180)
        time.sleep(1)

    def wait_until_and_return(self, target_second):
        self._check_abort()
        print(f"[ACTION] Attente de la seconde {target_second} pour retour base...")
        while shared.state["match_running"]:
            elapsed = time.time() - shared.state["start_time"]
            if elapsed >= target_second:
                break
            time.sleep(0.5)
        self.GoBase()

    def play_animation(self, anim_name):
        self._check_abort()
        print(f"[ACTION] Playing Animation: {anim_name}")
        shared.send_led_cmd(f"PLAY:{anim_name}")

    def play_sound(self, sound_name):
        self._check_abort()
        print(f"[ACTION] Playing Sound: {sound_name}")
        shared.audio.play(sound_name)


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