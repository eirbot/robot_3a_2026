import RPi.GPIO as GPIO
import os
import time
import subprocess

# PIN correspondant au Bouton 3 (PIN_REBOOT dans buttons_thread.py)
PIN_BUTTON_3 = 15  # Mode BOARD

# Chemin vers les scripts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXEC_SCRIPT = os.path.join(BASE_DIR, "exec.sh")
STOP_SCRIPT = os.path.join(BASE_DIR, "stop.sh")
LOG_FILE = "/home/eirbot/launcher_debug.log"

# Log de démarrage immédiat pour test
with open(LOG_FILE, "a") as f:
    f.write(f"\n[SYSTEM] Launcher démarré à {time.ctime()}\n")

def get_robot_status():
    """Vérifie si le processus main_robot.py est en cours d'exécution."""
    try:
        # pgrep -f cherche le nom complet de la commande
        subprocess.check_output(["pgrep", "-f", "main_robot.py"])
        return True
    except subprocess.CalledProcessError:
        return False

def toggle_robot(channel):
    """Lance ou arrête le robot selon son état actuel."""
    # Petit délai pour éviter les rebonds résiduels
    time.sleep(0.05)
    if GPIO.input(PIN_BUTTON_3) != 0:
        return

    print("[LAUNCHER] Bouton 3 détecté !")
    
    if get_robot_status():
        print("[LAUNCHER] Le robot tourne déjà -> Arrêt...")
        subprocess.run(["/bin/bash", STOP_SCRIPT])
    else:
        print("[LAUNCHER] Le robot est arrêté -> Démarrage...")
        env = os.environ.copy()
        # On log tout ce qui sort dans un fichier de debug
        log_file = open("/home/eirbot/launcher_debug.log", "a")
        log_file.write(f"\n--- Démarrage le {time.ctime()} ---\n")
        subprocess.Popen(["/bin/bash", EXEC_SCRIPT], 
                         stdout=log_file, 
                         stderr=log_file,
                         start_new_session=True,
                         env=env)

# Configuration GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN_BUTTON_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Détection de l'appui (Front descendant car pull-up interne)
# bouncetime de 500ms pour éviter les doubles appuis accidentels
GPIO.add_event_detect(PIN_BUTTON_3, GPIO.FALLING, callback=toggle_robot, bouncetime=800)

print(f"[LAUNCHER] Service prêt. Écoute sur le PIN {PIN_BUTTON_3} (Bouton 3).")
print(f"[LAUNCHER] Script Exec: {EXEC_SCRIPT}")
print(f"[LAUNCHER] Script Stop: {STOP_SCRIPT}")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("[LAUNCHER] Arrêt du service.")
    GPIO.cleanup()
