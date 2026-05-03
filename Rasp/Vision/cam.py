import sys
import cv2
import os
os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts/truetype/ubuntu'
    
class cam:
    def __init__(self, image_path=None, use_camera=False):
        self.use_camera = use_camera
        self.largeur_cible = 800 # largeur de l'image en pixels
        self.tolerance_position = 15 # pixels
        self.tolerance_angle = 8  # degres

        if self.use_camera:
            self.image_reduite = None
            self.dimension = None
        else:
            image = cv2.imread(image_path)
            ratio = self.largeur_cible / image.shape[1]
            self.dimension = (self.largeur_cible, int(image.shape[0] * ratio))
            self.image_reduite = cv2.resize(image, self.dimension, interpolation=cv2.INTER_AREA)

        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

        self.max_angle = None
        self.err_x = None
        self.err_y = None


    def check_aruco_position(self):

        self.everything_in_position = True

        self.allowed_zones = [(254, 288), (358, 288), (464, 288), (570, 288)] # toutes les valeurs sont mesurees pour 800 px de large

        angles = []
        self.aruco_center_positions = []

        if self.use_camera:
            image = self.capture_image()
            ratio = self.largeur_cible / image.shape[1]
            self.dimension = (self.largeur_cible, int(image.shape[0] * ratio))
            self.image_reduite = cv2.resize(image, self.dimension, interpolation=cv2.INTER_AREA)
        
        self.corners, self.ids, rejected = self.detector.detectMarkers(self.image_reduite)

        if self.ids is not None:
            for i in range(len(self.ids)):
                aruco_center_position = (self.corners[i][0][0] + self.corners[i][0][1] + self.corners[i][0][2] + self.corners[i][0][3]) / 4
                self.aruco_center_positions.append(aruco_center_position)
                if not any(abs(aruco_center_position[0] - zone[0]) <= self.tolerance_position and abs(aruco_center_position[1] - zone[1]) <= self.tolerance_position for zone in self.allowed_zones):
                    self.everything_in_position = False
                pt1 = tuple(map(int, self.corners[i][0][0]))
                pt2 = tuple(map(int, self.corners[i][0][1]))
                angle = cv2.fastAtan2(abs(pt2[1] - pt1[1]), abs(pt2[0] - pt1[0])) - 90
                angles.append(angle)


            self.max_angle = max(abs(angle) for angle in angles)
            if (self.max_angle) > self.tolerance_angle:
                self.everything_in_position = False

        else:
            self.everything_in_position = False

        return self.everything_in_position

    def capture_image(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError('Unable to open camera')
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise RuntimeError('Unable to capture image from camera')
        return frame
    
    def get_colors(self, equipe):
        self.sorted_ids = [id for _, id in sorted(zip([pos[0] for pos in self.aruco_center_positions], self.ids.flatten()))]
        if equipe == "jaune":
            return [id == 47 for id in self.sorted_ids]
        else:
            return [id == 36 for id in self.sorted_ids]
        
    def is_salvagable(self):
        # this function checks if the aruco codes are aligned with each other and that this alignment is roughly perpendicular to the angle of the aruco codes
        if self.ids is None:
            return False
        sorted_positions = sorted(self.aruco_center_positions, key=lambda pos: pos[0])
        alignment_angle = cv2.fastAtan2(abs(sorted_positions[-1][1] - sorted_positions[0][1]), abs(sorted_positions[-1][0] - sorted_positions[0][0])) - 90
        cv2.line(self.image_reduite, (int(sorted_positions[0][0]), int(sorted_positions[0][1])), (int(sorted_positions[-1][0]), int(sorted_positions[-1][1])), (255, 0, 0), 2)
        marker_angle = cv2.fastAtan2(abs(self.corners[0][0][1][1] - self.corners[0][0][0][1]), abs(self.corners[0][0][1][0] - self.corners[0][0][0][0])) - 90
        print(f"Alignment angle: {alignment_angle}")
        print(f"Marker angle: {marker_angle}")
        print(f"Difference: {abs(alignment_angle - marker_angle)}")
        if abs(abs(alignment_angle - marker_angle) - 90) > 20:
            return False
        return True

    def get_errors(self):
        if self.ids is None:
            return None, None, None
        
        main_center_position = (414, 290)
        avg_y = sum([pos[0] for pos in self.aruco_center_positions]) / len(self.aruco_center_positions)
        avg_x = sum([pos[1] for pos in self.aruco_center_positions]) / len(self.aruco_center_positions)
        px_to_mm = 30/56.5 # 56.5 px correspond a 30 mm dans la realite
        self.err_x = -(avg_x-main_center_position[1]) * px_to_mm
        self.err_y = -(avg_y-main_center_position[0]) * px_to_mm
        return self.err_x, self.err_y, self.max_angle
    
    def get_image(self):
        if self.ids is not None:
            for i in range(len(self.ids)):
                pt1 = tuple(map(int, self.corners[i][0][0]))
                pt2 = tuple(map(int, self.corners[i][0][1]))
                cv2.line(self.image_reduite, pt1, pt2, (0, 255, 0), 3)
                cv2.circle(self.image_reduite, (int(self.aruco_center_positions[i][0]), int(self.aruco_center_positions[i][1])), 5, (0, 255, 0), -1)
            for zone in self.allowed_zones:
                cv2.rectangle(self.image_reduite, (zone[0] - self.tolerance_position, zone[1] - self.tolerance_position), (zone[0] + self.tolerance_position, zone[1] + self.tolerance_position), (0, 255, 255), 2)
        
        cv2.aruco.drawDetectedMarkers(self.image_reduite, self.corners, self.ids)

        if self.everything_in_position:
            cv2.putText(self.image_reduite, 'OK', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        else:
            cv2.putText(self.image_reduite, 'PAS OK', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # writes angle in top left
        if self.max_angle is not None:
            cv2.putText(self.image_reduite, f'Max angle: {self.max_angle:.2f}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        # writes average x and y position of centers in top left
        # if self.everything_in_position:
        self.get_errors()
        if self.err_x is not None and self.err_y is not None:
            cv2.putText(self.image_reduite, f'Avg err : X {self.err_x:.2f}, Y {self.err_y:.2f}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        # prints a reference in the bottom right corner, x is an arrow pointing up and y is an arrow pointing left
        cv2.arrowedLine(self.image_reduite, (self.dimension[0] - 20, self.dimension[1] - 20), (self.dimension[0] - 20, self.dimension[1] - 70), (255, 255, 255), 2)
        cv2.arrowedLine(self.image_reduite, (self.dimension[0] - 20, self.dimension[1] - 20), (self.dimension[0] - 70, self.dimension[1] - 20), (255, 255, 255), 2)
        cv2.putText(self.image_reduite, 'X', (self.dimension[0] - 30, self.dimension[1] - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(self.image_reduite, 'Y', (self.dimension[0] - 80, self.dimension[1] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return self.image_reduite






cam = cam('logs/oui2.jpg')
# cam = cam(use_camera=True)

in_position = cam.check_aruco_position()
if in_position:
    colors = cam.get_colors("bleu")
    print("Colors in order : ")
    print(colors)
else:
    # if cam.is_salvagable():
    x_error, y_error, angle_error = cam.get_errors()
    print("X error : ", x_error)
    print("Y error : ", y_error)
    print("Angle error : ", angle_error)

img = cam.get_image()
cv2.imshow('Detection ArUco - Format Reduit', img)
cv2.waitKey(0)
cv2.destroyAllWindows()