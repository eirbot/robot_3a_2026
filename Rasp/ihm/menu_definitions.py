import os, socket, subprocess, psutil
from Rasp.ihm.sensors.ina226_reader import INA226

_ina = INA226(address=0x40, shunt_resistance=0.01)

def _first_or(s, default="N/A"):
    return s.strip().split()[0] if s and s.strip() else default


def get_ip():
    try:
        out = subprocess.check_output(["hostname", "-I"]).decode()
        return _first_or(out, "N/A")
    except Exception:
        return "N/A"


def get_cpu_temp():
    try:
        t = float(open('/sys/class/thermal/thermal_zone0/temp').read())/1000
        return f"{t:.1f} °C"
    except Exception:
        return "N/A"
    

def get_cpu_usage():
    try:
        return f"{psutil.cpu_percent(interval=None):.1f} %"
    except Exception:
        return "N/A"


def get_battery_voltage():
    try:
        return f"{_ina.voltage:.2f} V"
    except Exception:
        return "Erreur capteur"


def get_battery_current():
    try:
        return f"{_ina.current:.2f} A"
    except Exception:
        return "—"


def make_menus(ui):
    return {
        "root": {
            "title": "🏠 Menu principal",
            "items": [
                ("Mode & Équipe", lambda: ui.open_menu("mode")),
                ("Diagnostic I/O", lambda: ui.open_menu("diag")),
                ("Infos système", lambda: ui.open_menu("sys")),
                ("Mode stratégie", lambda: ui.open_menu("strat")),
                ("Arrêt / Reboot", lambda: ui.open_menu("power")),
            ]
        },
        "mode": {
            "title": "⚙️ Mode & Équipe",
            "items": [
                ("Changer équipe", ui.toggle_team),
                ("Basculer Debug", ui.toggle_debug),
                ("Aller au Dashboard", ui.show_dashboard),
                ("Retour", lambda: ui.open_menu("root"))
            ]
        },
        "diag": {
            "title": "🔍 Diagnostic I/O",
            "items": [
                ("Tester LED (respire)", lambda: ui.leds.match_start() if ui.leds else None),
                ("LED Off", lambda: ui.leds.off() if ui.leds else None),
                ("Tester audio (match)", lambda: ui.audio.play("match", loop=True) if ui.audio else None),
                ("Audio stop", lambda: ui.audio.stop() if ui.audio else None),
                ("Tester actionneurs", ui.run_actionneur_test),
                ("Retour", lambda: ui.open_menu("root"))
            ]
        },
        "sys": {
            "title": "📊 Infos système",
            "dynamic": lambda: [
                f"IP : {get_ip()}",
                f"Tension : {get_battery_voltage()}",
                f"Courant : {get_battery_current()}",
                f"CPU Temp : {get_cpu_temp()}",
                f"CPU Usage : {get_cpu_usage()}"
            ],
            "items": [
                ("Voir graphique courant", lambda: ui.open_menu("current")),
                ("Retour", lambda: ui.open_menu("root"))
            ]
        },
        "current": {
            "title": "📈 Graphique courant",
            "items": [
                ("Ouvrir fenêtre graphique", ui.show_current_plot),
                ("Retour", lambda: ui.open_menu("sys"))
            ]
        },
        "strat": {
            "title": "🧠 Mode stratégie",
            "items": [
                ("Lancer match", ui.start_match),
                ("Stopper match", ui.stop_match),
                ("Forcer fin", ui.force_end_match),
                ("Retour", lambda: ui.open_menu("root"))
            ]
        },
        "power": {
            "title": "⏻ Arrêt / Reboot",
            "items": [
                ("Redémarrer", lambda: os.system("sudo reboot")),
                ("Éteindre",   lambda: os.system("sudo shutdown now")),
                ("Retour", lambda: ui.open_menu("root"))
            ]
        }
    }