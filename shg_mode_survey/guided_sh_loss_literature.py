"""Guided-SHG efficiency under literature-informed SH-loss scenarios, EMode-free (crossings.csv only).

Companion to guided_sh_loss_ratio.py. That script replaces the whole SH loss by r * (pump loss); this one splits the
SH loss into a scattering part that scales from the stored PUMP SCATTERING and an additive SH absorption term:

    alpha_SH = r_scat * pump_scattering + A_abs  [+ the strip material's own bulk k, as in guided_sh_loss_ratio.py]

Literature inputs (2026-11 AlN study, see runs/Literature_Loss_Report.docx):
  r_scat   : Liu 2018 supplement gives AlN ring loss ~ lambda^-3 (lambda^-3.6 without interface scattering); 450 -> 225 nm is a
             wavelength ratio of 2, so r_scat ~ 8 (band 5-12). Corato-Zanarella's measured sidewall scattering per overlap
             follows lambda^-2.3 (+-0.6) over 461-780 nm (SiN), i.e. r ~ 5 (band 3-8). The user's rule of thumb is 5-10.
  A_abs    : bulk AlN absorption at the SH (all assumed, none measured on our film):
             0    -- scattering only
             43   -- Crystal IS patent claim for the best bulk PVT crystal, alpha < 10 cm-1 at 230 nm (a claim, not peer reviewed)
             100  -- the survey's calibrated working value (inside the 15-680 dB/cm device-output bound)
             300  -- in between
             870  -- Tillner 2020 MOCVD film floor, flat 150-200 cm-1 at 245-400 nm (probably a measurement floor)
Pump loss is left as stored (scattering + interface absorption). Only the AlN-only rows respond (strip rows are dominated
by the strip's bulk k, tracked by the ScAlN loss cases).
Usage: python guided_sh_loss_literature.py     (writes runs/guided_sh_loss_literature.csv)
"""
import os

import numpy as np
import pandas as pd

import cerenkov_fom as fom
from guided_loss_cases import peak_pct_per_W
from guided_sh_loss_ratio import crossings, _z

HERE = os.path.dirname(os.path.abspath(__file__))
R_SCAT = [5.0, 8.0, 12.0]
A_ABS_DB_PER_CM = [0.0, 43.0, 100.0, 300.0, 870.0]
F_PUMP = [1.0, 0.5]   # pump-loss multiplier: 1 = as run; 0.5 ~ literature (Liu 2018: 3.5 dB/cm in an 800 nm ring, 2-3x higher for narrow guides)


def evaluate(c, r_scat, a_abs_db_cm, f_pump=1.0):
    best = None
    for _, x in c.iterrows():
        a_p = f_pump * (_z(x['pump_scattering_dB_per_m']) + _z(x['pump_absorption_dB_per_m']))
        a_mat = max(_z(x['sh_absorption_dB_per_m']) - _z(x.get('sh_calibrated_dB_per_m')), 0.0)
        a_s = r_scat * f_pump * _z(x['pump_scattering_dB_per_m']) + a_abs_db_cm * 100.0 + a_mat
        peak, L, _ = peak_pct_per_W(float(x['eta_pct_per_W_cm2']), a_p, a_s)
        if best is None or peak > best['peak_pct_per_W']:
            best = {'peak_pct_per_W': peak, 'L_opt_mm': L * 1e3, 'pair': f"{x['pump_label']}->{x['sh_label']}",
                    'lambda_sh_nm': float(x['wavelength_sh']), 'pump_loss_dB_cm': a_p / 100, 'sh_loss_dB_cm': a_s / 100}
    return best


if __name__ == '__main__':
    rows = []
    for run, (label, _) in fom.GUIDED.items():
        c = crossings(run)
        for f in F_PUMP:
            for r in R_SCAT:
                for a in A_ABS_DB_PER_CM:
                    b = evaluate(c, r, a, f)
                    rows.append({'run': run, 'row': label, 'f_pump': f, 'r_scat': r, 'A_abs_dB_per_cm': a, **b})
    df = pd.DataFrame(rows)
    out = os.path.join(HERE, 'runs', 'guided_sh_loss_literature.csv')
    df.to_csv(out, index=False)
    pd.set_option('display.width', 220)
    for run in ('row1_ridge', 'row1_2_rib_unloaded'):
        t = df[(df.run == run) & (df.f_pump == 1.0)]
        print(f"\n{fom.GUIDED[run][0]}: best peak efficiency [%/W], pump loss as run  (rows r_scat, columns A_abs dB/cm)")
        print(t.pivot(index='r_scat', columns='A_abs_dB_per_cm', values='peak_pct_per_W').to_string(float_format=lambda x: f'{x:.3g}'))
        print(t[(t.r_scat == 8) & (t.A_abs_dB_per_cm == 100)][['pair', 'lambda_sh_nm', 'pump_loss_dB_cm', 'sh_loss_dB_cm', 'L_opt_mm']].to_string(index=False))
    print('\nAll guided rows, best peak [%/W] at r_scat=8 for A_abs = 0 | 43 | 100 | 300 | 870 dB/cm:')
    for run, (label, _) in fom.GUIDED.items():
        t = df[(df.run == run) & (df.r_scat == 8) & (df.f_pump == 1.0)].set_index('A_abs_dB_per_cm')['peak_pct_per_W']
        print(f"  {label:36s} " + ' | '.join(f"{t.loc[a]:.2e}" for a in A_ABS_DB_PER_CM))
    print('\nAlN ridge, r_scat=8: pump-loss multiplier 1.0 vs 0.5, by A_abs:')
    print(df[(df.run == 'row1_ridge') & (df.r_scat == 8)].pivot(index='f_pump', columns='A_abs_dB_per_cm', values='peak_pct_per_W').to_string(float_format=lambda x: f'{x:.3g}'))
