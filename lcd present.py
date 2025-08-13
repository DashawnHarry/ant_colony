# lcd_present.py
import os, numpy as np, pygame
import config as C
from lcd import get_lcd, W, H  # uses your SIM flag and returns LCDPi or LCDSim

# If we are pushing to the real LCD, avoid opening a pygame window for the offscreen surface.
if not C.SIM:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

pygame.init()
_surface = pygame.Surface((W, H))
_lcd = get_lcd()

def surface():
    """Get the offscreen pygame Surface you should draw onto each frame."""
    return _surface

def present():
    """Convert the current Surface to HxWx3 RGB and push via your backends."""
    # Convert to contiguous RGB888 -> (H, W, 3) uint8
    rgb_bytes = pygame.image.tostring(_surface, "RGB")
    arr = np.frombuffer(rgb_bytes, dtype=np.uint8).reshape((H, W, 3))
    _lcd.push_numpy_rgb(arr)

def close():
    try:
        pygame.quit()
    except:
        pass
    try:
        _lcd.close()
    except:
        pass

if __name__ == "__main__":
    # quick smoke test: moving gradient so you can verify orientation & size
    clock = pygame.time.Clock()
    t = 0
    try:
        while True:
            t += 1
            # draw to the offscreen surface
            s = surface()
            s.lock()
            for y in range(H):
                for x in range(W):
                    s.set_at((x,y), ((x+t) % 256, (y*2) % 256, ((x+y)//2 + t) % 256))
            s.unlock()
            present()
            clock.tick(C.FPS)
    except KeyboardInterrupt:
        close()
