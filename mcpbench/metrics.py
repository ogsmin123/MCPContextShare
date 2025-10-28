import csv, time
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import pyarrow as pa, pyarrow.parquet as pq
import psutil

@dataclass
class SysSample:
    ts: float
    cpu: float
    mem: float

class Metrics:
    def __init__(self, results_dir: str, run_id: str, log_interval: int):
        self.results_dir = Path(results_dir)
        self.run_id = run_id
        self.log_interval = log_interval
        self.ops = []
        self.persec = []
        (self.results_dir/"raw").mkdir(parents=True, exist_ok=True)
        (self.results_dir/"agg").mkdir(parents=True, exist_ok=True)
        self._last_flush = time.time()

    def record_op(self, opres):
        self.ops.append(opres)

    def tick(self):
        now = time.time()
        if now - self._last_flush >= self.log_interval:
            self._last_flush = now
            self.persec.append(SysSample(now, psutil.cpu_percent(), psutil.virtual_memory().percent))

    def finalize(self):
        rows = [{
            'op_id': o.op_id, 'op': o.op, 'cid': o.cid,
            'start': o.start, 'end': o.end, 'latency_ms': (o.end - o.start)*1000.0,
            'success': o.success, 'staleness_ms': o.staleness_ms,
            'conflict': o.conflict, 'version_seen': o.version_seen
        } for o in self.ops]
        table = pa.Table.from_pandas(pd.DataFrame(rows))
        pq.write_table(table, self.results_dir/"raw"/f"{self.run_id}.parquet")

        with open(self.results_dir/"agg"/f"{self.run_id}.csv", 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['ts','cpu','mem'])
            for s in self.persec:
                w.writerow([s.ts, s.cpu, s.mem])
