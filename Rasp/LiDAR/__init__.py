"""
Module LiDAR & Navigation
Gère la communication avec le capteur, l'odométrie et la fusion de données (EKF).
"""

# On importe les classes spécifiques depuis les fichiers du même dossier
from .ekf_localizer import EKFLocalizer
from .navigation_manager import NavigationManager
from .debug_map import MapVisualizer

# __all__ définit ce qui est exporté si quelqu'un fait `from LiDAR import *`
__all__ = [
    'EKFLocalizer',
    'NavigationManager',
    'MapVisualizer'
]