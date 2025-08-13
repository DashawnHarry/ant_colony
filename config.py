# -------- Display (Pi friendly) --------
WIDTH  = 240     # set 128/128 on your Pi LCD if needed
HEIGHT = 240
FPS    = 30

# -------- Backend (choose how to render) --------
# "lcd"  -> push frames to SPI LCD (Pi)
# "pygame" -> normal desktop window
RENDER = "lcd"

# SPI LCD wiring (Waveshare ST7735-style)
LCD_RST = 27       # BCM pins
LCD_DC  = 25
LCD_BL  = 24
SPI_BUS = 0
SPI_DEV = 0
SPI_HZ  = 8_000_000

# LCD memory access control (rotation + color order)
# If colors/orientation look wrong, try 0xE0, 0x60, 0x70, or 0x00.
MADCTL  = 0xA0

# Panel-specific column/row offsets (common for Waveshare 1.44")
XOFF, YOFF = 1, 2

# -------- Teams / Population --------
NUM_TEAMS   = 2
TEAM_COLORS = [(255, 60, 60), (80, 140, 255)]
START_UNITS = {  # per team
    "scavenger": 6,
    "builder":   4,  
    "defender":  2,
    "attacker":  2,   # (you changed this)
    "reproducer":1,   # spawns at home; never counts for survival
}
MAX_TEAM_POP   = 55   
RESPAWN_TICKS  = 8 * FPS

# Runtime-tuned by meta.py / main.py (per-team lists [scav, builder, defender, attacker])
ROLE_WEIGHTS = [[5,2,2,1] for _ in range(NUM_TEAMS)]

# -------- Movement / Exploration --------
BASE_SPEED   = 0.6
TURN_SPEED   = 0.08
FORAGE_WAYPOINT_DIST = int(min(WIDTH, HEIGHT) * 0.35)
FORAGE_TIMEOUT       = 4 * FPS
OUTWARD_BIAS         = 0.10

# Attackers move slower so they can't roam-kill
ATTACKER_SPEED_MULT  = 0.35   # 35% of BASE_SPEED  (kept)

# -------- Boundary control --------
BOUNCE_PAD           = 0        # touch the edge; bounce only on contact
EDGE_BOUNCE_JITTER   = 0.25
TETHER_FRAC          = 99.0     # effectively off

# -------- Needs / Life --------
ENERGY_DECAY = 0.0010         
ROLE_DECAY   = {"reproducer": 0.35, "default": 1.0}  # repro loses energy slower
HEALTH_DECAY_WHEN_STARVING = 0.01
START_ENERGY = 1.0
START_HEALTH = 1.0
LOW_ENERGY_HOME = 0.15

# Food → energy
FOOD_EAT_PER_TICK = 0.25
ENERGY_PER_FOOD   = 0.6
HOME_START_FOOD   = 13         

# -------- Resources / Food spawning --------
RESOURCE_TYPES = ["wood","stone","metal"]
FOOD_COLOR  = (0, 220, 90)
RES_COLORS  = {"wood": (139, 90, 43), "stone": (175,175,175), "metal": (90, 200, 255)}
MAX_FOOD        = 40           
MAX_RESOURCES   = 50           
FOOD_RESPAWN_CHANCE   = 0.30   
RES_RESPAWN_CHANCE    = 0.45   

# -------- Buildings --------
BUILDING_COLORS = {"home": (255,255,255)}  # others colored by dominant resource cost
HOME_RADIUS = 12
TOWER_RANGE = 48
TOWER_COOLDOWN_TICKS = int(0.8 * FPS)
TOWER_DAMAGE = 0.12

BUILD_COSTS = {
    "tower":   {"metal": 3, "stone": 2, "wood": 1},  # metal-dominant
    "farm":    {"wood": 2},                          # wood-dominant
    "storage": {"stone": 3, "wood": 1},               # stone-dominant
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
ROUND_MAX_TICKS = 4 * 60 * FPS   # safety cap
META_FILE = "meta.json"
