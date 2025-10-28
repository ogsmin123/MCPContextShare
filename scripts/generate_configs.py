import argparse, itertools, yaml
from pathlib import Path

STRATS = ["BC","PS","PD","HC","HA"]
AGENTS = [5,10,25,50,100]
SIZES = [100,500,2000]
WORKLOADS = {
  'RH': {'ops_per_sec': 10, 'read_ratio': 0.8},
  'WH': {'ops_per_sec': 8,  'read_ratio': 0.3},
  'BA': {'ops_per_sec': 10, 'read_ratio': 0.5},
  'BU': {'ops_per_sec': 10, 'read_ratio': None},
}
PATTERNS = [('uniform', {}), ('zipf', {'zipf_alpha': 0.99}), ('hotspot', {'hotspot_fraction':0.05,'hotspot_share':0.5})]

def main(out):
    Path(out).mkdir(parents=True, exist_ok=True)
    i = 0
    for s, a, c, (pat, extra) in itertools.product(STRATS, AGENTS, SIZES, PATTERNS):
        for wl, cfg in WORKLOADS.items():
            i += 1
            d = {
              'seed': 42,
              'results_dir': 'results',
              'run_id': f'C{i:03d}',
              'workload': { 'type': wl, **cfg },
              'access_pattern': { 'type': pat, **extra },
              'agents': { 'count': a, 'group_mod': 5 },
              'context': { 'size_tokens': c },
              'mcp': {
                'strategy': s, 'network_delay_ms': 5, 'ttl_seconds': 60,
                'l1_capacity': 100, 'l2_capacity': 1000
              },
              'measurement': {
                'init_seconds': 5, 'warmup_seconds': 30,
                'measure_seconds': 300, 'cooldown_seconds': 10,
                'log_interval_seconds': 1
              }
            }
            with open(Path(out)/f"{d['run_id']}.yaml","w") as f:
                yaml.safe_dump(d,f, sort_keys=False)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()
    main(args.out)
