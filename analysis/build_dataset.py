# analysis/build_dataset.py
import glob, json, os, sys, tempfile, shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

RAW_GLOB = "results/raw/*.parquet"
MAN_TPL   = "results/agg/{rid}.manifest.json"
OUT_PARQ  = "tables/runs_merged.parquet"
OUT_CSV   = "tables/runs_merged.csv"   # optional, sampled
CSV_SAMPLE = 0                         # set >0 to sample that many rows per run into CSV

def load_manifest_dict(rid: str) -> dict:
    p = Path(MAN_TPL.format(rid=rid))
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text()).get("cfg", {})
    except Exception:
        return {}

def get(cfg: dict, path: str, default=None):
    cur = cfg
    for k in path.split("/"):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def to_str_array(val, length: int):
    return pa.array([val] * length, type=pa.string())

def main():
    Path("tables").mkdir(exist_ok=True, parents=True)

    files = sorted(glob.glob(RAW_GLOB))
    if not files:
        print(f"[WARN] No input files match {RAW_GLOB}")
        # still create empty parquet with schema so downstream scripts don’t crash
        schema = pa.schema([
            ("run_id", pa.string()),
            ("latency_ms", pa.float64()),
            ("staleness_ms", pa.float64()),
            ("conflict", pa.bool_()),
            ("start", pa.float64()),
            ("end", pa.float64()),
            ("op", pa.string()),
            ("strategy", pa.string()),
            ("agents", pa.int64()),
            ("context_tokens", pa.int64()),
            ("workload", pa.string()),
            ("read_ratio", pa.float64()),
            ("ops_per_sec_cfg", pa.int64()),
            ("access_pattern", pa.string()),
        ])
        with pq.ParquetWriter(OUT_PARQ, schema) as w:
            pass
        print("Wrote empty parquet:", OUT_PARQ)
        return

    tmp_parq = OUT_PARQ + ".tmp"
    writer = None

    # if sampling to CSV, prepare a temp CSV and write header once
    csv_tmp = None
    csv_header_written = False
    if CSV_SAMPLE and CSV_SAMPLE > 0:
        import pandas as pd  # only used if CSV sampling is enabled
        csv_tmp = OUT_CSV + ".tmp"

    try:
        for p in files:
            rid = Path(p).stem
            # read just needed columns (lower memory)
            try:
                table = pq.read_table(
                    p,
                    columns=["op_id", "latency_ms", "staleness_ms", "conflict", "start", "end", "op"],
                )
            except Exception as e:
                print(f"[WARN] skipping unreadable parquet: {p} ({e})", file=sys.stderr)
                continue

            n = table.num_rows
            if n == 0:
                continue

            cfg = load_manifest_dict(rid)

            # Build extra columns as Arrow arrays
            cols = {
                "run_id": to_str_array(rid, n),
                "strategy": to_str_array(get(cfg, "mcp/strategy", "NA"), n),
                "agents": pa.array([get(cfg, "agents/count", None)] * n, type=pa.int64()),
                "context_tokens": pa.array([get(cfg, "context/size_tokens", None)] * n, type=pa.int64()),
                "workload": to_str_array(get(cfg, "workload/type", None), n),
                "read_ratio": pa.array([get(cfg, "workload/read_ratio", None)] * n, type=pa.float64()),
                "ops_per_sec_cfg": pa.array([get(cfg, "workload/ops_per_sec", None)] * n, type=pa.int64()),
                "access_pattern": to_str_array(get(cfg, "access_pattern/type", None), n),
            }

            # Ensure required data columns exist (fill with nulls if missing)
            def ensure(tab, name, pa_type, default=None):
                if name in tab.column_names:
                    return tab[name]
                return pa.chunked_array([pa.array([default] * n, type=pa_type)])

            base_cols = {
                "latency_ms": ensure(table, "latency_ms", pa.float64(), None),
                "staleness_ms": ensure(table, "staleness_ms", pa.float64(), None),
                "conflict": ensure(table, "conflict", pa.bool_(), False),
                "start": ensure(table, "start", pa.float64(), None),
                "end": ensure(table, "end", pa.float64(), None),
                "op": ensure(table, "op", pa.string(), "NA"),
            }

            # Construct final table (order is stable)
            final_table = pa.table({
                "run_id": cols["run_id"],
                "latency_ms": base_cols["latency_ms"],
                "staleness_ms": base_cols["staleness_ms"],
                "conflict": base_cols["conflict"],
                "start": base_cols["start"],
                "end": base_cols["end"],
                "op": base_cols["op"],
                "strategy": cols["strategy"],
                "agents": cols["agents"],
                "context_tokens": cols["context_tokens"],
                "workload": cols["workload"],
                "read_ratio": cols["read_ratio"],
                "ops_per_sec_cfg": cols["ops_per_sec_cfg"],
                "access_pattern": cols["access_pattern"],
            })

            if writer is None:
                writer = pq.ParquetWriter(tmp_parq, final_table.schema)
            writer.write_table(final_table)

            # Optional: write a sampled CSV row-chunk (for quick looks)
            if CSV_SAMPLE and CSV_SAMPLE > 0:
                import pandas as pd
                # convert only this chunk to pandas (still bounded)
                pdf = final_table.to_pandas()
                if len(pdf) > CSV_SAMPLE:
                    pdf = pdf.sample(CSV_SAMPLE, random_state=42)
                if not csv_header_written:
                    pdf.to_csv(csv_tmp, index=False, mode="w")
                    csv_header_written = True
                else:
                    pdf.to_csv(csv_tmp, index=False, mode="a", header=False)

        if writer is not None:
            writer.close()
            # atomic move into place
            shutil.move(tmp_parq, OUT_PARQ)
            print("Wrote", OUT_PARQ)
        else:
            # nothing was written (empty inputs)
            print("[WARN] No rows written; nothing to move")

        if csv_tmp and csv_header_written:
            shutil.move(csv_tmp, OUT_CSV)
            print("Wrote (sampled) CSV", OUT_CSV)

    finally:
        # cleanup temps if something failed
        for tmp in (tmp_parq, csv_tmp or ""):
            if tmp and Path(tmp).exists():
                # if the destination exists we already moved; otherwise leave tmp for debugging
                pass

if __name__ == "__main__":
    main()
