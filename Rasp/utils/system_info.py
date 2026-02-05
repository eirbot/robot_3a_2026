import psutil
import socket
import os

# Tente d'importer le vrai capteur, sinon utilise un mode simulation
try:
    # Note le point devant 'sensors' : cela signifie "dans le dossier courant (utils)"
    from .sensors.ina226_reader import INA226
    # On tente d'initialiser (adresse I2C par défaut 0x40)
    voltage_sensor = INA226() 
    SENSOR_AVAILABLE = True
except Exception as e:
    print(f"[SYS] Capteur INA226 non détecté ({e}). Mode Simulation.")
    voltage_sensor = None
    SENSOR_AVAILABLE = False

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return str(round(int(f.read()) / 1000, 1)) + "°C"
    except:
        return "??"

def get_battery_voltage():
    """Retourne la tension réelle ou une valeur simulée"""
    if SENSOR_AVAILABLE and voltage_sensor:
        try:
            # lecture de l'attribut .voltage (mis à jour par le thread INA226)
            return f"{voltage_sensor.voltage:.2f}V"
        except:
            return "Err V"
    else:
        return "12.4V (Simu)"

def get_battery_current():
    """Retourne le courant réel ou une valeur simulée"""
    if SENSOR_AVAILABLE and voltage_sensor:
        try:
            return f"{voltage_sensor.current:.2f}"
        except:
            return "0.00"
    else:
        return "0.50" # Simu