"""Common figure of merit: Cerenkov (row 8) vs the guided-SHG rows, EMode-free (reads CSVs).

Metric: SH-out / pump-in per WATT of pump [%/W], small-conversion limit (conversion linear in pump
power), with the pump's own propagation loss included.
  guided   : `peak_efficiency_pct_per_W` already in each run's crossings.csv  (eta * L_eff^2 at
             L_opt, with pump + SH scattering/absorption, SH loss incl. the calibrated 100 dB/cm term,
             ScAlN/TiO2/SiNx strip k at the project's fitted values). Best 'refined' crossing per row
             that passes the window/box-mode filter (sh_edge_ratio <= 0.02).
  Cerenkov : eff(L) = kappa * L_eff(L)  with  L_eff = (1 - exp(-2 a L)) / (2 a),  a = ln10/10 *
             (pump scattering + absorption [dB/m]) per m, kappa in %/W/cm, L in cm. Reported at
             L = 1 mm, 1 cm and L -> infinity (= kappa / 2a, pump-loss limited). The radiated SH is NOT
             extracted here: multiply by an extraction efficiency (tags 1.0 / 0.5 / 0.1) -- both the
             upward and the substrate path need z-breaking structure (kz = n_p k0 > k0 of air).

Optimism tags carried on every row: loss_case (ScAlN k multiple of the Baumler fit; 'fit' = the
assumption the guided ScAlN rows already use), d33_case (yoshioka = optimistic working value,
frac_x, mbe_like), the 2D numerical-bias flag. Guided rows: their own tags are listed in
GUIDED_TAGS. Usage: python cerenkov_fom.py [cases_csv] [run]
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

import cerenkov_pump_loss as cpl

HERE = os.path.dirname(os.path.abspath(__file__))

GUIDED = {  # run -> (label, tags)
    'row1_ridge': ('1  AlN ridge (guided)', 'd33=AlN 4.7; SH loss calibrated'),
    'row1_2_rib_unloaded': ('1.2 bare rib (guided)', 'd33=AlN 4.7; SH loss calibrated'),
    'row3_loaded_tio2': ('3  TiO2-loaded (guided)', 'd33=AlN 4.7; TiO2 k as fitted'),
    'row4_loaded_sin': ('4  SiN-loaded (guided)', 'd33=AlN 4.7; SiNx k as fitted'),
    'row5_loaded_scaln_low': ('5.1 ScAlN 9% strip (guided)', 'd33=Yoshioka (opt.); ScAlN k=fit'),
    'row5_3_loaded_scaln_mid': ('5.3 ScAlN 23% strip (guided)', 'd33=Yoshioka (opt.); ScAlN k=fit'),
    'row5_loaded_scaln_high': ('5.2 ScAlN 41% strip (guided)', 'd33=Yoshioka (opt.,extrap.); ScAlN k=fit'),
    'row6_hybrid_lateral': ('6  AlN/SiNx hybrid lat. (guided)', 'd33=AlN 4.7; SiNx k as fitted'),
    'row6_hybrid_vertical': ('6  AlN/SiNx hybrid vert. (guided)', 'd33=AlN 4.7; SiNx k as fitted'),
}
MAX_SH_EDGE = 0.02


def guided_best(run):
    c = pd.read_csv(os.path.join(HERE, 'runs', run, 'crossings.csv'))
    edge = c['sh_edge_ratio'] if 'sh_edge_ratio' in c else pd.Series(np.nan, index=c.index)
    if 'sh_edge_ratio_screen' in c:
        edge = edge.fillna(c['sh_edge_ratio_screen'])
    t = c[((edge <= MAX_SH_EDGE) | edge.isna()) & (c['status'] == 'refined')]
    b = t.loc[t['peak_efficiency_pct_per_W'].idxmax()]
    return {'peak_pct_per_W': float(b['peak_efficiency_pct_per_W']), 'L_opt_mm': float(b['L_opt_mm']),
            'pair': f"{b['pump_label']}->{b['sh_label']}", 'nce': float(b['eta_pct_per_W_cm2'])}


def cerenkov_rows(cases_csv, run):
    """One row per (pump, loss case, d33 scenario). Pump loss budget from cerenkov_pump_loss.csv
    (run `python cerenkov_pump_loss.py <run> --config=<mod>` first):
      eff_inf_pct_W        scattering + interface defects + ScAlN bulk k(450) x loss-case multiplier
      eff_inf_nok450_pct_W scattering + interface only (what the first FoM used -- omits ScAlN k(450))
      eff_inf_lowloss_pct_W optimistic fabrication: interface defects removed, scattering x0.25
                           (1.25 nm rms roughness), ScAlN k(450) still included"""
    cs = pd.read_csv(cases_csv)
    pl = pd.read_csv(os.path.join(HERE, 'runs', run, 'cerenkov_pump_loss.csv')).set_index(['fingerprint', 'pump_id'])
    scen = [c[len('kappa_'):] for c in cs.columns if c.startswith('kappa_')]
    out = []
    for _, r in cs.iterrows():
        pr = pl.loc[(r['fingerprint'], int(r['pump_id']))]
        rec = pr.to_dict()
        s_ = float(r['k_scale'])
        loss = {'': cpl.pump_loss_total(rec, s_), '_nok450': cpl.pump_loss_total(rec, s_, include_k450=False),
                '_lowloss': cpl.pump_loss_total(rec, s_, interface_scale=0.0, scat_scale=0.25)}
        a = {k: math.log(10) / 10 * v for k, v in loss.items()}           # power attenuation [1/m]
        for sname in scen:
            kap = float(r[f'kappa_{sname}'])           # %/W/cm
            row = {'comp_sc': r['comp_sc'], 'h_core': r['h_core'], 'w_core': r['w_core'], 'pump': r['label'],
                   'n_eff': r['n_eff'], 'k_case': r['k_case'], 'k_scale': s_, 'd33_case': sname,
                   'd_nm': r['d_nm'], 'bias_2d_over_1d': r.get('bias_2d_over_1d', np.nan),
                   'pump_loss_dB_per_cm': loss[''] / 100, 'kappa_pct_W_cm': kap,
                   'escape_frac': float(r[f'escape_{sname}'])}
            for suf, av in a.items():
                row[f'eff_inf{suf}_pct_W'] = kap * 1e2 / (2 * av)
            row['eff_1cm_pct_W'] = kap * (1 - math.exp(-2 * a[''] * 1e-2)) / (2 * a['']) * 1e2
            out.append(row)
    return pd.DataFrame(out)


def guided_scaln_cases():
    p = os.path.join(HERE, 'runs', 'guided_scaln_loss_cases.csv')
    return pd.read_csv(p) if os.path.exists(p) else None


if __name__ == '__main__':
    cases = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'runs', 'cerenkov_fixwin', 'cerenkov_cases.csv')
    run = sys.argv[2] if len(sys.argv) > 2 else 'cerenkov_fixwin'
    pd.set_option('display.width', 220)
    g = {r: guided_best(r) for r in GUIDED}
    print('GUIDED rows as run (fitted ScAlN k, Yoshioka d33 for rows 5.x) -- best loss-limited peak [%/W]:')
    for r, v in sorted(g.items(), key=lambda kv: -kv[1]['peak_pct_per_W']):
        print(f"  {GUIDED[r][0]:36s} {v['peak_pct_per_W']:10.3e}  [{GUIDED[r][1]}]")
    best_g = max(v['peak_pct_per_W'] for v in g.values())
    df = cerenkov_rows(cases, run)
    out_csv = os.path.join(HERE, 'runs', run, 'cerenkov_fom.csv')
    df.to_csv(out_csv, index=False)
    order = ['lossless', 'fit_x0.05', 'fit_x0.1', 'fit_x0.25', 'fit_x0.5', 'fit', 'fit_x2']
    tm = df[(df['pump'] == 'TM00') & (df['d33_case'] == 'yoshioka')]
    for col, title in (('eff_inf_pct_W', 'full pump-loss budget (scat + interface + ScAlN k450 x s)'),
                       ('eff_inf_nok450_pct_W', 'WITHOUT ScAlN k(450) (first-pass assumption)'),
                       ('eff_inf_lowloss_pct_W', 'low-loss fabrication (no interface defects, scat x0.25), k450 kept')):
        print(f"\nCerenkov TM00, Yoshioka d33 -- eff_inf [%/W] per 1 W pump, BEFORE extraction; {title}:")
        print(tm.pivot_table(index=['comp_sc', 'h_core', 'w_core'], columns='k_case', values=col)
              [[o for o in order if o in tm.k_case.values]].to_string(float_format=lambda x: f'{x:.2e}'))
    gs = guided_scaln_cases()
    if gs is not None:
        print("\nGUIDED ScAlN strips under the same loss cases (Yoshioka d33; pump variants A/B bound):")
        for pv in ('A', 'B'):
            t = gs[(gs.d33_case == 'yoshioka') & (gs.pump_variant == pv)]
            print(f"variant {pv}:"); print(t.pivot_table(index='comp_sc', columns='k_case', values='peak_pct_per_W')
                                          [order].to_string(float_format=lambda x: f'{x:.2e}'))
    print('wrote', out_csv)
