import time, numpy as np, spidev
import RPi.GPIO as G
import config as C

W, H = C.WIDTH, C.HEIGHT
RST, DC, BL = 27, 25, 24

class LCDPi:
    def __init__(self):
        G.setwarnings(False)
        G.setmode(G.BCM)
        for p in (RST,DC,BL):
            G.setup(p, G.OUT)
        G.output(BL, 1)
        self.spi = spidev.SpiDev(); self.spi.open(0,0); self.spi.max_speed_hz = C.SPI_HZ
        self._cmd(0x11); time.sleep(0.12)
        self._cmd(0x36, [C.M])
        self._cmd(0x3A, [0x05])
        self._cmd(0x29)

    def _write_chunked(self, b):
        for i in range(0, len(b), 4096):
            self.spi.writebytes(b[i:i+4096])

    def _cmd(self, v, data=None):
        G.output(DC,0); self.spi.writebytes([v])
        if data is not None:
            G.output(DC,1); self._write_chunked(bytearray(data))

    def _window_full(self):
        G.output(DC,0); self.spi.writebytes([0x2A])
        G.output(DC,1); self._write_chunked(bytearray([0,0+C.X0, 0,(W-1)+C.X0]))
        G.output(DC,0); self.spi.writebytes([0x2B])
        G.output(DC,1); self._write_chunked(bytearray([0,0+C.Y0, 0,(H-1)+C.Y0]))
        G.output(DC,0); self.spi.writebytes([0x2C])

    @staticmethod
    def rgb_to_bgr565_bytes(img_np):
        r = img_np[...,0]; g = img_np[...,1]; b = img_np[...,2]
        r, b = b, r
        v = ((r & 0xF8).astype(np.uint16) << 8) | ((g & 0xFC).astype(np.uint16) << 3) | (b.astype(np.uint16) >> 3)
        hi = (v >> 8).astype(np.uint8); lo = (v & 0xFF).astype(np.uint8)
        out = np.empty((img_np.shape[0], img_np.shape[1]*2), dtype=np.uint8)
        out[:,0::2], out[:,1::2] = hi, lo
        return out.ravel().tobytes()

    def push_numpy_rgb(self, img_np):
        assert img_np.shape[0]==H and img_np.shape[1]==W and img_np.shape[2]==3
        self._window_full()
        G.output(DC,1)
        self._write_chunked(self.rgb_to_bgr565_bytes(img_np))

    def close(self):
        try: G.cleanup()
        except: pass
