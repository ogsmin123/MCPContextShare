# MCP Context Sharing Benchmark (MS MARCO)

A complete, **working** benchmark and analysis suite to reproduce an empirical evaluation of context sharing strategies
(Broadcast, Publish–Subscribe, Pull‑on‑Demand, Hierarchical Caching, Hybrid Adaptive) on the **MS MARCO passages** dataset.

## Strategies
- **Broadcast (BC)** – push every write to all agents (strong consistency, high network)
- **Publish–Subscribe (PS)** – topic channels; push to subscribers (eventual consistency)
- **Pull‑on‑Demand (PD)** – fetch on read miss (weak consistency, low network)
- **Hierarchical Caching (HC)** – L1 (agent), L2 (group), L3 (global) caches (eventual)
- **Hybrid Adaptive (HA)** – selects strategy at runtime based on workload/scale

## Requirements
- Python 3.11+
- OS: Linux/macOS (tested on Ubuntu 24.04)

```bash
bash setup.sh
source .venv/bin/activate
```

## Dataset (MS MARCO Passages)
> MS MARCO is under a Microsoft Research license for research use. You must accept the license on the MS MARCO site.
Place the following under `.data/msmarco/`:
- `collection.tsv`
- `queries.dev.tsv`
- `qrels.dev.tsv`

Then optionally create a 100k sample:
```bash
python scripts/download_msmarco.py --out .data/msmarco --sample 100000
```

## Generate experiment configs
```bash
python scripts/generate_configs.py --out configs/generated --seed 42
```

## Run experiments
```bash
# single config
python scripts/run_all_experiments.py --config configs/default.yaml
# batch
python scripts/run_all_experiments.py --glob "configs/generated/*.yaml"
```

Each run includes: 5s init, 30s warmup (not measured), 300s measurement, 10s cooldown.

Outputs:
- per‑operation logs → `results/raw/*.parquet`
- per‑second aggregates → `results/agg/*.csv`
- manifest → `results/agg/<run_id>.manifest.json`

## Analyze & visualize
```bash
python analysis/aggregate_results.py
python analysis/statistical_tests.py
python analysis/visualization.py
```

Generates:
- `tables/summary.csv`
- figures in `results/figures/` (latency histogram; extend as needed)

## Repro tips
- Use `--seed 42` anywhere for determinism
- Pin deps via `requirements.txt`
- Hardware/env snapshot saved in `manifest.json`

## License
MIT (see LICENSE)
