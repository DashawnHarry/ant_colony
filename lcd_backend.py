import time, spidev, RPi.GPIO as G
import numpy as np
from config import WIDTH, HEIGHT, LCD_RST, LCD_DC, LCD_BL, SPI_BUS, SPI_DEV, SPI_HZ, MADCTL, XOFF, YOFF

class LCDBackend:
    def __init__(self, w=WIDTH, h=HEIGHT):
        self.W, self.H = w, h

        # SPI
        self.spi = spidev.SpiDev()
        self.spi.open(SPI_BUS, SPI_DEV)
        self.spi.max_speed_hz = SPI_HZ
        self.spi.mode = 0

        # GPIO
        G.setwarnings(False)
        G.setmode(G.BCM)
        for pin in (LCD_RST, LCD_DC, LCD_BL):
            G.setup(pin, G.OUT)
        G.output(LCD_BL, 1)

        self._reset()
        self._init_panel()

    def _c(self, val):
        G.output(LCD_DC, 0)
        self.spi.writebytes([val & 0xFF])

    def _d(self, data):
        G.output(LCD_DC, 1)
        if isinstance(data, (bytes, bytearray)):
            # split to safe chunks
            for i in range(0, len(data), 4096):
                self.spi.writebytes(data[i:i+4096])
        else:
            # list/iterable of ints
            buf = list(data)
            for i in range(0, len(buf), 4096):
                self.spi.writebytes(buf[i:i+4096])

    def _reset(self):
        G.output(LCD_RST, 1); time.sleep(0.01)
        G.output(LCD_RST, 0); time.sleep(0.01)
        G.output(LCD_RST, 1); time.sleep(0.12)

    def _init_panel(self):
        self._c(0x11); time.sleep(0.12)         # Sleep out
        self._c(0x36); self._d([MADCTL])        # MADCTL (rotation / BGR)
        self._c(0x3A); self._d([0x05])          # 16-bit color
        # Address window full screen (with panel offsets)
        self._c(0x2A); self._d([0, XOFF, 0, XOFF + self.W - 1])
        self._c(0x2B); self._d([0, YOFF, 0, YOFF + self.H - 1])
        self._c(0x29)                           # Display on

    def blit_surface(self, surface):
        """Convert a pygame Surface (WIDTH x HEIGHT) to RGB565 and push."""
        import pygame
        # RGB 24-bit bytes (row-major)
        rgb_bytes = pygame.image.tostring(surface, "RGB")
        arr = np.frombuffer(rgb_bytes, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3))
        r = arr[:,:,0].astype(np.uint16)
        g = arr[:,:,1].astype(np.uint16)
        b = arr[:,:,2].astype(np.uint16)
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        # interleave MSB/LSB
        out = np.empty(self.W*self.H*2, dtype=np.uint8)
        out[0::2] = (rgb565 >> 8).astype(np.uint8)
        out[1::2] = (rgb565 & 0xFF).astype(np.uint8)

        self._c(0x2C)           # RAM write
        self._d(out.tobytes())  # chunked inside ._d

    def close(self):
        try:
            self._c(0x28)  # display off
        except Exception:
            pass
        try:
            G.output(LCD_BL, 0)
            G.cleanup()
        except Exception:
            pass
        try:
            self.spi.close()
        except Exception:
            pass
