from collections import namedtuple
import numpy as np

ArucoPosition2D = namedtuple("ArucoPosition2D", ["corners", "id"])
RealPosition2D = namedtuple("RealPosition2D", ["x", "y"])

class ArucoMarker:
    def __init__(self, aruco_pos_2d: ArucoPosition2D, pose_3d: RealPosition2D):
        self.aruco_pos = aruco_pos_2d
        self.pose_3d = pose_3d

class RealPosition2D:
    def __init__(self, x: float, y: float):
        self._data = np.array([x, y])
    
    def x(self) -> float:
        return self._data[0]
    
    def y(self) -> float:
        return self._data[1]
    

    # shenanigans to perform (RealPosition2D + np.ndarray) operations
    @classmethod
    def __check_other(cls, other):
        if type(other) != np.ndarray:
            raise ValueError(f"Cannot add/sub RealPosition2D to {type(other)}, only np.array is supported for addition")
        if other.shape != (2,):
            raise ValueError(f"Shape of other object is invalid (shape: {other.shape})")

    def __add__(self, other):
        RealPosition2D.__check_other(other)
        print(self._data)
        return self._data + other
    
    def __sub__(self, other):
        RealPosition2D.__check_other(other)
        return self._data - other