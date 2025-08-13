# main.py
import random, pygame
from typing import List
import config as C
from entities import Unit, Building, Food, Resource
import meta

# bridge that gives us an offscreen Surface and pushes to LCD (or SIM window)
from lcd_present import surface, present, close

# Offscreen render target (HxW) — draw to this exactly like a normal pygame Surface.
screen = surface()
clock  = pygame.time.Clock()
try:
    font = pygame.font.SysFont("consolas", 12)
except Exception:
    font = pygame.font.Font(None, 12)

# --- world state ---
buildings: List[Building] = []
units:     List[Unit]     = []
foods:     List[Food]     = []
resources: List[Resource] = []
tick      = 0
round_id  = 0

# --- learning state ---
meta_state = meta.load_meta()
C.ROLE_WEIGHTS = meta_state["role_weights"]  # keep per-team weights in sync

# ----------------- world setup -----------------
def spawn_initial_world():
    global buildings, units, foods, resources, tick
    buildings, units, foods, resources = [], [], [], []
    tick = 0

    homes=[]
    margin = 16 if min(C.WIDTH, C.HEIGHT) <= 128 else 24
    for t in range(C.NUM_TEAMS):
        hx = margin if t == 0 else C.WIDTH - margin
        hy = C.HEIGHT // 2
        b = Building(hx, hy, t, "home")
        buildings.append(b)
        homes.append(b)

    # starting population
    for t, home in enumerate(homes):
        for role, n in C.START_UNITS.items():
            for _ in range(n):
                units.append(Unit(home.x, home.y, t, role, home))

    # scatter initial food/resources
    for _ in range(C.MAX_FOOD):
        foods.append(Food(random.randint(6, C.WIDTH-6), random.randint(6, C.HEIGHT-6)))
    for _ in range(C.MAX_RESOURCES):
        rtype = random.choice(C.RESOURCE_TYPES)
        resources.append(Resource(random.randint(6, C.WIDTH-6), random.randint(6, C.HEIGHT-6), rtype))

def spawn_food_and_resources():
    # light, probabilistic respawn each frame
    if len(foods) < C.MAX_FOOD and random.random() < C.FOOD_RESPAWN_CHANCE / C.FPS:
        foods.append(Food(random.randint(6, C.WIDTH-6), random.randint(6, C.HEIGHT-6)))
    if len(resources) < C.MAX_RESOURCES and random.random() < C.RES_RESPAWN_CHANCE / C.FPS:
        rtype = random.choice(C.RESOURCE_TYPES)
        resources.append(Resource(random.randint(6, C.WIDTH-6), random.randint(6, C.HEIGHT-6), rtype))

def survivors_nonrepro_count():
    counts = [0]*C.NUM_TEAMS
    for u in units:
        if u.role != "reproducer":
            counts[u.team] += 1
    return counts

def survivors_by_role():
    # [team][scav,builder,defender,attacker]
    role_ix = {"scavenger":0,"builder":1,"defender":2,"attacker":3}
    data = [[0,0,0,0] for _ in range(C.NUM_TEAMS)]
    for u in units:
        if u.role == "reproducer": continue
        data[u.team][ role_ix.get(u.role,0) ] += 1
    return data

def ensure_reproducer_exists():
    """Guarantee each team always has a reproducer (spawns free at home if missing)."""
    for t in range(C.NUM_TEAMS):
        home = next((b for b in buildings if b.team==t and b.btype=="home"), None)
        if not home: continue
        has_repro = any(u for u in units if u.team==t and u.role=="reproducer")
        in_queue  = any(role=="reproducer" for _,role in home.respawn_q)
        if not has_repro and not in_queue:
            home.respawn_q.append((1,"reproducer"))

def end_round_and_restart(winner):
    """Persist tiny 'learning' for role weights and restart the world."""
    global round_id, meta_state
    surv_roles = survivors_by_role()
    meta_state = meta.update_after_round(meta_state, winner, surv_roles)
    meta.save_meta(meta_state)
    C.ROLE_WEIGHTS = meta_state["role_weights"]
    round_id += 1
    spawn_initial_world()

def reproduction_tick():
    """Reproducer attempts to spawn one unit per second (if base has food, pop cap not reached)."""
    pops = [0]*C.NUM_TEAMS
    for u in units:
        if u.role != "reproducer":
            pops[u.team] += 1

    for t in range(C.NUM_TEAMS):
        if pops[t] >= C.MAX_TEAM_POP: continue
        home = next((b for b in buildings if b.team==t and b.btype=="home"), None)
        if not home: continue
        if tick % C.FPS != 0: continue   # ~1Hz
        if home.stock_food < C.REPRODUCE_FOOD_COST: continue

        weights = C.ROLE_WEIGHTS[t]  # [scav, builder, defender, attacker]
        roles = ["scavenger","builder","defender","attacker"]
        role  = random.choices(roles, weights=weights, k=1)[0]
        home.stock_food -= C.REPRODUCE_FOOD_COST
        units.append(Unit(home.x, home.y, t, role, home))

# ----------------- rendering -----------------
def draw_world():
    screen.fill((0,0,0))
    for r in resources: r.draw(screen)
    for f in foods:     f.draw(screen)
    for b in buildings: b.draw(screen)
    for u in units:     u.draw(screen)

    # Tiny HUD (top-left)
    sr = survivors_nonrepro_count()
    hud = f"Rd {round_id} t:{tick}  A:{sr[0]} B:{sr[1]}"
    screen.blit(font.render(hud, True, (200,200,200)), (2,2))

# ----------------- main loop -----------------
def main():
    spawn_initial_world()
    running = True
    global tick

    while running:
        dt = clock.tick(C.FPS)
        tick += 1

        # even in SIM, let pygame pump the event queue
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        spawn_food_and_resources()

        # buildings update
        for b in list(buildings):
            allies  = [u for u in units if u.team==b.team]
            enemies = [u for u in units if u.team!=b.team and u.role!="reproducer"]
            b.update(allies, enemies, buildings, foods)

        ensure_reproducer_exists()
        reproduction_tick()

        # units update (remove dead)
        alive=[]
        for u in units:
            if u.update(foods, resources, buildings, units):
                alive.append(u)
        units[:] = alive

        # round end / restart logic
        sr = survivors_nonrepro_count()
        alive_teams = [i for i,c in enumerate(sr) if c>0]
        if len(alive_teams) == 1:
            end_round_and_restart(alive_teams[0])
        elif len(alive_teams) == 0 and tick > C.FPS*8:
            end_round_and_restart(None)
        elif tick >= C.ROUND_MAX_TICKS:
            winner = 0 if sr[0] > sr[1] else 1 if sr[1] > sr[0] else None
            end_round_and_restart(winner)

        # draw & present to LCD or SIM window
        draw_world()
        present()

    close()

if __name__ == "__main__":
    main()
