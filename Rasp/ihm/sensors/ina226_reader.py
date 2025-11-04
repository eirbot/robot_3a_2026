import smbus2, time, threading, collections

class INA226:
    def __init__(self, address=0x40, shunt_resistance=0.01):
        self.addr = address
        self.r_shunt = shunt_resistance
        self.bus = smbus2.SMBus(1)
        self.voltage = 0.0
        self.current = 0.0
        self.history = collections.deque(maxlen=600)  # 600 s = 10 min
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _read_word(self, reg):
        val = self.bus.read_word_data(self.addr, reg)
        return ((val & 0xFF) << 8) | (val >> 8)

    def read_voltage_once(self):
        return self._read_word(0x02) * 1.25e-3  # 1.25 mV/bit

    def read_current_once(self):
        raw = self._read_word(0x04)
        return raw * 0.001  # 1 mA/bit

    def _loop(self):
        while not self._stop.is_set():
            try:
                self.voltage = self.read_voltage_once()
                self.current = self.read_current_once()
                self.history.append((time.time(), self.current))
            except Exception:
                pass
            time.sleep(0.5)

    def stop(self):
        self._stop.set()
