# strat/__init__.py

# Le point . signifie "depuis ce dossier"
from .actions import RobotActions
from .main_strat import strat_loop

# Liste de ce qui est exporté quand on fait "from strat import *"
__all__ = ['RobotActions', 'strat_loop']