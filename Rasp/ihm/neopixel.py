# neopixel.py — version SPI pour WS2811 12V (par Ziagl)
# https://github.com/Ziagl/raspberry-pi-ws2811
import math, time

class NeoPixel:
    def __init__(self, n, spi, freq_hz=2400000, invert=False):
        self.n = n
        self.spi = spi
        self.spi.max_speed_hz = freq_hz
        self.buf = [(0, 0, 0)] * n

    def __setitem__(self, i, color):
        if isinstance(i, slice):
            indices = range(*i.indices(self.n))
            for j in indices:
                self.buf[j] = color
        else:
            self.buf[i] = color

    def __getitem__(self, i):
        return self.buf[i]

    def fill(self, color):
        for i in range(self.n):
            self.buf[i] = color

    def _encode_byte(self, b):
        """Encode 1 octet en 24 bits SPI (3 bits par bit WS2811)."""
        bits = []
        for i in range(8):
            if (b << i) & 0x80:
                bits += [1, 1, 0]  # "1" WS2811
            else:
                bits += [1, 0, 0]  # "0" WS2811
        return bits

    def _encode_color(self, color):
        r, g, b = color
        bits = []
        for c in (g, r, b):  # ordre GRB
            bits += self._encode_byte(c)
        return bits

    def _build_spi_buffer(self):
        bits = []
        for color in self.buf:
            bits += self._encode_color(color)
        bytes_out = []
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(bits):
                    byte = (byte << 1) | bits[i + j]
            bytes_out.append(byte)
        return bytes(bytes_out)

    def show(self):
        data = self._build_spi_buffer()
        self.spi.xfer2(list(data))
        time.sleep(0.001)  # latch

    def deinit(self):
        self.fill((0, 0, 0))
        self.show()
