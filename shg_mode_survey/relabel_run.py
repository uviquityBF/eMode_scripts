"""Recompute SH/pump labels of refined crossings from their field exports (after a change to
shg_physics.mode_label). Rewrites crossings.csv in place (old label kept as sh_label_old).
Usage: python relabel_run.py <run_name>"""

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shg_physics as sp  # noqa: E402


def main(run_name):
    path = os.path.join(HERE, 'runs', run_name, 'crossings.csv')
    c = pd.read_csv(path)
    if 'sh_label_old' not in c:
        c['sh_label_old'] = c['sh_label']
    for i, r in c[c['status'] == 'refined'].iterrows():
        z = np.load(os.path.join(HERE, r['export_path']))
        f = {k: z[f'sh_{k}'] for k in ('Ex', 'Ey', 'Ez')}
        c.at[i, 'sh_label'] = sp.mode_label(f, r['sh_te_fraction'], z['core_mask'])
    c.to_csv(path, index=False)
    ch = c[(c['status'] == 'refined') & (c['sh_label'] != c['sh_label_old'])]
    print(f"{len(ch)} of {(c['status'] == 'refined').sum()} refined labels changed")
    print(ch[['sh_label_old', 'sh_label']].value_counts().head(30).to_string())


if __name__ == '__main__':
    main(sys.argv[1])
