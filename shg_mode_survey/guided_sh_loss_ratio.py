"""Sensitivity of the guided-SHG rows to the (unmeasured) SH-to-pump loss ratio, EMode-free (crossings.csv only).

The survey's SH loss is NOT measured: it is scattering + absorption mechanisms + a calibrated 100 dB/cm film
term. The working engineering rule of thumb is Loss_SH = 5-10 x Loss_pump (scattering ~ 1/lambda^2..3). Here
the SH loss of every refined, window-filtered crossing is replaced by

    alpha_SH(r) = r * alpha_pump  +  alpha_SH,material       [dB/m]

with alpha_pump = pump_scattering + pump_absorption (stored per crossing), and alpha_SH,material =
sh_absorption - sh_calibrated (the strip's own bulk k at 225 nm, nan -> 0; zero for the plain-AlN rows, where
sh_absorption IS the calibrated term). The best crossing is re-selected for every r (max of eta * L_eff^2
maximised over L <= 0.2 m, guided_loss_cases.peak_pct_per_W). 'as_run' = the stored loss, which for the AlN
ridge corresponds to r = alpha_SH/alpha_pump (printed). Only the AlN-only rows (1, 1.2) respond; strip rows
(3-6) are dominated by the strip material's bulk k at 225 nm (1e4..3e5 dB/cm) -- a separate uncertainty
tracked by the ScAlN loss cases -- so r barely moves them.
Usage: python guided_sh_loss_ratio.py       (writes runs/guided_sh_loss_ratio.csv)
"""
import math
import os

import numpy as np
import pandas as pd

import cerenkov_fom as fom
from guided_loss_cases import peak_pct_per_W

HERE = os.path.dirname(os.path.abspath(__file__))
RATIOS = [1, 2, 3, 5, 7.5, 10, 15, 20]


def _z(x):
    return 0.0 if pd.isna(x) else float(x)


def crossings(run):
    c = pd.read_csv(os.path.join(HERE, 'runs', run, 'crossings.csv'))
    c = c[c['status'] == 'refined'].copy()
    edge = c['sh_edge_ratio'] if 'sh_edge_ratio' in c else pd.Series(np.nan, index=c.index)
    if 'sh_edge_ratio_screen' in c:
        edge = edge.fillna(c['sh_edge_ratio_screen'])
    return c[(edge <= fom.MAX_SH_EDGE) | edge.isna()].reset_index(drop=True)


def evaluate(c, r):
    best = None
    for _, x in c.iterrows():
        a_p = _z(x['pump_scattering_dB_per_m']) + _z(x['pump_absorption_dB_per_m'])
        a_mat = max(_z(x['sh_absorption_dB_per_m']) - _z(x.get('sh_calibrated_dB_per_m')), 0.0)
        a_s = (_z(x['sh_scattering_dB_per_m']) + _z(x['sh_absorption_dB_per_m'])) if r is None else r * a_p + a_mat
        peak, L, _ = peak_pct_per_W(float(x['eta_pct_per_W_cm2']), a_p, a_s)
        if best is None or peak > best['peak_pct_per_W']:
            best = {'peak_pct_per_W': peak, 'L_opt_mm': L * 1e3, 'pair': f"{x['pump_label']}->{x['sh_label']}",
                    'lambda_sh_nm': float(x['wavelength_sh']), 'pump_loss_dB_cm': a_p / 100,
                    'sh_loss_dB_cm': a_s / 100, 'ratio_sh_over_pump': a_s / a_p if a_p else np.nan}
    return best


if __name__ == '__main__':
    rows = []
    for run, (label, _) in fom.GUIDED.items():
        c = crossings(run)
        for r in [None] + RATIOS:
            b = evaluate(c, r)
            rows.append({'run': run, 'row': label, 'r': 'as_run' if r is None else r, **b})
    df = pd.DataFrame(rows)
    out = os.path.join(HERE, 'runs', 'guided_sh_loss_ratio.csv')
    df.to_csv(out, index=False)
    pd.set_option('display.width', 220)
    for run in ('row1_ridge', 'row1_2_rib_unloaded'):
        t = df[df.run == run]
        print(f"\n{fom.GUIDED[run][0]}: best peak efficiency [%/W] vs Loss_SH/Loss_pump")
        print(t[['r', 'pair', 'lambda_sh_nm', 'pump_loss_dB_cm', 'sh_loss_dB_cm', 'ratio_sh_over_pump', 'L_opt_mm',
                 'peak_pct_per_W']].to_string(index=False, float_format=lambda x: f'{x:.4g}'))
    print('\nAll guided rows: best peak [%/W] (as_run | r=2 | 5 | 10 | 20):')
    for run, (label, _) in fom.GUIDED.items():
        t = df[df.run == run].set_index('r')['peak_pct_per_W']
        print(f"  {label:36s} " + ' | '.join(f"{t.loc[k]:.2e}" for k in ('as_run', 2, 5, 10, 20)))
    print('wrote', out)
