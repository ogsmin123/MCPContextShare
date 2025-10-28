# analysis/statistical_tests.py
import pandas as pd, itertools
from scipy import stats
from pathlib import Path
import json

summ = pd.read_csv('tables/summary_enriched.csv') if Path('tables/summary_enriched.csv').exists() else pd.read_csv('tables/summary.csv')
if 'strategy' not in summ.columns:
    rows = []
    for rid in summ['run_id']:
        mp = Path(f'results/agg/{rid}.manifest.json')
        row = {'run_id': rid, 'strategy': 'NA'}
        if mp.exists():
            try:
                j = json.loads(mp.read_text()).get('cfg', {})
                row['strategy'] = j.get('mcp',{}).get('strategy','NA')
            except Exception:
                pass
        rows.append(row)
    summ = summ.merge(pd.DataFrame(rows), on='run_id', how='left')

groups = [g['p95'].values for _, g in summ.groupby('strategy') if len(g) > 1]
labels = [k for k, g in summ.groupby('strategy') if len(g) > 1]

if len(groups) >= 2:
    f, p = stats.f_oneway(*groups)
    print("ANOVA p95 across strategies: F=%.4f p=%.4g" % (f, p))
else:
    print("ANOVA skipped (not enough groups).")

pairs = list(itertools.combinations(labels, 2))
m = len(pairs)
rows = []
for a, b in pairs:
    xa = summ[summ['strategy']==a]['p95'].values
    xb = summ[summ['strategy']==b]['p95'].values
    if len(xa) > 1 and len(xb) > 1:
        t, p = stats.ttest_ind(xa, xb, equal_var=False)
        rows.append({'A':a,'B':b,'t':float(t),'p_raw':float(p),'p_bonf':float(min(1.0, p*m))})
pd.DataFrame(rows).to_csv('tables/pairwise_p95_bonferroni.csv', index=False)
print("Wrote tables/pairwise_p95_bonferroni.csv")
