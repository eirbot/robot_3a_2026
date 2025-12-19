#!/usr/bin/env python3
import time
import socket
import os
import signal
import sys
import math
from rpi_ws281x import PixelStrip, Color

# === CONFIG ===
LED_COUNT = 60
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 128
LED_CHANNEL = 0
SOCKET_PATH = "/tmp/ledsock"

class LedServer:
    def __init__(self):
        self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, False, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        self.running = True
        
        # Nettoyage socket
        if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.server.bind(SOCKET_PATH)
        os.chmod(SOCKET_PATH, 0o666)
        
        print(f"[LED] Service démarré sur {SOCKET_PATH}")
        self.clear()

    def clear(self):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0,0,0))
        self.strip.show()

    def set_all(self, r, g, b):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(r, g, b))
        self.strip.show()

    def gradient(self, r1, g1, b1, r2, g2, b2):
        """Applique un dégradé linéaire du début à la fin du bandeau"""
        n = self.strip.numPixels()
        for i in range(n):
            ratio = i / float(n - 1)
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)
            self.strip.setPixelColor(i, Color(r, g, b))
        self.strip.show()

    def handle_command(self, data):
        cmd = data.decode('utf-8').strip().upper()
        # Format attendu : "CMD:ARG1,ARG2..."
        
        if cmd == "OFF":
            self.clear()
            
        elif cmd.startswith("COLOR:"):
            # Ex: COLOR:255,0,0
            try:
                parts = cmd.split(":")[1].split(",")
                self.set_all(int(parts[0]), int(parts[1]), int(parts[2]))
            except: pass
            
        elif cmd.startswith("GRADIENT:"):
            # Ex: GRADIENT:255,0,0,0,0,255 (Rouge vers Bleu)
            try:
                p = cmd.split(":")[1].split(",")
                self.gradient(int(p[0]), int(p[1]), int(p[2]), int(p[3]), int(p[4]), int(p[5]))
            except: pass

        elif cmd.startswith("TEAM:"):
            team = cmd.split(":")[1]
            if team == "JAUNE": self.set_all(255, 160, 0)
            else: self.set_all(0, 0, 255) # BLEUE
            
        elif cmd == "MATCH_START": self.set_all(0, 255, 0) # Vert
        elif cmd == "MATCH_STOP": self.set_all(255, 255, 255) # Blanc
        elif cmd == "DEBUG": self.set_all(128, 0, 128) # Violet

    def run(self):
        try:
            while self.running:
                data, _ = self.server.recvfrom(1024)
                if data: self.handle_command(data)
        except KeyboardInterrupt: pass
        finally: 
            self.clear()
            self.server.close()
            if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)

if __name__ == "__main__":
    srv = LedServer()
    def handler(s, f): srv.running = False; sys.exit(0)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    srv.run()