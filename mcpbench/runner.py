import time, json
from pathlib import Path
from .config import load_config
from .context_store import ContextStore
from .message_router import MessageRouter
from .metrics import Metrics
from .agent import Agent
from .workload import Workload, AccessSampler
from .strategies.broadcast import Broadcast
from .strategies.pubsub import PubSub
from .strategies.pull_on_demand import PullOnDemand
from .strategies.hierarchical_cache import HierarchicalCache
from .strategies.hybrid_adaptive import HybridAdaptive

def _mk_strategy(name, agent_id, store, router, cfg):
    if name == 'PD':
        return PullOnDemand(agent_id, store, router, ttl_seconds=cfg['mcp']['ttl_seconds'])
    if name == 'HC':
        return HierarchicalCache(agent_id, store, router, group_mod=cfg['agents']['group_mod'],
                                 l1_capacity=cfg['mcp']['l1_capacity'], l2_capacity=cfg['mcp']['l2_capacity'])
    if name == 'HA':
        rr = cfg['workload']['read_ratio'] if cfg['workload']['type'] != 'BU' else 0.5
        return HybridAdaptive(agent_id, store, router, cfg['agents']['count'], rr, access_skew=0.9)
    if name == 'PS':
        return PubSub(agent_id, store, router)
    return Broadcast(agent_id, store, router)

def run_experiment(cfg):
    cfg = load_config(cfg)
    rs = cfg['results_dir']; rid = cfg['run_id']
    Path(rs).mkdir(parents=True, exist_ok=True)

    store = ContextStore()
    router = MessageRouter(delay_ms=cfg['mcp']['network_delay_ms'])
    metrics = Metrics(rs, rid, cfg['measurement']['log_interval_seconds'])

    workload = cfg['workload']['type']
    rr = cfg['workload']['read_ratio'] if workload != 'BU' else 0.5
    wl = Workload(workload, cfg['workload']['ops_per_sec'], rr)

    sampler = AccessSampler(n_items=10_000, kind=cfg['access_pattern']['type'],
                            zipf_alpha=cfg['access_pattern'].get('zipf_alpha', 0.99),
                            hotspot_fraction=cfg['access_pattern'].get('hotspot_fraction', 0.05),
                            hotspot_share=cfg['access_pattern'].get('hotspot_share', 0.5),
                            seed=cfg['seed'])

    agents = []
    for i in range(cfg['agents']['count']):
        strat = _mk_strategy(cfg['mcp']['strategy'], i, store, router, cfg)
        agents.append(Agent(i, strat, metrics))

    # INIT
    time.sleep(cfg['measurement']['init_seconds'])

    # WARMUP
    t0 = time.time()
    i = 0
    while time.time() - t0 < cfg['measurement']['warmup_seconds']:
        count, op = wl.next_op(time.time()-t0)
        for _ in range(count):
            aid = i % len(agents); i += 1
            cid = f"doc:{sampler.sample()}"
            agents[aid].step(op, cid, payload="X")
        metrics.tick()

    # MEASURE
    t0 = time.time()
    while time.time() - t0 < cfg['measurement']['measure_seconds']:
        count, op = wl.next_op(time.time()-t0)
        for _ in range(count):
            aid = int(time.time()*1000) % len(agents)
            cid = f"doc:{sampler.sample()}"
            agents[aid].step(op, cid, payload="X")
        metrics.tick()

    # COOLDOWN
    time.sleep(cfg['measurement']['cooldown_seconds'])

    metrics.finalize()
    with open(Path(rs)/"agg"/f"{rid}.manifest.json","w") as f:
        json.dump({"cfg":cfg}, f)
    print("Finished", rid)
