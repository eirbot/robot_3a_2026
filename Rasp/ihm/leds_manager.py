import time
import threading
try:
    from rpi_ws281x import PixelStrip, Color
except Exception:
    PixelStrip = None
    def Color(r, g, b): return (r, g, b)

TEAM_COLORS = {
    "BLEUE": (0, 80, 255),
    "JAUNE": (255, 160, 0)
}
WHITE, RED, PURPLE = (255,255,255), (255,0,0), (120,0,160)

class LedStrip:
    def __init__(self, enabled=True, num_leds=60, pin_pwm=18, brightness=128, **_):
        self.enabled = enabled and PixelStrip is not None
        self.num_leds = num_leds
        self._stop = threading.Event()
        self._thread = None
        self._base_color = TEAM_COLORS["BLEUE"]
        if self.enabled:
            self.strip = PixelStrip(num_leds, pin_pwm, 800000, 10, False, brightness, 0)
            self.strip.begin()
        else:
            self.strip = None

    def _set_all(self, rgb):
        if not self.enabled: return
        c = Color(*rgb)
        for i in range(self.num_leds):
            self.strip.setPixelColor(i, c)
        self.strip.show()

    def _anim(self, func):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._stop.clear()
        self._thread = threading.Thread(target=func, daemon=True)
        self._thread.start()

    def _breathe(self):
        import math
        t = 0.0
        while not self._stop.is_set():
            k = 0.6 + 0.4 * (math.sin(t) * 0.5 + 0.5)
            self._set_all(tuple(int(c * k) for c in self._base_color))
            t += 0.1
            time.sleep(0.05)

    def _blink(self, color, period):
        on = True
        while not self._stop.is_set():
            self._set_all(color if on else (0,0,0))
            on = not on
            time.sleep(period)

    def off(self):
        self._stop.set()
        self._set_all((0,0,0))

    def set_team(self, team):
        self._base_color = TEAM_COLORS.get(team.upper(), TEAM_COLORS["BLEUE"])
        self._stop.set()
        self._set_all(self._base_color)

    def set_debug(self, on):
        self._stop.set()
        self._set_all(PURPLE if on else self._base_color)

    def set_error(self, on):
        if on: self._anim(lambda: self._blink(RED, 0.2))
        else: self._stop.set(); self._set_all(self._base_color)

    def match_start(self):
        self._anim(self._breathe)

    def match_stop(self):
        self._anim(lambda: self._blink(WHITE, 0.4))
        threading.Timer(3, self._stop.set).start()