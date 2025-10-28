# scripts/run_all_experiments.py
import argparse, glob, os, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from time import perf_counter

# Avoid NumPy/BLAS thread oversubscription per worker
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

def _run_one(cfg_path: str):
    # Import inside worker to keep state isolated in each process
    from mcpbench.runner import run_experiment
    return run_experiment(cfg_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', help='Single YAML config path')
    ap.add_argument('--glob', help='Glob for multiple YAML configs (e.g., "configs/generated/*.yaml")')
    ap.add_argument('--workers', type=int, default=1, help='Number of parallel workers (processes)')
    args = ap.parse_args()

    if args.config:
        cfgs = [args.config]
    elif args.glob:
        cfgs = sorted(glob.glob(args.glob))
    else:
        raise SystemExit('Provide --config or --glob')

    t0 = perf_counter()
    if args.workers <= 1 or len(cfgs) == 1:
        for c in cfgs:
            _run_one(c)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(_run_one, c): c for c in cfgs}
            for fut in as_completed(futs):
                c = futs[fut]
                try:
                    fut.result()
                except Exception as e:
                    print(f"[ERROR] {c}: {e}", file=sys.stderr)
    dt = perf_counter() - t0
    print(f"Completed {len(cfgs)} run(s) in {dt:.2f}s with workers={args.workers}")

if __name__ == '__main__':
    main()
