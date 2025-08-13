# -------- Display (Pi friendly) --------
WIDTH  = 128      # <- set to 128 for Waveshare 1.44"
HEIGHT = 128
FPS    = 30

# -------- Backend toggle --------
# SIM=True shows a pygame window via LCDSim; SIM=False pushes to SPI LCDPi
SIM = False

# --- LCD (your backends read these) ---
SPI_HZ = 8_000_000
# ST7735 MADCTL value that worked in your earlier runs; change if orientation/colors are off
M  = 0xA0
# Panel window offsets (often 0/0 or small) for this HAT
X0 = 1
Y0 = 2

# --- SIM (window) niceties ---
SCALE = 3
WINDOW_TITLE = "Ant Colony (LCDSim)"

# -------- Teams / Population --------
NUM_TEAMS   = 2
TEAM_COLORS = [(255, 60, 60), (80, 140, 255)]
START_UNITS = {
    "scavenger": 6,
    "builder":   4,   # you changed
    "defender":  2,
    "attacker":  2,   # you changed
    "reproducer":1,
}
MAX_TEAM_POP   = 55   # you changed
RESPAWN_TICKS  = 8 * FPS

ROLE_WEIGHTS = [[5,2,2,1] for _ in range(NUM_TEAMS)]

# -------- Movement / Exploration --------
BASE_SPEED   = 0.6
TURN_SPEED   = 0.08
FORAGE_WAYPOINT_DIST = int(min(WIDTH, HEIGHT) * 0.35)
FORAGE_TIMEOUT       = 4 * FPS
OUTWARD_BIAS         = 0.10
ATTACKER_SPEED_MULT  = 0.35   # kept

# -------- Boundary control --------
BOUNCE_PAD           = 0
EDGE_BOUNCE_JITTER   = 0.25
TETHER_FRAC          = 99.0

# -------- Needs / Life --------
ENERGY_DECAY = 0.0010   # you changed
ROLE_DECAY   = {"reproducer": 0.35, "default": 1.0}
HEALTH_DECAY_WHEN_STARVING = 0.01
START_ENERGY = 1.0
START_HEALTH = 1.0
LOW_ENERGY_HOME = 0.15

# Food → energy
FOOD_EAT_PER_TICK = 0.25
ENERGY_PER_FOOD   = 0.6
HOME_START_FOOD   = 13      # you changed

# -------- Resources / Food spawning --------
RESOURCE_TYPES = ["wood","stone","metal"]
FOOD_COLOR  = (0, 220, 90)
RES_COLORS  = {"wood": (139, 90, 43), "stone": (175,175,175), "metal": (90, 200, 255)}
MAX_FOOD        = 40       # you changed
MAX_RESOURCES   = 50       # you changed
FOOD_RESPAWN_CHANCE   = 0.30   # you changed
RES_RESPAWN_CHANCE    = 0.45   # you changed

# -------- Buildings --------
BUILDING_COLORS = {"home": (255,255,255)}
HOME_RADIUS = 12
TOWER_RANGE = 48
TOWER_COOLDOWN_TICKS = int(0.8 * FPS)
TOWER_DAMAGE = 0.12

BUILD_COSTS = {
    "tower":   {"metal": 3, "stone": 2, "wood": 1},
    "farm":    {"wood": 2},   # you changed
    "storage": {"stone": 3, "wood": 1},
    "wall":    {"stone": 2},
}

FARM_YIELD_TICKS = int(6 * FPS)
FARM_YIELD_AMOUNT = 1
SALVAGE_RATE = 0.5

MAX_TOWERS   = 3
MAX_FARMS    = 2
MAX_STORAGE  = 2
MAX_WALLS    = 10

REPRODUCE_FOOD_COST = 2

# -------- Round / learning --------
ROUND_MAX_TICKS = 4 * 60 * FPS
META_FILE = "meta.json"
