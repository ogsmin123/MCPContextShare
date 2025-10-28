# MCP Context Sharing Benchmark (MS MARCO)

A complete, **working** benchmark and analysis suite to reproduce an empirical evaluation of context sharing strategies
(Broadcast, Publish–Subscribe, Pull‑on‑Demand, Hierarchical Caching, Hybrid Adaptive) on the **MS MARCO passages** dataset.

## 🎯 Research Objective
Systematically evaluate five context sharing strategies across performance, overhead, and consistency metrics using realistic workloads from the MS MARCO dataset to provide evidence-based guidance for multi-agent system design.

## Strategies
- **Broadcast (BC)** – push every write to all agents (strong consistency, high network)
- **Publish–Subscribe (PS)** – topic channels; push to subscribers (eventual consistency)
- **Pull‑on‑Demand (PD)** – fetch on read miss (weak consistency, low network)
- **Hierarchical Caching (HC)** – L1 (agent), L2 (group), L3 (global) caches (eventual)
- **Hybrid Adaptive (HA)** – selects strategy at runtime based on workload/scale

## 🚀 Quick Start
```bash
# Clone repository
git clone https://github.com/ogsmin123/MCPContextShare.git
cd mcp-context-sharing-msmarco
```

## Requirements
- Python 3.11+
- OS: Linux/macOS (tested on Ubuntu 24.04)


### Step 1: Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Step 3: System Configuration
(**Optional Step**, Only needed if planning to create own Curated configuration directory **configs**)

```bash
python scripts/generate_configs.py --out configs/generated --seed 42
```

### Step 4: Dataset (MS MARCO Passages) & Curated Results (758 Configurations)
> MS MARCO is under a Microsoft Research license for research use. You must accept the license on the MS MARCO site.
Place the following under `.data/msmarco/`:
- `collection.tsv`
- `queries.dev.tsv`
- `qrels.dev.tsv`

The dataset can be dowloaded from official website of **MS Marco**:https://microsoft.github.io/msmarco/
OR from Author's kaggle public dataset location: https://www.kaggle.com/datasets/ogsmin/mcpcontextshare-data

Once downloaded place the data directory into your project directory. 
**There is no need for you to use this data, as we have already created curated 758 configuration from this data set and stored in results folder.**
The results folder can be downloaded from Author's Kaggle public dataset location: https://www.kaggle.com/datasets/ogsmin/mcpcontextshare-results

Once downloaded place the results directory into your project directory. The results 
```
results/
├── agg                 # Curated per-second aggregates (CSV) from MS Marco dataset                 
│   ├── C001.csv
│   ├── C001.manifest.json
........
├── raw/                # per-operation logs (Parquet) from MS Marco dataset
│   └── C001.parquet    
........
├── figures/            # generated figures (PNG/SVG)
```

### Step 5: Run experiments
(**Optional Step**, Only needed if planning to create own Curated results directory **results**)

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

### Step 6: Generate Visualizations

```bash
python analysis/aggregate_results.py
python analysis/statistical_tests.py
python analysis/visualization.py
```
Generates:
- `tables/summary.csv`
- figures in `results/figures/` (latency histogram; extend as needed)


## Directory Structure
```
mcp-context-sharing-msmarco/
├─ README.md
├─ requirements.txt           # Dependencies
├─ requirements-py312.txt     # Dependencies for Python 3.12
├─ setup.sh                   # Env Setup
├─ configs/                   # Configurations
│ └─ default.yaml
│ └─ generated          
│    └─ C001.yaml
.......
├─ scripts/                  # Scripts for generating configs and running experiment
│ ├─ generate_configs.py
│ └─ run_all_experiments.py
├─ mcpbench/                 # Primary code base directory
│ ├─ __init__.py
│ ├─ config.py
│ ├─ utils.py
│ ├─ context_store.py
│ ├─ message_router.py
│ ├─ agent.py
│ ├─ workload.py
│ ├─ metrics.py
│ └─ strategies/            # Different Strategy code base directory
│    ├─ base.py
│    ├─ broadcast.py
│    ├─ pubsub.py
│    ├─ pull_on_demand.py
│    ├─ hierarchical_cache.py
│    └─ hybrid_adaptive.py
├─ analysis/               # Scripts for generating visualization.
│ ├─ aggregate_results.py
│ ├─ statistical_tests.py
│ └─ visualization.py
```
