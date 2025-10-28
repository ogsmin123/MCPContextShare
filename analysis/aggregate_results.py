# analysis/aggregate_results.py
import argparse, glob, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

def is_valid_parquet(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 16:
            return False
        pq.read_metadata(path)
        return True
    except Exception:
        return False

def per_run(df: pd.DataFrame, rid: str) -> dict:
    duration_s = max(1.0, (df['end'].max() - df['start'].min()))
    lat = df['latency_ms'].values
    return {
        'run_id': rid,
        'p50': float(np.percentile(lat, 50)),
        'p95': float(np.percentile(lat, 95)),
        'p99': float(np.percentile(lat, 99)),
        'throughput_ops_s': float(len(df) / duration_s),
        'staleness_ms_mean': float(df.get('staleness_ms', pd.Series([0])).mean()),
        'conflict_rate': float(df.get('conflict', pd.Series([0])).mean()),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', default='results/raw/*.parquet')
    ap.add_argument('--out', default='tables/summary.csv')
    args = ap.parse_args()

    files = sorted(glob.glob(args.raw))
    Path('tables').mkdir(exist_ok=True)

    rows = []
    bad = []
    for p in files:
        path = Path(p)
        if not is_valid_parquet(path):
            bad.append(p); continue
        try:
            df = pd.read_parquet(p, engine='pyarrow')
        except Exception as e:
            print(f"[WARN] Skipping unreadable parquet: {p} ({e})", file=sys.stderr)
            bad.append(p); continue
        if df.empty or 'latency_ms' not in df.columns:
            bad.append(p); continue
        rows.append(per_run(df, path.stem))

    if not rows:
        pd.DataFrame(columns=['run_id','p50','p95','p99','throughput_ops_s','staleness_ms_mean','conflict_rate']).to_csv(args.out, index=False)
        print("No good parquet files found; wrote empty summary to", args.out)
        return

    out = pd.DataFrame(rows).sort_values('run_id')
    out.to_csv(args.out, index=False)
    print("Wrote", args.out, "with", len(out), "rows.")

    # Enrich with manifests
    def load_cfg(rid):
        mp = Path(f'results/agg/{rid}.manifest.json')
        if mp.exists():
            try:
                return pd.json_normalize([__import__('json').loads(mp.read_text()).get('cfg', {})])
            except Exception:
                pass
        return pd.json_normalize([{}])

    cfgs = []
    for rid in out['run_id']:
        c = load_cfg(rid); c['run_id'] = rid; cfgs.append(c)
    cfgdf = pd.concat(cfgs, ignore_index=True)
    joined = out.merge(cfgdf, on='run_id', how='left')
    joined['strategy'] = joined.get('mcp.strategy', 'NA')
    joined['agents'] = joined.get('agents.count', None)
    joined['context_tokens'] = joined.get('context.size_tokens', None)
    joined['workload'] = joined.get('workload.type', None)
    joined['access_pattern'] = joined.get('access_pattern.type', None)

    joined.to_csv('tables/summary_enriched.csv', index=False)

    # Per-strategy
    strat = joined.groupby('strategy').agg(
        runs=('run_id','count'),
        p95_mean=('p95','mean'),
        p95_std=('p95','std'),
        thr_mean=('throughput_ops_s','mean'),
        thr_std=('throughput_ops_s','std'),
        stale_mean=('staleness_ms_mean','mean')
    ).reset_index()
    strat.to_csv('tables/per_strategy.csv', index=False)

    # Strategy × agents
    sa = joined.groupby(['strategy','agents']).agg(
        runs=('run_id','count'),
        p95_mean=('p95','mean'),
        thr_mean=('throughput_ops_s','mean')
    ).reset_index()
    sa.to_csv('tables/per_strategy_agents.csv', index=False)

    # Best per agents (lowest p95)
    best = joined.loc[joined.groupby('agents')['p95'].idxmin()].sort_values('agents')
    best[['run_id','strategy','agents','p95','throughput_ops_s']].to_csv('tables/best_by_agents.csv', index=False)

    print("Wrote grouped tables to tables/: summary_enriched.csv, per_strategy.csv, per_strategy_agents.csv, best_by_agents.csv")

if __name__ == '__main__':
    main()
