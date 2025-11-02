try:
    from gpiozero import Button
except Exception:
    Button = None

class GPIOInput:
    def __init__(self, cfg_gpio: dict, ui):
        self.enabled = bool(cfg_gpio.get("use_buttons", True)) and Button is not None
        self.ui = ui
        self.buttons = {}
        if not self.enabled:
            return
        pins = cfg_gpio.get("pins", {})
        self._add(pins.get("UP"), ui.nav_up)
        self._add(pins.get("DOWN"), ui.nav_down)
        self._add(pins.get("SELECT"), ui.nav_select)
        self._add(pins.get("BACK"), ui.nav_back)
        self._add(pins.get("START"), ui.start_match)
        self._add(pins.get("STOP"), ui.stop_match)

    def _add(self, pin, callback):
        if pin is None:
            return
        b = Button(pin, pull_up=False, bounce_time=0.08)
        b.when_pressed = callback
        self.buttons[pin] = b

    def close(self):
        for b in self.buttons.values():
            try: b.close()
            except Exception: pass