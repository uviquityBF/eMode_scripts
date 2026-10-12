"""Recompute EMode-free quantities of refined crossings from their field exports, after a change
to shg_physics (labels, NCE term split, core power fraction). Rewrites crossings.csv in place;
the original SH label is kept once as sh_label_old. Screened rows have no exports and keep
their in-scan values.

Also (2026-10-12) adds aln_pump_loss_dB_per_m / aln_sh_loss_dB_per_m: AlN's own intrinsic bulk
absorption (geometry.aln_core_loss_dB_per_m, confinement-weighted by core_mask, same perturbation
pattern as the existing shell/strip bulk_absorption_loss in survey.py), computed purely from each
crossing's field export -- no EMode re-solve needed. Deliberately ADDITIVE, not merged into the
existing pump_absorption_dB_per_m/sh_absorption_dB_per_m columns: those stay exactly as originally
computed (AlN-lossless baseline, preserved for comparison), so the AlN-lossy total is
pump_absorption_dB_per_m + aln_pump_loss_dB_per_m (and the SH equivalent) computed downstream,
not baked in here. See PLAN.md's 2026-10-12 AlN k-wiring entry.

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
    n, missing = 0, 0
    for i, r in c[c['status'] == 'refined'].iterrows():
        export_path = os.path.join(HERE, r['export_path'])
        if not os.path.exists(export_path):
            # export .npz files are gitignored (runs/*/exports/) -- not every refined crossing's
            # field export is present on every machine (e.g. a run done on the other machine via
            # the shared git repo). Skip rather than crash; rows keep their existing values.
            missing += 1
            continue
        z = np.load(export_path)
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
        gamma_p, gamma_s = sp.power_fraction_in(fp, mask), sp.power_fraction_in(fs, mask)
        c.at[i, 'pump_power_in_core'] = gamma_p
        c.at[i, 'sh_power_in_core'] = gamma_s
        c.at[i, 'pump_edge_ratio'] = sp.lateral_edge_ratio(fp, x)
        c.at[i, 'sh_edge_ratio'] = sp.lateral_edge_ratio(fs, x)
        wl_sh = float(r['wavelength_sh'])
        c.at[i, 'aln_pump_loss_dB_per_m'] = (0.0 if np.isnan(gamma_p) else
            gamma_p * geo.aln_core_loss_dB_per_m(2 * wl_sh))
        c.at[i, 'aln_sh_loss_dB_per_m'] = (0.0 if np.isnan(gamma_s) else
            gamma_s * geo.aln_core_loss_dB_per_m(wl_sh))
        n += 1
    c.to_csv(path, index=False)
    print(f"{run_name}: reprocessed {n} refined crossings" +
          (f" ({missing} skipped, export file missing)" if missing else ""))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'survey_config')
