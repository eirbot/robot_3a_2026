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
        print("[ACTION] Recalage visuel devant les Kaplas (Robot Différentiel)...")

        if not vision_cam:
            print("[VISION] Caméra indisponible, mouvement à l'aveugle.")
            # Mouvement par défaut si pas de caméra (ton ancien code)
            x_robot, y_robot, theta_robot = shared.robot_pos['x'], shared.robot_pos['y'], shared.robot_pos['theta']
            x = x_robot - math.cos(math.radians(theta_robot)) * 100
            y = y_robot - math.sin(math.radians(theta_robot)) * 100
            self.goto(x, y, theta_robot)
            self.goto(0, 0, 0) # Remplace par tes coo absolues par défaut
            return

        # On fait une boucle d'approche (max 3 tentatives pour ne pas perdre trop de temps)
        for tentative in range(3):
            self._check_abort()
            
            # 1. On regarde si on est déjà bien placé
            in_position = vision_cam.check_aruco_position()
            if in_position:
                print(f"[VISION] Alignement parfait ! (Tentative {tentative+1}/3)")
                break

            # 2. Sinon, on récupère les erreurs
            err_x, err_y, err_angle = vision_cam.get_errors()
            
            if err_x is None or err_y is None:
                print("[VISION] Aucun code ArUco détecté. Impossible de se recaler.")
                break

            print(f"[VISION] Erreurs -> Latéral(X):{err_x:.1f}mm, Profondeur(Y):{err_y:.1f}mm, Angle:{err_angle:.1f}°")

            # 3. Position actuelle de l'odomètrie
            x_actuel = shared.robot_pos['x']
            y_actuel = shared.robot_pos['y']
            theta_actuel = shared.robot_pos['theta']
            theta_rad = math.radians(theta_actuel)

            # 4. Calcul de la CIBLE FINALE ABSOLUE sur la table
            # (err_y = profondeur devant le robot, err_x = décalage latéral gauche/droite)
            # Attention : adapte le signe de err_x et err_y si ton robot part dans le mauvais sens !
            correction_x = (err_y * math.cos(theta_rad)) - (err_x * math.sin(theta_rad))
            correction_y = (err_y * math.sin(theta_rad)) + (err_x * math.cos(theta_rad))
            
            cible_x = x_actuel + correction_x
            cible_y = y_actuel + correction_y
            cible_theta = (theta_actuel + err_angle) % 360

            # 5. LA MANŒUVRE : On recule d'abord pour se dégager (ex: 150 mm)
            recul = 150 
            x_recul = x_actuel - (recul * math.cos(theta_rad))
            y_recul = y_actuel - (recul * math.sin(theta_rad))
            
            print(f"[VISION] Manœuvre : Recul de {recul}mm...")
            self.goto(x_recul, y_recul, theta_actuel, real=True)
            
            # 6. On fonce vers la position parfaite
            print("[VISION] Alignement sur la cible...")
            self.goto(cible_x, cible_y, cible_theta, real=True)
            
            # Petite pause pour que la caméra ne prenne pas une photo floue au prochain tour
            time.sleep(0.5)

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
            
            # On traduit ça en commandes pour les actionneurs
            # (Admettons que FLIP = prendre, nFLIP = ignorer)
            kaplas_decision = ["FLIP" if bon else "nFLIP" for bon in bonnes_couleurs]
            
            # Sécurité au cas où la lecture a foiré
            if len(kaplas_decision) != 4:
                print("[VISION] Erreur : Pas exactement 4 Kaplas détectés, on prend tout par sécurité.")
                kaplas_decision = ["FLIP", "FLIP", "FLIP", "FLIP"]
                
        else:
            print("[VISION/SIMU] Simulation des Kaplas (Caméra non dispo).")
            kaplas_decision = ["nFLIP", "nFLIP", "nFLIP", "nFLIP"]
            
        print(f"[DECISION] Actionneurs : 1={kaplas_decision[0]} | 2={kaplas_decision[1]} | 3={kaplas_decision[2]} | 4={kaplas_decision[3]}")
        
        # Envoi physique aux servos
        self.cmd_actionneurs(
            act1=kaplas_decision[0],
            act2=kaplas_decision[1],
            act3=kaplas_decision[2],
            act4=kaplas_decision[3]
        )
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