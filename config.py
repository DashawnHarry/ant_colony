# -------- Display (Pi friendly) --------
WIDTH  = 128      # Waveshare 1.44" is 128x128
HEIGHT = 128
FPS    = 30

# -------- Backend toggle --------
# SIM=True shows a pygame window; SIM=False pushes to SPI LCD
SIM = False

# --- LCD (your backends read these) ---
SPI_HZ = 8_000_000
# ST7735 MADCTL; change if orientation/colors are off
M  = 0xA0
# panel window offsets for this HAT
X0 = 1
Y0 = 2

# --- SIM (window) niceties ---
SCALE = 3
WINDOW_TITLE = "Ant Colony (LCDSim)"

# -------- Teams / Population --------
NUM_TEAMS   = 2
TEAM_COLORS = [(255, 60, 60), (80, 140, 255)]
START_UNITS = {  # per team
    "scavenger": 6,
    "builder":   4,   # YOUR CHANGE
    "defender":  2,
    "attacker":  2,   # YOUR CHANGE
    "reproducer":1,   # spawns at home; never counts for survival
}
MAX_TEAM_POP   = 55    # YOUR CHANGE
RESPAWN_TICKS  = 8 * FPS

# Runtime-tuned by meta.py / main.py (per-team lists [scav, builder, defender, attacker])
ROLE_WEIGHTS = [[5,2,2,1] for _ in range(NUM_TEAMS)]

# -------- Movement / Exploration --------
BASE_SPEED   = 0.6
TURN_SPEED   = 0.08
FORAGE_WAYPOINT_DIST = int(min(WIDTH, HEIGHT) * 0.35)
FORAGE_TIMEOUT       = 4 * FPS
OUTWARD_BIAS         = 0.10
ATTACKER_SPEED_MULT  = 0.35   # 35% of BASE_SPEED

# -------- Boundary control --------
BOUNCE_PAD           = 0        # touch the edge; bounce only on contact
EDGE_BOUNCE_JITTER   = 0.25
TETHER_FRAC          = 99.0     # effectively off

# -------- Needs / Life --------
ENERGY_DECAY = 0.0010           # YOUR CHANGE
ROLE_DECAY   = {"reproducer": 0.35, "default": 1.0}  # repro loses energy slower
HEALTH_DECAY_WHEN_STARVING = 0.01
START_ENERGY = 1.0
START_HEALTH = 1.0
LOW_ENERGY_HOME = 0.15

# Food → energy
FOOD_EAT_PER_TICK = 0.25
ENERGY_PER_FOOD   = 0.6
HOME_START_FOOD   = 13           # YOUR CHANGE

# -------- Resources / Food spawning --------
RESOURCE_TYPES = ["wood","stone","metal"]
FOOD_COLOR  = (0, 220, 90)
RES_COLORS  = {"wood": (139, 90, 43), "stone": (175,175,175), "metal": (90, 200, 255)}
MAX_FOOD        = 40             # YOUR CHANGE
MAX_RESOURCES   = 50             # YOUR CHANGE
FOOD_RESPAWN_CHANCE   = 0.30     # YOUR CHANGE
RES_RESPAWN_CHANCE    = 0.45     # YOUR CHANGE

# -------- Buildings (gameplay) --------
BUILDING_COLORS = {"home": (255,255,255)}  # others colored by dominant resource cost
HOME_RADIUS = 12
TOWER_RANGE = 48
TOWER_COOLDOWN_TICKS = int(0.8 * FPS)
TOWER_DAMAGE = 0.12

BUILD_COSTS = {
    "tower":   {"metal": 3, "stone": 2, "wood": 1},
    "farm":    {"wood": 2},   # YOUR CHANGE
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
ROUND_MAX_TICKS = 4 * 60 * FPS   # safety cap
META_FILE = "meta.json"

# -------- Visual-only tweaks for tiny 128x128 display --------
# These DO NOT affect gameplay logic (e.g., HOME_RADIUS still used for logic).
VIS_UNIT_R     = 1      # 1px units (use single pixel)
VIS_FOOD_R     = 1
VIS_RES_R      = 1
VIS_BUILD_R    = 3      # non-home building radius
VIS_HOME_R     = 8      # visual home circle; logic still uses HOME_RADIUS
VIS_WALL_W     = 2      # wall line thickness
DRAW_HEALTH_BARS = False # set True if you want tiny health ticks
HUD_FONT_SIZE    = 8     # small HUD font on 128x128
