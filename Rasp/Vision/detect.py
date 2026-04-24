import cv2 as cv
from marker_map import NutCases

if __name__ == '__main__':
    d = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_100)
    filled_blue_nutcase_img = cv.aruco.generateImageMarker(d, 
                                              id=NutCases.FILLED_BLUE.value, # Aruco ID
                                              sidePixels=200) # Image size in pixels
    cv.imshow("win", filled_blue_nutcase_img)
    cv.waitKey(-1)

    detector = cv.aruco.ArucoDetector(
        dictionary=d,
        detectorParams=cv.aruco.DetectorParameters(),
        refineParams=cv.aruco.RefineParameters() # optional?
    )

    corners, ids, rejectedImgPoints = detector.detectMarkers()
    
    cv.aruco.drawDetectedMarkers()