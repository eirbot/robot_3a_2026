import time
import logging

import cv2 as cv
import numpy as np
from marker_map import NutCases
from aruco import *

class NutCaseArucoDetector:
    """Nutcase aruco detector (wrapper on cv.aurco.ArucoDetector with some utilitaries)"""

    ARUCO_DICT = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_100)

    def __init__(self):
        self._detector = cv.aruco.ArucoDetector(
            dictionary=NutCaseArucoDetector.ARUCO_DICT,
            detectorParams=cv.aruco.DetectorParameters(),
            refineParams=cv.aruco.RefineParameters() # optional?
        )
        self._logger = logging.getLogger("ArUco")

    def find_markers(self, frame: cv.Mat) -> list[ArucoPosition2D]:
        """On an image, returns a list of on-image ArUco marker corners and their ID"""
        t_start = time.time()
        
        # ignoring rejected image points (we don't use it anyway)
        corners, ids, _ = self._detector.detectMarkers(frame)
        self._logger.info(f"Number of detected IDs : {len(ids)}")

        elapsed = time.time() - t_start
        self._logger.debug(f"Marker detection time : {elapsed}")

        aruco_pos_2d_list = map(
            lambda c, i: ArucoPosition2D(c, i),
            zip(corners, ids)
        )

        return corners, ids
    
    def marker_to_real_pos(image: cv.Mat, aruco_pose: ArucoPosition2D) -> RealPosition2D:
        """Maps a given 2D ArUco marker position into its relative 3D position in the robot frame"""
        CAMERA_POSE_OFFSET = np.array([0., 0.])
        # todo
        return RealPosition2D(0, 0, 0)
        


if __name__ == '__main__':
    WINDOW_NAME = "win"
    cv.namedWindow(WINDOW_NAME, cv.WINDOW_NORMAL)
    filled_blue_nutcase_img = cv.aruco.generateImageMarker(NutCaseArucoDetector.ARUCO_DICT, 
                                              id=NutCases.FILLED_BLUE.value, # Aruco ID
                                              sidePixels=200) # Image size in pixels
    cv.imshow(WINDOW_NAME, filled_blue_nutcase_img)
    cv.waitKey(-1)

    detector = NutCaseArucoDetector()

    img = cv.imread("test_data/non.jpg")
    corners, ids = detector.find_markers(img)
    print(f"IDs : {ids.T}")
    print(f"Corners : {len(corners)}")
    
    highlighted = cv.aruco.drawDetectedMarkers(img, corners, ids)
    cv.imshow(WINDOW_NAME, highlighted)
    cv.waitKey(-1)