import os, socket, subprocess

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


def get_battery_voltage():
    # Adapter selon ton capteur (ADC/I2C). Placeholder :
    path_candidates = [
        "/sys/class/power_supply/battery/voltage_now",
        "/sys/class/power_supply/axp20x-battery/voltage_now"
    ]
    for p in path_candidates:
        try:
            return f"{int(open(p).read())/1e6:.2f} V"
        except Exception:
            pass
    return "Inconnue"


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
            # dynamic(): lignes informatives non‑sélectionnables
            "dynamic": lambda: [
                f"IP : {get_ip()}",
                f"CPU Temp : {get_cpu_temp()}",
                f"Batterie : {get_battery_voltage()}",
                f"Équipe : {ui.state.team}",
                f"Score objectif : {ui.state.score_target}",
                f"Score courant : {ui.state.score_current}"
            ],
            "items": [
                ("Retour", lambda: ui.open_menu("root"))
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