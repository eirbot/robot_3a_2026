#!/usr/bin/env python3
import time
import socket
import os
import signal
import sys
import math
import board
import adafruit_dotstar

import json
import threading

# === CONFIG ===
LED_COUNT = 288
# Pins are implicitly board.SCK (GPIO 11) and board.MOSI (GPIO 10) for RPi 4 SPI
LED_BRIGHTNESS = 0.1 # 0.0 to 1.0 for DotStar
SOCKET_PATH = "/tmp/ledsock"
ANIMATIONS_FILE = os.path.join(os.path.dirname(__file__), '..', 'config_led_animations.json')

class LedServer:
    def __init__(self):
        try:
            self.strip = adafruit_dotstar.DotStar(
                board.SCK, 
                board.MOSI, 
                LED_COUNT, 
                brightness=LED_BRIGHTNESS, 
                auto_write=False,
                baudrate=1000000
            )
            self.running = True
            print("[LED] DotStar Strip Initialized")
        except Exception as e:
            print(f"[LED] Erreur d'initialisation du bandeau : {e}")
            self.running = False

        # Nettoyage socket
        if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.server.bind(SOCKET_PATH)
        os.chmod(SOCKET_PATH, 0o666)
        
        # Animations
        self.animations = {}
        self.load_animations()
        self.current_anim_thread = None
        self.stop_anim_flag = False

        print(f"[LED] Service démarré sur {SOCKET_PATH}")
        self.pixels = [(0, 0, 0)] * LED_COUNT
        self.clear()

    def load_animations(self):
        try:
            if os.path.exists(ANIMATIONS_FILE):
                with open(ANIMATIONS_FILE, 'r') as f:
                    self.animations = json.load(f)
                print(f"[LED] Chargé {len(self.animations)} animations.")
            else:
                self.animations = {}
        except Exception as e:
            print(f"[LED] Erreur chargement animations: {e}")

    def stop_current_anim(self):
        self.stop_anim_flag = True
        if self.current_anim_thread and self.current_anim_thread.is_alive():
            self.current_anim_thread.join(timeout=0.2)
        self.stop_anim_flag = False

    def clear(self):
        self.stop_current_anim()
        if not self.running: return
        self.pixels = [(0, 0, 0)] * LED_COUNT
        self.strip.fill((0, 0, 0))
        self.strip.show()

    def set_all(self, r, g, b):
        self.stop_current_anim()
        if not self.running: return
        # DotStar expects (r, g, b) tuple
        self.pixels = [(r, g, b)] * LED_COUNT
        self.strip.fill((r, g, b))
        self.strip.show()

    def gradient(self, r1, g1, b1, r2, g2, b2):
        """Applique un dégradé linéaire du début à la fin du bandeau"""
        self.stop_current_anim()
        if not self.running: return
        n = LED_COUNT
        for i in range(n):
            ratio = i / float(n - 1)
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)
            self.pixels[i] = (r, g, b)
            self.strip[i] = (r, g, b)
        self.strip.show()

    def handle_command(self, data):
        raw_cmd = data.decode('utf-8').strip()
        cmd = raw_cmd.upper()
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

        elif cmd.startswith("ANIM:BREATH"):
             # Ex: ANIM:BREATH:0,255,0
             try:
                 parts = cmd.split(":")
                 if len(parts) >= 3:
                     vals = parts[2].split(",")
                     self.anim_breathe((int(vals[0]), int(vals[1]), int(vals[2])))
                 else:
                     self.anim_breathe() # Default Cyan
             except: self.anim_breathe()

        elif cmd.startswith("ANIM:"):
            # Ex: ANIM:RAINBOW
            anim = cmd.split(":")[1]
            if anim == "RAINBOW": self.anim_rainbow()
            elif anim == "FLASH": self.anim_flash()

        elif cmd.startswith("PIXEL:"):
            # Ex: PIXEL:12,255,0,0
            try:
                parts = cmd.split(":")[1].split(",")
                idx = int(parts[0])
                if 0 <= idx < LED_COUNT:
                    color = (int(parts[1]), int(parts[2]), int(parts[3]))
                    self.pixels[idx] = color
                    self.strip[idx] = color
                    self.strip.show()
            except: pass

        elif cmd.startswith("TEAM:"):
            team = cmd.split(":")[1]
            if team == "JAUNE": self.set_all(255, 160, 0)
            else: self.set_all(0, 0, 255) # BLEUE
            
        elif cmd.startswith("PLAY:"):
            # Ex: PLAY:match_start
            # Use raw_cmd to preserve case sensitivity of the animation name
            try:
                anim_name = raw_cmd.split(":", 1)[1]
                self.play_animation(anim_name)
            except IndexError: pass

        elif cmd == "RELOAD":
            self.load_animations()

        elif cmd == "MATCH_START": self.set_all(0, 255, 0) # Vert
        elif cmd == "MATCH_STOP": self.set_all(255, 255, 255) # Blanc
        elif cmd.startswith("BRIGHTNESS:"):
            # Ex: BRIGHTNESS:0.5
            try:
                val = float(cmd.split(":")[1])
                val = max(0.0, min(1.0, val)) # Clamp 0.0-1.0
                self.strip.brightness = val
                
                # IMPORTANT : DotStar n'applique la luminosité qu'au moment du SET du pixel.
                # Il faut donc réappliquer tout le cache (self.pixels) vers le strip.
                for i, p in enumerate(self.pixels):
                    self.strip[i] = p
                
                self.strip.show()
            except: pass

        elif cmd == "DEBUG": self.set_all(128, 0, 128) # Violet

    def play_animation(self, name):
        if name not in self.animations:
            print(f"[LED] Animation inconnue: {name}")
            return
            
        self.stop_current_anim()
        self.stop_anim_flag = False
        self.current_anim_thread = threading.Thread(target=self._run_animation, args=(self.animations[name],))
        self.current_anim_thread.start()

    def _run_animation(self, anim_data):
        steps = anim_data.get('steps', [])
        loop = anim_data.get('loop', False)
        
        while not self.stop_anim_flag:
            for step in steps:
                if self.stop_anim_flag: return
                
                duration = step.get('duration', 1.0)
                transition = step.get('transition', 'NONE')
                target_pixels = step.get('pixels', [])
                
                # Conversion data -> [(r,g,b), ...]
                # Use local cache COPY instead of self.strip[:]
                current_pixels = list(self.pixels)
                
                target_colors = []
                for i in range(LED_COUNT):
                    if i < len(target_pixels):
                        c = target_pixels[i]
                        if isinstance(c, list) and len(c) == 3: target_colors.append(tuple(c))
                        else: target_colors.append((0,0,0))
                    else:
                        target_colors.append((0,0,0))

                # TRANSITION
                if transition == "FADE" and duration > 0.1:
                    steps_fade = int(duration * 30) # 30hz
                    if steps_fade < 1: steps_fade = 1
                    
                    for s in range(steps_fade):
                        if self.stop_anim_flag: return
                        alpha = (s + 1) / steps_fade
                        for i in range(LED_COUNT):
                            r1, g1, b1 = current_pixels[i]
                            r2, g2, b2 = target_colors[i]
                            nr = int(r1 + (r2 - r1) * alpha)
                            ng = int(g1 + (g2 - g1) * alpha)
                            nb = int(b1 + (b2 - b1) * alpha)
                            self.pixels[i] = (nr, ng, nb)
                            self.strip[i] = (nr, ng, nb)
                        self.strip.show()
                        time.sleep(duration / steps_fade)
                else:
                    # Instant
                    self.pixels = list(target_colors) # Update cache fully
                    for i in range(LED_COUNT):
                        self.strip[i] = self.pixels[i]
                    self.strip.show()
                    time.sleep(duration)
            
            if not loop: break

    def anim_rainbow(self):
        """Affiche un arc-en-ciel statique"""
        n = LED_COUNT
        for i in range(n):
            hue = i / n
            rgb = self.hsv_to_rgb(hue, 1.0, 1.0)
            self.pixels[i] = rgb
            self.strip[i] = rgb
        self.strip.show()

    def anim_flash(self):
        """Flash Blanc rapide"""
        for _ in range(3):
            self.set_all(255, 255, 255)
            time.sleep(0.1)
            self.clear()
            time.sleep(0.1)

    def anim_breathe(self, color=(0, 128, 128)):
        """Simulation respiration (Couleur par argument, defaut Cyan)"""
        import math
        r_max, g_max, b_max = color
        for i in range(0, 360, 5): # Cycle complet
            if self.stop_anim_flag: return
            
            # Sinus entre 0.1 et 1.0
            factor = (math.sin(math.radians(i)) + 1) / 2 # 0..1
            factor = 0.1 + 0.9 * factor # 0.1 .. 1.0 (ne s'éteint pas complètement)
            
            r = int(r_max * factor)
            g = int(g_max * factor)
            b = int(b_max * factor)
            
            self.set_all(r, g, b) 
            time.sleep(0.02)

    def hsv_to_rgb(self, h, s, v):
        """Utils: Conversion HSV [0..1] vers RGB [0..255]"""
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        i %= 6
        if i == 0: r, g, b = v, t, p
        elif i == 1: r, g, b = q, v, p
        elif i == 2: r, g, b = p, v, t
        elif i == 3: r, g, b = p, q, v
        elif i == 4: r, g, b = t, p, v
        elif i == 5: r, g, b = v, p, q
        return (int(r * 255), int(g * 255), int(b * 255))

    def run(self):
        try:
            while self.running:
                data, _ = self.server.recvfrom(1024)
                if data: self.handle_command(data)
        except KeyboardInterrupt: pass
        finally: 
            if self.running: self.clear()
            self.server.close()
            if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)

if __name__ == "__main__":
    srv = LedServer()
    def handler(s, f): srv.running = False; sys.exit(0)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    srv.run()