"""Pull refined-crossing sub-figure-of-merit data (overlap_shape, SH-side scattering/absorption
split, etc.) out of one or more survey.py run directories' crossings.csv, for a closer look than
the headline eta_pct_per_W_cm2 ranking gives -- these per-mechanism/per-shape fields are already
computed during refine (see refine_crossing() in survey.py), just never surfaced on their own.
Only `status == 'refined'` rows carry them (screening doesn't solve losses/overlap_shape, too
expensive to do for every screened crossing).

Usage: python extract_subfigure_data.py <run_name> [<run_name> ...] > out.json
"""
import json
import sys

import numpy as np
import pandas as pd

COLS = ['run', 'fingerprint', 'h_core', 'w_core', 'sin_width', 'sin_height',
        'pump_label', 'sh_label', 'wavelength_sh', 'n_eff_pump', 'n_eff_sh',
        'overlap_shape', 'overlap_linear_emode',
        'sh_scattering_dB_per_m', 'sh_absorption_dB_per_m', 'sh_calibrated_dB_per_m',
        'sh_loss_total_dB_per_m',
        'pump_scattering_dB_per_m', 'pump_absorption_dB_per_m', 'pump_loss_total_dB_per_m',
        'eta_pct_per_W_cm2', 'peak_efficiency_pct_per_W', 'L_opt_mm', 'L_eff_mm',
        'A_eff_pump_um2', 'A_eff_sh_um2', 'pump_power_in_core', 'sh_power_in_core',
        'share_d33', 'share_d31', 'share_d15']


def load(run_names):
    frames = []
    for run in run_names:
        d = pd.read_csv(f'runs/{run}/crossings.csv')
        d['run'] = run
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    r = d[d['status'] == 'refined'].copy()

    def geom_params(s):
        p = json.loads(s)
        return p['h_core'], p['w_core'], p['sin_width'], p['sin_height']

    parsed = r['params'].apply(geom_params)
    r['h_core'] = [t[0] for t in parsed]
    r['w_core'] = [t[1] for t in parsed]
    r['sin_width'] = [t[2] for t in parsed]
    r['sin_height'] = [t[3] for t in parsed]
    # runs predating the 2026-10-12 SH-loss calibration (e.g. the pedestal family) have no
    # sh_calibrated_dB_per_m column at all -- 0.0 is the correct value there (calibration genuinely
    # wasn't applied), not a missing-data placeholder.
    if 'sh_calibrated_dB_per_m' not in r.columns:
        r['sh_calibrated_dB_per_m'] = 0.0
    else:
        r['sh_calibrated_dB_per_m'] = r['sh_calibrated_dB_per_m'].fillna(0.0)
    r['sh_loss_total_dB_per_m'] = r['sh_scattering_dB_per_m'].fillna(0) + r['sh_absorption_dB_per_m'].fillna(0)
    r['pump_loss_total_dB_per_m'] = r['pump_scattering_dB_per_m'].fillna(0) + r['pump_absorption_dB_per_m'].fillna(0)
    return r[COLS].replace({np.nan: None})


if __name__ == '__main__':
    runs = sys.argv[1:] or ['row6_hybrid_lateral', 'row6_hybrid_vertical']
    df = load(runs)
    print(json.dumps(df.to_dict(orient='records'), default=str))
