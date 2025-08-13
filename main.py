import pygame, random, math, time
from typing import List
import config
from config import *
from entities import Unit, Building, Food, Resource
import meta

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("consolas", 12)

# --- world state ---
buildings: List[Building] = []
units:     List[Unit]     = []
foods:     List[Food]     = []
resources: List[Resource] = []
tick      = 0
round_id  = 0

# --- learning state ---
meta_state = meta.load_meta()
# copy meta role weights into config so entities uses them
config.ROLE_WEIGHTS = meta_state["role_weights"]

def spawn_initial_world():
    global buildings, units, foods, resources, tick
    buildings, units, foods, resources = [], [], [], []
    tick = 0

    # homes
    homes=[]
    margin = 40
    for t in range(NUM_TEAMS):
        hx = margin if t==0 else WIDTH - margin
        hy = HEIGHT//2
        b = Building(hx, hy, t, "home")
        buildings.append(b)
        homes.append(b)

    # start units
    for t, home in enumerate(homes):
        for role, n in START_UNITS.items():
            for _ in range(n):
                units.append(Unit(home.x, home.y, t, role, home))

    # seed some food/resources
    for _ in range(MAX_FOOD):
        foods.append(Food(random.randint(8, WIDTH-8), random.randint(8, HEIGHT-8)))
    for _ in range(MAX_RESOURCES):
        rtype = random.choice(RESOURCE_TYPES)
        resources.append(Resource(random.randint(8, WIDTH-8), random.randint(8, HEIGHT-8), rtype))

def spawn_food_and_resources():
    # probabilistic respawn per second
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
    # [team][scav,builder,defender,attacker]
    role_ix = {"scavenger":0,"builder":1,"defender":2,"attacker":3}
    data = [[0,0,0,0] for _ in range(NUM_TEAMS)]
    for u in units:
        if u.role == "reproducer": continue
        data[u.team][ role_ix.get(u.role,0) ] += 1
    return data

def ensure_reproducer_exists():
    # if a team lost its reproducer (e.g., killed), schedule an immediate free spawn at home
    for t in range(NUM_TEAMS):
        home = next((b for b in buildings if b.team==t and b.btype=="home"), None)
        if not home: continue
        has_repro = any(u for u in units if u.team==t and u.role=="reproducer")
        in_queue  = any(role=="reproducer" for _,role in home.respawn_q)
        if not has_repro and not in_queue:
            home.respawn_q.append((1,"reproducer"))

def end_round_and_restart(winner):
    global round_id, meta_state
    # update learning based on survivors
    surv_roles = survivors_by_role()
    meta_state = meta.update_after_round(meta_state, winner, surv_roles)
    meta.save_meta(meta_state)
    # push new weights into config for next round
    config.ROLE_WEIGHTS = meta_state["role_weights"]
    round_id += 1
    spawn_initial_world()

def reproduction_tick():
    """Let each reproducer try to spawn according to current ROLE_WEIGHTS."""
    # cap population
    pops = [0]*NUM_TEAMS
    for u in units:
        if u.role != "reproducer":
            pops[u.team] += 1

    # attempt spawns
    for t in range(NUM_TEAMS):
        if pops[t] >= MAX_TEAM_POP: continue
        home = next((b for b in buildings if b.team==t and b.btype=="home"), None)
        if not home: continue
        # cheap "cooldown": only attempt every 1s
        if tick % FPS != 0: continue
        # need some food in base to spawn fighters/workers
        if home.stock_food < REPRODUCE_FOOD_COST: continue

        weights = config.ROLE_WEIGHTS[t]  # [scav, builder, defender, attacker]
        roles = ["scavenger","builder","defender","attacker"]
        role  = random.choices(roles, weights=weights, k=1)[0]
        # consume and spawn
        home.stock_food -= REPRODUCE_FOOD_COST
        units.append(Unit(home.x, home.y, t, role, home))

def draw_world():
    screen.fill((0,0,0))
    # items
    for r in resources: r.draw(screen)
    for f in foods:     f.draw(screen)
    # buildings then units
    for b in buildings: b.draw(screen)
    for u in units:     u.draw(screen)

    # HUD
    sr = survivors_nonrepro_count()
    txt = f"Round {round_id}  tick:{tick}  A:{sr[0]}  B:{sr[1]}  " \
          f"wA:{config.ROLE_WEIGHTS[0]}  wB:{config.ROLE_WEIGHTS[1]}"
    screen.blit(font.render(txt, True, (200,200,200)), (4,4))

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

        # periodic resource/food respawn
        spawn_food_and_resources()

        # buildings update
        for b in list(buildings):
            allies = [u for u in units if u.team==b.team]
            enemies = [u for u in units if u.team!=b.team and u.role!="reproducer"]
            b.update(allies, enemies, buildings, foods)

        # ensure there is always a reproducer
        ensure_reproducer_exists()

        # reproduction attempts (based on learned weights)
        reproduction_tick()

        # units update (remove dead)
        alive=[]
        for u in units:
            if u.update(foods, resources, buildings, units):
                alive.append(u)
        # NOTE: dead units can queue respawns on their home; homes handle it.
        # keep reproducers from drifting if something nudged them
        units[:] = alive

        # end-of-round rules
        sr = survivors_nonrepro_count()
        alive_teams = [i for i,c in enumerate(sr) if c>0]
        if len(alive_teams) == 1:
            end_round_and_restart(alive_teams[0])
        elif len(alive_teams) == 0 and tick > FPS*8:  # nobody left (except repros) for a while
            end_round_and_restart(None)
        elif tick >= ROUND_MAX_TICKS:
            # choose winner by most non-repro population, tie→most buildings, else draw
            if sr[0] != sr[1]:
                winner = 0 if sr[0] > sr[1] else 1
            else:
                b0 = sum(1 for b in buildings if b.team==0 and b.btype!="home")
                b1 = sum(1 for b in buildings if b.team==1 and b.btype!="home")
                winner = (0 if b0>b1 else 1) if b0!=b1 else None
            end_round_and_restart(winner)

        draw_world()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
