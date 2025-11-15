#!/usr/bin/env python3
import sys, time
from rpi_ws281x import PixelStrip, Color # type: ignore

# === Config ===
LED_COUNT = 60
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 128
LED_CHANNEL = 0

TEAM_COLORS = {
    "BLEUE": (0, 0, 255),
    "JAUNE": (255, 160, 0)
}
RED = (255, 0, 0)
PURPLE = (128, 0, 128)
WHITE = (255, 255, 255)


def set_color(strip, rgb):
    """Allume toutes les LED avec la couleur donnée"""
    r, g, b = rgb
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(r, g, b))
    strip.show()


def blink_once(strip, rgb, n=4, delay=0.5):
    """Petit clignotement lent (optionnel)"""
    for _ in range(n):
        set_color(strip, rgb)
        time.sleep(delay)
        set_color(strip, (0, 0, 0))
        time.sleep(delay)
    set_color(strip, rgb)


def main():
    args = sys.argv[1:]
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, False, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    if not args:
        print("Usage: led_service.py <MODE> [team]")
        return

    mode = args[0].lower()

    if mode == "team":
        team = args[1].upper() if len(args) > 1 else "BLEUE"
        set_color(strip, TEAM_COLORS.get(team, TEAM_COLORS["BLEUE"]))
    elif mode == "debug":
        set_color(strip, PURPLE)
    elif mode == "error":
        set_color(strip, RED)
    elif mode == "stop":
        blink_once(strip, WHITE)
    elif mode == "off":
        set_color(strip, (0, 0, 0))
    else:
        print("Unknown mode:", mode)


if __name__ == "__main__":
    main()
