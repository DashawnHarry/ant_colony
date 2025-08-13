import config as C

def get_lcd():
    if C.SIM:
        from lcd_backend_sim import LCDSim
        return LCDSim()
    try:
        from lcd_backend_pi import LCDPi
        return LCDPi()
    except Exception as e:
        print("[lcd] Falling back to simulator:", e)
        from lcd_backend_sim import LCDSim
        return LCDSim()

W, H = C.WIDTH, C.HEIGHT
