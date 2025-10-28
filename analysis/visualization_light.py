# analysis/visualization_light.py
import os
os.environ.setdefault("MPLBACKEND", "Agg")  # headless & lighter

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

FIGDIR = Path("results/figures")
FIGDIR.mkdir(parents=True, exist_ok=True)

# Always use the small table produced by aggregate_results.py
summary_path = Path("tables/summary_enriched.csv")
if not summary_path.exists():
    raise SystemExit("tables/summary_enriched.csv not found. Run: python analysis/aggregate_results.py")

summary = pd.read_csv(summary_path)

def savefig(name):
    plt.tight_layout()
    plt.savefig(FIGDIR / f"{name}.png", dpi=180)
    plt.close()

# 01 Throughput by strategy (mean ± std)
plt.figure()
g = summary.groupby('strategy')['throughput_ops_s']
x = g.mean().index.tolist(); y = g.mean().values; yerr = g.std().fillna(0).values
plt.bar(range(len(x)), y, yerr=yerr)
plt.xticks(range(len(x)), x); plt.ylabel('Throughput (ops/s)')
plt.title('Throughput by Strategy (mean ± std)')
savefig('01_throughput_by_strategy')

# 02 p95 latency by strategy (mean ± std)
plt.figure()
g = summary.groupby('strategy')['p95']
x = g.mean().index.tolist(); y = g.mean().values; yerr = g.std().fillna(0).values
plt.bar(range(len(x)), y, yerr=yerr)
plt.xticks(range(len(x)), x); plt.ylabel('Latency p95 (ms)')
plt.title('Latency p95 by Strategy (mean ± std)')
savefig('02_p95_by_strategy')

# 03 Scaling: throughput vs agents
plt.figure()
for strat, sdf in summary.groupby('strategy'):
    s = sdf.groupby('agents', dropna=True)['throughput_ops_s'].mean().sort_index()
    if len(s): plt.plot(s.index, s.values, marker='o', label=strat)
plt.xlabel('Agents'); plt.ylabel('Throughput (ops/s)')
plt.title('Scaling: Throughput vs Agents'); plt.legend()
savefig('03_scaling_throughput_vs_agents')

# 04 Pareto: throughput vs p95
plt.figure()
for strat, sdf in summary.groupby('strategy'):
    plt.scatter(sdf['p95'], sdf['throughput_ops_s'], alpha=0.7, label=strat)
plt.xlabel('Latency p95 (ms)'); plt.ylabel('Throughput (ops/s)')
plt.title('Pareto: Throughput vs p95 Latency'); plt.legend()
savefig('04_pareto_throughput_vs_p95')

# 07 Heatmap p95 vs (agents, context) per strategy
for strat, sdf in summary.groupby('strategy'):
    pv = sdf.pivot_table(index='agents', columns='context_tokens', values='p95', aggfunc='mean')
    if pv.empty: continue
    plt.figure()
    plt.imshow(pv.values, aspect='auto', origin='lower')
    plt.xticks(range(len(pv.columns)), pv.columns)
    plt.yticks(range(len(pv.index)), pv.index)
    plt.colorbar(label='p95 (ms)')
    plt.xlabel('Context tokens'); plt.ylabel('Agents')
    plt.title(f'Heatmap p95 (Agents × Context) – {strat}')
    savefig(f'07_heatmap_p95_agents_context_{strat}')

print("Saved figures (light): 01, 02, 03, 04, 07 → results/figures/")
