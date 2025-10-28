# analysis/visualization_streaming.py
import os
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import glob, json, random, sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pyarrow.parquet as pq

FIGDIR = Path("results/figures")
FIGDIR.mkdir(parents=True, exist_ok=True)

# ---------- TUNABLES ----------
RAW_GLOB = "results/raw/*.parquet"
MAX_FILES = 80          # sample at most this many runs
SAMPLE_PER_FILE = 5000  # sample this many rows per selected run
MAX_PER_STRAT = 150000  # cap rows per strategy globally (prevents runaway memory)
RNG_SEED = 42
# ------------------------------

random.seed(RNG_SEED)

def strategy_from_manifest(run_id: str):
    mp = Path(f"results/agg/{run_id}.manifest.json")
    if not mp.exists():
        return "NA"
    try:
        cfg = json.loads(mp.read_text()).get("cfg", {})
        return cfg.get("mcp", {}).get("strategy", "NA")
    except Exception:
        return "NA"

def savefig(name):
    plt.tight_layout()
    plt.savefig(FIGDIR / f"{name}.png", dpi=180)
    plt.close()

files = sorted(glob.glob(RAW_GLOB))
if not files:
    print(f"[WARN] No files match {RAW_GLOB}", file=sys.stderr)
    sys.exit(0)

# Downselect files to keep memory bounded
if len(files) > MAX_FILES:
    random.shuffle(files)
    files = files[:MAX_FILES]

# Reservoir-like bounded collectors
lat_by_strat = {}
stale_by_strat = {}

def bounded_extend(bucket: dict, key: str, arr: np.ndarray, cap: int):
    if key not in bucket:
        bucket[key] = np.empty((0,), dtype=float)
    remaining = cap - bucket[key].size
    if remaining <= 0: 
        return
    if arr.size > remaining:
        arr = arr[:remaining]
    bucket[key] = np.concatenate([bucket[key], arr])

for p in files:
    run_id = Path(p).stem
    strat = strategy_from_manifest(run_id)

    try:
        t_lat = pq.read_table(p, columns=["latency_ms"])
    except Exception as e:
        print(f"[WARN] skip {p}: {e}", file=sys.stderr)
        continue

    n = t_lat.num_rows
    if n == 0: 
        continue

    # draw random indices (without reading full columns into pandas)
    k = min(SAMPLE_PER_FILE, n)
    idx = np.sort(np.random.default_rng(RNG_SEED).choice(n, size=k, replace=False))

    lat_chunk = t_lat.column("latency_ms").to_numpy()[idx]
    bounded_extend(lat_by_strat, strat, lat_chunk.astype(float), MAX_PER_STRAT)

    # staleness (optional, only if exists)
    try:
        t_stale = pq.read_table(p, columns=["staleness_ms"])
        stale_col = t_stale.column("staleness_ms").to_numpy()
        if stale_col is not None and len(stale_col) == n:
            bounded_extend(stale_by_strat, strat, stale_col[idx].astype(float), MAX_PER_STRAT)
    except Exception:
        pass

# ---- Figure 05: Staleness boxplot (sampled) ----
if any(v.size > 0 for v in stale_by_strat.values()):
    data, labels = [], []
    for strat, arr in sorted(stale_by_strat.items()):
        if arr.size == 0: continue
        data.append(arr)
        labels.append(strat)
    if data:
        plt.figure()
        plt.boxplot(data, labels=labels, showfliers=False)
        plt.ylabel("Staleness (ms)"); plt.title("Staleness by Strategy (sampled)")
        savefig("05_staleness_boxplot_by_strategy_sampled")
        print("Saved 05_staleness_boxplot_by_strategy_sampled.png")

# ---- Figure 06: Latency CDF (sampled) ----
if any(v.size > 0 for v in lat_by_strat.values()):
    plt.figure()
    for strat, arr in sorted(lat_by_strat.items()):
        x = np.sort(arr)
        y = np.linspace(0, 1, len(x), endpoint=True)
        plt.plot(x, y, label=strat)
    plt.xlabel("Latency (ms)"); plt.ylabel("CDF")
    plt.title("Latency CDF by Strategy (sampled)")
    plt.legend()
    savefig("06_latency_cdf_by_strategy_sampled")
    print("Saved 06_latency_cdf_by_strategy_sampled.png")

print("Done (streamed).")
