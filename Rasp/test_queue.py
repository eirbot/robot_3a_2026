import interface_deplacement.interface_deplacement as inter_dep
import numpy as np

inter_dep.init()

msg = np.array([[1,2], [3,4]]).tolist()
print(f"msg type: {type(msg)}")
print(f"isinstance: {isinstance(msg, (list, np.ndarray))}")

