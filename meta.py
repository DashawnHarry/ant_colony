import json, os, random
from typing import List
from config import META_FILE, NUM_TEAMS

def _default():
    return {
        "role_weights": [[5,2,2,1] for _ in range(NUM_TEAMS)],
        "rounds": 0
    }

def load_meta():
    if not os.path.exists(META_FILE):
        return _default()
    try:
        with open(META_FILE, "r") as f:
            data = json.load(f)
        # sanity
        if "role_weights" not in data or len(data["role_weights"]) != NUM_TEAMS:
            data = _default()
        return data
    except Exception:
        return _default()

def save_meta(data):
    try:
        with open(META_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def _normalize(w):
    s = sum(w)
    return [x/s*10.0 for x in w] if s>0 else [2.5,2.5,2.5,2.5]

def update_after_round(meta, winner_team: int, survivors_by_role: List[List[int]]):
    """Very small 'learning': increase weight for roles that survived for the winner;
       slight random jitter for exploration; normalize to about sum=10."""
    if winner_team is None:
        # draw → tiny jitter for both
        for t in range(NUM_TEAMS):
            meta["role_weights"][t] = _normalize([max(0.5, w*(1.0 + random.uniform(-0.03,0.03)))
                                                  for w in meta["role_weights"][t]])
        meta["rounds"] += 1
        return meta

    # winner boosted toward its survivor composition
    surv = survivors_by_role[winner_team]
    base = meta["role_weights"][winner_team]
    # map surv counts (scav,builder,defender,attacker) to multiplier
    tot = sum(surv) or 1
    boost = [1.0 + 0.10*(c/tot) for c in surv]
    neww = [max(0.3, b*m) for b,m in zip(base, boost)]
    # small randomization
    neww = [w*(1.0 + random.uniform(-0.02,0.04)) for w in neww]
    meta["role_weights"][winner_team] = _normalize(neww)

    # loser(s) get gentle shake-up
    for t in range(NUM_TEAMS):
        if t == winner_team: continue
        w = meta["role_weights"][t]
        w = [max(0.3, x*(1.0 + random.uniform(-0.05,0.05))) for x in w]
        meta["role_weights"][t] = _normalize(w)

    meta["rounds"] += 1
    return meta
