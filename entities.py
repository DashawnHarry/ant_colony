import math, random, pygame
from dataclasses import dataclass, field
from typing import List, Dict
from config import *

# ---------------- helpers ----------------
def clamp(x, lo, hi): return lo if x < lo else hi if x > hi else x
def dist2(ax, ay, bx, by): dx, dy = ax - bx, ay - by; return dx*dx + dy*dy

def building_fill_color(btype: str):
    if btype == "home":
        return BUILDING_COLORS["home"]
    cost = BUILD_COSTS.get(btype, {})
    if not cost: return (200,200,200)
    dom = max(cost.items(), key=lambda kv: kv[1])[0]
    return RES_COLORS.get(dom, (200,200,200))

def _px(surf, x, y, col):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        surf.set_at((int(x), int(y)), col)

# 5x5 pixel icons (centered on building)
_ICON_TOWER = [
    "#####",
    "  #  ",
    "  #  ",
    "  #  ",
    "  #  ",
]
_ICON_FARM = [
    "# # #",
    " #####",
    "# # #",
    " #####",
    "# # #",
]
_ICON_STORAGE = [
    "#####",
    "#   #",
    "#   #",
    "#   #",
    "#####",
]

def _draw_icon(surf, cx, cy, pattern, color):
    ox, oy = -2, -2  # center 5x5 on (cx,cy)
    for j, row in enumerate(pattern):
        for i, ch in enumerate(row):
            if ch != " ":
                _px(surf, cx + ox + i, cy + oy + j, color)

# ---------------- world objects ----------------
@dataclass
class Resource:
    x: float; y: float; rtype: str
    def draw(self, surf):
        r = max(1, VIS_RES_R)
        if r <= 1:
            _px(surf, int(self.x), int(self.y), RES_COLORS[self.rtype])
        else:
            pygame.draw.circle(surf, RES_COLORS[self.rtype], (int(self.x), int(self.y)), r)

@dataclass
class Food:
    x: float; y: float
    def draw(self, surf):
        r = max(1, VIS_FOOD_R)
        if r <= 1:
            _px(surf, int(self.x), int(self.y), FOOD_COLOR)
        else:
            pygame.draw.circle(surf, FOOD_COLOR, (int(self.x), int(self.y)), r)

@dataclass
class Building:
    x: float; y: float; team: int; btype: str
    hp: float = 1.0
    stock_food: float = HOME_START_FOOD
    stock: Dict[str, int] = field(default_factory=lambda: {k:0 for k in RESOURCE_TYPES})
    respawn_q: List[tuple] = field(default_factory=list)  # (ticks_remaining, role)
    _cooldown:int = 0
    _farm_timer:int = 0

    def is_home(self): return self.btype == "home"

    def draw(self, surf):
        fill = building_fill_color(self.btype)
        teamc = TEAM_COLORS[self.team]
        cx, cy = int(self.x), int(self.y)

        if self.btype == "wall":
            x1, y1 = int(self.x - 5), int(self.y)
            x2, y2 = int(self.x + 5), int(self.y)
            pygame.draw.line(surf, fill, (x1,y1), (x2,y2), max(1, VIS_WALL_W))
            return

        if self.is_home():
            r_vis = max(3, VIS_HOME_R)
            # Team-colored ring
            pygame.draw.circle(surf, teamc, (cx, cy), r_vis, 2 if r_vis >= 4 else 1)
            # Compact center fill
            inner = max(1, r_vis - 2)
            pygame.draw.circle(surf, BUILDING_COLORS["home"], (cx, cy), inner, 0)
        else:
            r_vis = max(2, VIS_BUILD_R)
            pygame.draw.circle(surf, fill, (cx, cy), r_vis, 0)
            if r_vis >= 2:
                pygame.draw.circle(surf, teamc, (cx, cy), r_vis, 1)

            # Micro icon overlay (white for clarity on resource-colored fill)
            icon_color = (240, 240, 240)
            if self.btype == "tower":
                _draw_icon(surf, cx, cy, _ICON_TOWER, icon_color)
            elif self.btype == "farm":
                _draw_icon(surf, cx, cy, _ICON_FARM, icon_color)
            elif self.btype == "storage":
                _draw_icon(surf, cx, cy, _ICON_STORAGE, icon_color)

        # Optional tiny health tick (off by default)
        if (not self.is_home()) and DRAW_HEALTH_BARS:
            w = max(1, int(6*self.hp))  # small
            pygame.draw.line(surf, teamc, (cx-3, cy + r_vis + 1), (cx-3 + w, cy + r_vis + 1), 1)

    def update(self, allies, enemies, buildings, foods):
        if self.btype == "tower":
            self._tick_tower(enemies)
        elif self.btype == "farm":
            self._tick_farm(foods)
        if self.is_home():
            self._tick_respawns(allies)
            self._feed_allies_inside(allies)

    def _tick_tower(self, enemies):
        if self._cooldown > 0:
            self._cooldown -= 1; return
        tgt = None; best = 1e18
        for e in enemies:
            d2 = dist2(e.x, e.y, self.x, self.y)
            if d2 < TOWER_RANGE*TOWER_RANGE and d2 < best:
                best = d2; tgt = e
        if tgt:
            tgt.health -= TOWER_DAMAGE
            self._cooldown = TOWER_COOLDOWN_TICKS

    def _tick_farm(self, foods):
        self._farm_timer += 1
        if self._farm_timer >= FARM_YIELD_TICKS:
            self._farm_timer = 0
            foods.append(Food(self.x + random.randint(-10,10),
                              self.y + random.randint(-10,10)))

    def _tick_respawns(self, allies):
        keep=[]
        for t_left, role in self.respawn_q:
            if t_left>0:
                keep.append((t_left-1, role)); continue
            if role == "reproducer":
                allies.append(Unit(self.x, self.y, self.team, role, self))
                continue
            if self.stock_food >= REPRODUCE_FOOD_COST:
                self.stock_food -= REPRODUCE_FOOD_COST
                allies.append(Unit(self.x, self.y, self.team, role, self))
            else:
                keep.append((FPS, role))
        self.respawn_q = keep

    def _feed_allies_inside(self, allies):
        if self.stock_food <= 0: return
        r2 = (HOME_RADIUS + 2) ** 2
        for u in allies:
            if dist2(u.x,u.y,self.x,self.y) <= r2 and u.energy < 1.0 and self.stock_food > 0:
                eat = min(FOOD_EAT_PER_TICK, self.stock_food)
                self.stock_food -= eat
                u.energy = min(1.0, u.energy + eat * ENERGY_PER_FOOD)

# ---------------- units ----------------
class Unit:
    __slots__ = ("x","y","team","role","home","angle","speed","energy","health",
                 "carry_food","carry_res","wp","wp_t")

    def __init__(self, x, y, team, role, home: Building):
        self.x=x; self.y=y; self.team=team; self.role=role; self.home=home
        self.angle = random.uniform(0, math.pi*2)
        self.speed = BASE_SPEED * (ATTACKER_SPEED_MULT if role == "attacker" else 1.0)
        self.energy = START_ENERGY
        self.health = START_HEALTH
        self.carry_food = 0
        self.carry_res = {k:0 for k in RESOURCE_TYPES}
        self.wp = None
        self.wp_t = 0

    # ---- movement primitives ----
    def move_towards_point(self, tx, ty):
        a = math.atan2(ty - self.y, tx - self.x)
        diff = (a - self.angle + math.pi) % (2*math.pi) - math.pi
        if abs(diff) > TURN_SPEED:
            self.angle += TURN_SPEED * (1 if diff > 0 else -1)
        else:
            self.angle = a
        self.x += math.cos(self.angle)*self.speed
        self.y += math.sin(self.angle)*self.speed
        self._bounce_if_needed()

    def wander(self):
        out_ang = math.atan2(self.y - self.home.y, self.x - self.home.x)
        self.angle += random.uniform(-0.08, 0.08)
        self.angle = (self.angle * (1.0 - OUTWARD_BIAS) + out_ang * OUTWARD_BIAS)
        self.x += math.cos(self.angle)*self.speed*0.9
        self.y += math.sin(self.angle)*self.speed*0.9
        self._bounce_if_needed()

    def _bounce_if_needed(self):
        pad = BOUNCE_PAD
        bounced = False
        if self.x <= pad:
            self.x = pad; self.angle = math.pi - self.angle; bounced=True
        elif self.x >= WIDTH - pad:
            self.x = WIDTH - pad; self.angle = math.pi - self.angle; bounced=True
        if self.y <= pad:
            self.y = pad; self.angle = -self.angle; bounced=True
        elif self.y >= HEIGHT - pad:
            self.y = HEIGHT - pad; self.angle = -self.angle; bounced=True
        if bounced:
            self.angle += random.uniform(-EDGE_BOUNCE_JITTER, EDGE_BOUNCE_JITTER)

    def _too_far_from_home(self):
        tether_r = min(WIDTH, HEIGHT) * TETHER_FRAC
        return dist2(self.x,self.y,self.home.x,self.home.y) > tether_r*tether_r

    def _inside_home(self):
        return dist2(self.x,self.y,self.home.x,self.home.y) <= (HOME_RADIUS + 2)**2

    def _head_home(self):
        self.move_towards_point(self.home.x, self.home.y)
        if self._inside_home():
            if self.carry_food>0:
                self.home.stock_food += self.carry_food
                self.carry_food = 0
            if any(self.carry_res.values()):
                for k,v in self.carry_res.items():
                    self.home.stock[k]+=v
                    self.carry_res[k]=0
            if self.home.stock_food > 0 and self.energy < 1.0:
                eat = min(FOOD_EAT_PER_TICK, self.home.stock_food)
                self.home.stock_food -= eat
                self.energy = min(1.0, self.energy + eat * ENERGY_PER_FOOD)

    # ---- brain ----
    def update(self, foods: List[Food], resources: List[Resource],
               buildings: List[Building], units: List['Unit']):
        decay = 0.0 if self.role == "reproducer" else ENERGY_DECAY * ROLE_DECAY.get(self.role, ROLE_DECAY["default"])
        self.energy -= decay
        if self.role != "reproducer" and self.energy <= 0:
            self.health -= HEALTH_DECAY_WHEN_STARVING

        if self.health <= 0:
            if self.role == "reproducer":
                self.home.respawn_q.append((1, "reproducer"))
            else:
                self.home.respawn_q.append((RESPAWN_TICKS, self.role))
            if self.carry_food>0: foods.append(Food(self.x, self.y))
            for k,v in self.carry_res.items():
                for _ in range(v):
                    resources.append(Resource(self.x+random.randint(-2,2),
                                              self.y+random.randint(-2,2), k))
            return False

        if self.energy < LOW_ENERGY_HOME:
            self._head_home(); return True
        if self._too_far_from_home():
            self.move_towards_point(self.home.x, self.home.y); return True

        if self.role == "scavenger":
            self._tick_scavenger(foods)
        elif self.role == "builder":
            self._tick_builder(resources, buildings)
        elif self.role == "defender":
            self._tick_defender(units)
        elif self.role == "attacker":
            self._tick_attacker(buildings, resources, units)
        elif self.role == "reproducer":
            self._tick_reproducer(units)

        return True

    # ---- role details ----
    def _pick_waypoint(self):
        ang = random.uniform(0, 2*math.pi)
        r   = FORAGE_WAYPOINT_DIST + random.randint(-8, 8)
        x   = clamp(self.home.x + math.cos(ang)*r, 4, WIDTH-4)
        y   = clamp(self.home.y + math.sin(ang)*r, 4, HEIGHT-4)
        self.wp = (x, y)
        self.wp_t = FORAGE_TIMEOUT

    def _tick_scavenger(self, foods):
        if self.carry_food>0:
            self._head_home(); return
        if foods:
            tgt = min(foods, key=lambda f: dist2(self.x,self.y,f.x,f.y))
            self.move_towards_point(tgt.x, tgt.y)
            if dist2(self.x,self.y,tgt.x,tgt.y) < 16:
                self.carry_food += 1
                if tgt in foods: foods.remove(tgt)
            return
        if not self.wp or self.wp_t <= 0: self._pick_waypoint()
        self.move_towards_point(self.wp[0], self.wp[1]); self.wp_t -= 1
        if dist2(self.x,self.y,self.wp[0],self.wp[1]) < 20: self._pick_waypoint()

    def _builder_plan(self, buildings):
        my = [b for b in buildings if b.team==self.team]
        counts = {"tower":0,"farm":0,"storage":0,"wall":0}
        for b in my:
            if b.btype in counts: counts[b.btype]+=1
        if counts["tower"] < MAX_TOWERS: return "tower"
        if counts["farm"]  < MAX_FARMS:  return "farm"
        if counts["storage"]< MAX_STORAGE:return "storage"
        return None

    def _has_cost(self, cost): return all(self.home.stock.get(k,0) >= v for k,v in cost.items())
    def _pay_cost(self, cost):
        for k,v in cost.items(): self.home.stock[k] -= v

    def _tick_builder(self, resources, buildings):
        if any(self.carry_res.values()):
            self._head_home(); return
        plan = self._builder_plan(buildings)
        if plan:
            cost = BUILD_COSTS[plan]
            if not self._has_cost(cost):
                if resources:
                    tgt = min(resources, key=lambda r: dist2(self.x,self.y,r.x,r.y))
                    self.move_towards_point(tgt.x, tgt.y)
                    if dist2(self.x,self.y,tgt.x,tgt.y) < 16:
                        self.carry_res[tgt.rtype]+=1
                        if tgt in resources: resources.remove(tgt)
                else:
                    if not self.wp or self.wp_t <= 0: self._pick_waypoint()
                    self.move_towards_point(self.wp[0], self.wp[1]); self.wp_t -= 1
            else:
                px = clamp(self.home.x + random.randint(-20,20), 8, WIDTH-8)
                py = clamp(self.home.y + random.randint(-20,20), 8, HEIGHT-8)
                self._pay_cost(cost)
                buildings.append(Building(px, py, self.team, plan))
                self.wp = None
        else:
            if not self.wp or self.wp_t <= 0: self._pick_waypoint()
            self.move_towards_point(self.wp[0], self.wp[1]); self.wp_t -= 1

    def _tick_defender(self, units):
        enemies = [u for u in units if u.team!=self.team and u.role!="reproducer"]
        if enemies:
            tgt = min(enemies, key=lambda e: dist2(self.home.x,self.home.y,e.x,e.y))
            self.move_towards_point(tgt.x, tgt.y)
            if dist2(self.x,self.y,tgt.x,tgt.y) < 25:
                tgt.health -= 0.05
        else:
            ang = math.atan2(self.y-self.home.y, self.x-self.home.x) + 0.1
            rad = HOME_RADIUS + 8
            tx = self.home.x + math.cos(ang)*rad
            ty = self.home.y + math.sin(ang)*rad
            self.move_towards_point(tx, ty)

    def _tick_attacker(self, buildings, resources, units):
        if any(self.carry_res.values()):
            self._head_home(); return

        enemy_units = [u for u in units if u.team != self.team and u.role != "reproducer"]
        if enemy_units:
            tgt = min(enemy_units, key=lambda e: dist2(self.x,self.y,e.x,e.y))
            self.move_towards_point(tgt.x, tgt.y)
            if dist2(self.x,self.y,tgt.x,tgt.y) < 25:
                tgt.health -= 0.06
            return

        targets = [b for b in buildings if b.team != self.team and b.btype != "home"]
        if targets:
            tgt = min(targets, key=lambda b: dist2(self.x,self.y,b.x,b.y))
            self.move_towards_point(tgt.x, tgt.y)
            if dist2(self.x,self.y,tgt.x,tgt.y) < 36:
                cost = BUILD_COSTS.get(tgt.btype, {})
                for k,v in cost.items():
                    salv = max(0, int(round(v * SALVAGE_RATE)))
                    if salv>0: self.carry_res[k] += salv
                tgt.hp -= 0.08
                if tgt.hp <= 0 and tgt in buildings:
                    buildings.remove(tgt)
            return

        if not self.wp or self.wp_t <= 0: self._pick_waypoint()
        self.move_towards_point(self.wp[0], self.wp[1]); self.wp_t -= 1

    def _tick_reproducer(self, units):
        if not self._inside_home():
            self._head_home(); return
        if self.home.stock_food > 0 and self.energy < 1.0:
            eat = min(FOOD_EAT_PER_TICK, self.home.stock_food)
            self.home.stock_food -= eat
            self.energy = min(1.0, self.energy + eat * ENERGY_PER_FOOD)
        return

    # ---- render ----
    def draw(self, surf):
        r = max(1, VIS_UNIT_R)
        x, y = int(self.x), int(self.y)
        if r <= 1:
            _px(surf, x, y, TEAM_COLORS[self.team])
        else:
            pygame.draw.circle(surf, TEAM_COLORS[self.team], (x, y), r)
