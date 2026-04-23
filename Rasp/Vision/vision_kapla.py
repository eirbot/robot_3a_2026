import cv2
import cv2.aruco as aruco
import numpy as np

class KaplaVision:
    """
    Module de vision basé sur OpenCV et ArUco pour vérifier l'orientation des kaplas.
    Utilise une instance de Picamera2 (LibCamera) en flux BGR.
    """
    def __init__(self, camera=None):
        self.camera = camera
        
        # Le dictionnaire 4x4 est classique pour les robots (DICT_4X4_50)
        try:
            self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
            self.aruco_params = aruco.DetectorParameters()
            # Dans OpenCV >= 4.7
            self.detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        except AttributeError:
            # OpenCV plus ancien (< 4.7)
            self.aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
            self.aruco_params = aruco.DetectorParameters_create()
            self.detector = None
        
        print("[VISION] Détecteur ArUco initialisé.")

    def detect_kaplas_orientation(self, team_yellow=True):
        """
        Lit une image depuis la caméra, détecte les ArUco, 
        et détermine la nécessité (FLIP/nFLIP) de gauche à droite
        en fonction de l'équipe actuelle du robot.
        """
        decisions = ["nFLIP", "nFLIP", "nFLIP", "nFLIP"]
        
        if not self.camera:
            print("[VISION] Erreur: Aucune référence vers la caméra.")
            return decisions
            
        status, frame = self.camera.read()
        if not status or frame is None:
            print("[VISION] Erreur: Impossible de lire la frame depuis la caméra.")
            return decisions

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Détection des marqueurs
        if self.detector:
            corners, ids, rejected = self.detector.detectMarkers(gray)
        else:
            corners, ids, rejected = aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)

        if ids is not None and len(ids) > 0:
            markers = []
            for i in range(len(ids)):
                # Calculer le centre (moyenne X des 4 coins) du marqueur
                c = corners[i][0]
                center_x = (c[0][0] + c[1][0] + c[2][0] + c[3][0]) / 4.0
                marker_id = int(ids[i][0])
                markers.append((center_x, marker_id))
            
            # Trier de gauche à droite sur l'image
            markers.sort(key=lambda m: m[0])
            print(f"[VISION] {len(markers)} kapla(s) détecté(s). IDs (G->D): {[m[1] for m in markers]}")
            
            for i in range(min(4, len(markers))):
                m_id = markers[i][1]
                
                # IMPORTANT: Personnaliser ici la reconnaissance des Faces
                # Exemple : on part du principe que la face JAUNE porte un ID PAIR.
                # Et que la face BLEU porte un ID IMPAIR.
                is_face_yellow = (m_id % 2 == 0)
                
                if team_yellow:
                    # On est l'équipe JAUNE. 
                    # Si la caméra voit la face JAUNE -> le kapla est déjà bon (nFLIP).
                    # Si elle voit la face BLEU -> on le retourne (FLIP).
                    decisions[i] = "nFLIP" if is_face_yellow else "FLIP"
                else:
                    # On est l'équipe BLEU.
                    # Si la caméra voit la face JAUNE -> il faut retourner (FLIP).
                    # Si elle voit BLEU -> déjà bon (nFLIP).
                    decisions[i] = "FLIP" if is_face_yellow else "nFLIP"
        else:
            print("[VISION] /!\\ Image capturée, mais aucun marqueur ArUco visible !")

        return decisions
