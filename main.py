import os, pygame, random
from typing import List
import config
from config import *
from entities import Unit, Building, Food, Resource
import meta

# Choose backend BEFORE pygame.init()
LCD = None
if RENDER == "lcd":
    os.environ["SDL_VIDEODRIVER"] = "dummy"   # headless pygame
pygame.init()

# Offscreen surface for both modes (we'll present differently)
screen = pygame.Surface((WIDTH, HEIGHT)) if RENDER == "lcd" \
         else pygame.display.set_mode((WIDTH, HEIGHT))
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("consolas", 12)

if RENDER == "lcd":
    from lcd_backend import LCDBackend
    LCD = LCDBackend(WIDTH, HEIGHT)

# --- world state ---
buildings: List[Building] = []
units:     List[Unit]     = []
foods:     List[Food]     = []
resources: List[Resource] = []
tick      = 0
round_id  = 0

# --- learning state ---
meta_state = meta.load_meta()
config.ROLE_WEIGHTS = meta_state["role_weights"]

def spawn_initial_world():
    global buildings, units, foods, resources, tick
    buildings, units, foods, resources = [], [], [], []
    tick = 0
    homes=[]
    margin = 24
    for t in range(NUM_TEAMS):
        hx = margin if t==0 else WIDTH - margin
        hy = HEIGHT//2
        b = Building(hx, hy, t, "home")
        buildings.append(b); homes.append(b)
    for t, home in enumerate(homes):
        for role, n in START_UNITS.items():
            for _ in range(n):
                units.append(Unit(home.x, home.y, t, role, home))
    for _ in range(MAX_FOOD):
        foods.append(Food(random.randint(8, WIDTH-8), random.randint(8, HEIGHT-8)))
    for _ in range(MAX_RESOURCES):
        rtype = random.choice(RESOURCE_TYPES)
        resources.append(Resource(random.randint(8, WIDTH-8), random.randint(8, HEIGHT-8), rtype))

def spawn_food_and_resources():
    if len(foods)   < MAX_FOOD       and random.random() < FOOD_RESPAWN_CHANCE / FPS:
        foods.append(Food(random.randint(8, WIDTH-8), random.randint(8, HEIGHT-8)))
    if len(resources) < MAX_RESOURCES and random.random() < RES_RESPAWN_CHANCE / FPS:
        rtype = random.choice(RESOURCE_TYPES)
        resources.append(Resource(random.randint(8, WIDTH-8), random.randint(8, HEIGHT-8), rtype))

def survivors_nonrepro_count():
    counts = [0]*NUM_TEAMS
    for u in units:
        if u.role != "reproducer":
            counts[u.team] += 1
    return counts

def survivors_by_role():
    role_ix = {"scavenger":0,"builder":1,"defender":2,"attacker":3}
    data = [[0,0,0,0] for _ in range(NUM_TEAMS)]
    for u in units:
        if u.role == "reproducer": continue
        data[u.team][ role_ix.get(u.role,0) ] += 1
    return data

def ensure_reproducer_exists():
    for t in range(NUM_TEAMS):
        home = next((b for b in buildings if b.team==t and b.btype=="home"), None)
        if not home: continue
        has_repro = any(u for u in units if u.team==t and u.role=="reproducer")
        in_queue  = any(role=="reproducer" for _,role in home.respawn_q)
        if not has_repro and not in_queue:
            home.respawn_q.append((1,"reproducer"))

def end_round_and_restart(winner):
    global round_id, meta_state
    surv_roles = survivors_by_role()
    meta_state = meta.update_after_round(meta_state, winner, surv_roles)
    meta.save_meta(meta_state)
    config.ROLE_WEIGHTS = meta_state["role_weights"]
    round_id += 1
    spawn_initial_world()

def reproduction_tick():
    pops = [0]*NUM_TEAMS
    for u in units:
        if u.role != "reproducer":
            pops[u.team] += 1
    for t in range(NUM_TEAMS):
        if pops[t] >= MAX_TEAM_POP: continue
        home = next((b for b in buildings if b.team==t and b.btype=="home"), None)
        if not home: continue
        if tick % FPS != 0: continue
        if home.stock_food < REPRODUCE_FOOD_COST: continue
        weights = config.ROLE_WEIGHTS[t]
        roles = ["scavenger","builder","defender","attacker"]
        import random
        role  = random.choices(roles, weights=weights, k=1)[0]
        home.stock_food -= REPRODUCE_FOOD_COST
        units.append(Unit(home.x, home.y, t, role, home))

def draw_world():
    screen.fill((0,0,0))
    for r in resources: r.draw(screen)
    for f in foods:     f.draw(screen)
    for b in buildings: b.draw(screen)
    for u in units:     u.draw(screen)
    sr = survivors_nonrepro_count()
    txt = f"Rd {round_id} t:{tick}  A:{sr[0]} B:{sr[1]}"
    screen.blit(font.render(txt, True, (200,200,200)), (2,2))

def main():
    spawn_initial_world()
    running = True
    global tick
    while running:
        dt = clock.tick(FPS)
        tick += 1

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        spawn_food_and_resources()

        for b in list(buildings):
            allies = [u for u in units if u.team==b.team]
            enemies = [u for u in units if u.team!=b.team and u.role!="reproducer"]
            b.update(allies, enemies, buildings, foods)

        ensure_reproducer_exists()
        reproduction_tick()

        alive=[]
        for u in units:
            if u.update(foods, resources, buildings, units):
                alive.append(u)
        units[:] = alive

        sr = survivors_nonrepro_count()
        alive_teams = [i for i,c in enumerate(sr) if c>0]
        if len(alive_teams) == 1:
            end_round_and_restart(alive_teams[0])
        elif len(alive_teams) == 0 and tick > FPS*8:
            end_round_and_restart(None)
        elif tick >= ROUND_MAX_TICKS:
            winner = 0 if sr[0] > sr[1] else 1 if sr[1] > sr[0] else None
            end_round_and_restart(winner)

        draw_world()

        if RENDER == "lcd":
            LCD.blit_surface(screen)
        else:
            pygame.display.flip()

    if LCD:
        LCD.close()
    pygame.quit()

if __name__ == "__main__":
    main()
