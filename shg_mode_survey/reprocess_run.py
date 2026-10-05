"""Recompute EMode-free quantities of refined crossings from their field exports, after a change
to shg_physics (labels, NCE term split, core power fraction). Rewrites crossings.csv in place;
the original SH label is kept once as sh_label_old. Screened rows have no exports and keep
their in-scan values.

Usage: python reprocess_run.py <run_name> [config_module]
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geometry as geo  # noqa: E402
import shg_physics as sp  # noqa: E402


def main(run_name, config_module='survey_config'):
    cfg = importlib.import_module(config_module).SETTINGS
    path = os.path.join(HERE, 'runs', run_name, 'crossings.csv')
    c = pd.read_csv(path)
    if 'sh_label_old' not in c:
        c['sh_label_old'] = c['sh_label']
    for col in ('sh_label', 'sh_label_old'):
        c[col] = c[col].astype(object)
    n = 0
    for i, r in c[c['status'] == 'refined'].iterrows():
        z = np.load(os.path.join(HERE, r['export_path']))
        x, y, mask = z['x'], z['y'], z['core_mask']
        dA = sp.cell_areas_m2(x, y)
        geom = geo.make_geometry(r['family'], __import__('json').loads(r['params']))
        d = geom.chi2_map(x, y, cfg['d_tensors_pm'])
        fs = {k: z[f'sh_{k}'].astype(complex) for k in ('Ex', 'Ey', 'Ez', 'Hx', 'Hy')}
        fp = {k: z[f'pump_{k}'].astype(complex) for k in ('Ex', 'Ey', 'Ez', 'Hx', 'Hy')}
        fs['Sz'], fp['Sz'] = z['sh_Sz'], z['pump_Sz']
        c.at[i, 'sh_label'] = sp.mode_label(fs, r['sh_te_fraction'], mask)
        for k, v in sp.overlap_terms(fs, fp, d, dA, r['wavelength_sh']).items():
            c.at[i, k] = v
        c.at[i, 'pump_power_in_core'] = sp.power_fraction_in(fp, mask)
        c.at[i, 'sh_power_in_core'] = sp.power_fraction_in(fs, mask)
        c.at[i, 'pump_edge_ratio'] = sp.lateral_edge_ratio(fp, x)
        c.at[i, 'sh_edge_ratio'] = sp.lateral_edge_ratio(fs, x)
        n += 1
    c.to_csv(path, index=False)
    print(f"{run_name}: reprocessed {n} refined crossings")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'survey_config')
