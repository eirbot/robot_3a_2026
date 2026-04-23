import smbus2, time, threading, collections # type: ignore

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
        # On lit le Shunt Voltage (0x01) au lieu du Current Register (0x04) 
        # car ce dernier nécessite une calibration complexe.
        # 1 LSB = 2.5 uV. R_shunt = 0.01 Ohm.
        raw = self._read_word(0x01)
        # Conversion du complément à 2 (16 bits)
        if raw > 32767:
            raw -= 65536
            
        shunt_voltage = raw * 2.5e-6 # en Volts
        return shunt_voltage / self.r_shunt

    def _loop(self):
        while not self._stop.is_set():
            try:
                self.voltage = self.read_voltage_once()
                self.current = self.read_current_once()
                self.history.append((time.time(), self.current))
            except Exception:
                pass
            time.sleep(0.05)

    def stop(self):
        self._stop.set()
