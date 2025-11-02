import json, tkinter as tk
from leds_manager import LedStrip
from audio_manager import AudioManager
from ui_manager import UIManager
from gpio_input import GPIOInput

CONFIG_PATH = 'config.json'

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def main():
    cfg = load_config()
    leds = LedStrip(**cfg.get('leds', {}))
    audio = AudioManager(cfg.get('audio', {}))

    root = tk.Tk()
    ui = UIManager(root, leds, audio, cfg)
    gpio = GPIOInput(cfg.get('gpio', {}), ui)

    # Musique d'intro (pré‑match)
    if audio: audio.play('intro')

    try:
        root.mainloop()
    finally:
        try: gpio.close()
        except Exception: pass
        try: leds.off()
        except Exception: pass
        try: audio.stop()
        except Exception: pass

if __name__ == '__main__':
    main()