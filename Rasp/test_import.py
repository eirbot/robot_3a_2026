import sys
sys.path.append('/home/guig/Documents/Eirbot/robot_3a_2026/Rasp')
import traceback

try:
    import interface_deplacement.bezier as Bezier
    print("Imported Bezier successfully!")
except Exception as e:
    print("FAILED to import bezier:")
    traceback.print_exc()

try:
    from interface_deplacement.interface_deplacement import envoyer
    print("Imported envoyer successfully!")
except Exception as e:
    print("FAILED to import envoyer:")
    traceback.print_exc()
