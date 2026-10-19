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
    cs = pd.read_csv(cases_csv)
    pm = pd.read_csv(os.path.join(HERE, 'runs', run, 'pump_modes.csv'))
    pm['sub_h'] = pm['params'].apply(lambda s: json.loads(s)['substrate_height'])
    key = pm.set_index(['fingerprint', 'pump_id'])
    scen = [c[len('kappa_'):] for c in cs.columns if c.startswith('kappa_')]
    out = []
    for _, r in cs.iterrows():
        pr = key.loc[(r['fingerprint'], int(r['pump_id']))]
        loss_dB_m = float(pr['scattering_dB_per_m']) + float(pr['absorption_dB_per_m'])
        a = math.log(10) / 10 * loss_dB_m          # pump POWER attenuation [1/m]
        for s in scen:
            kap = float(r[f'kappa_{s}'])           # %/W/cm
            Leff_cm = lambda L_cm: (1 - math.exp(-2 * a * L_cm * 1e-2)) / (2 * a) * 1e2
            out.append({'comp_sc': r['comp_sc'], 'pump': r['label'], 'k_case': r['k_case'], 'd33_case': s,
                        'd_nm': r['d_nm'], 'bias_2d_over_1d': r.get('bias_2d_over_1d', np.nan),
                        'pump_loss_dB_per_cm': loss_dB_m / 100, 'kappa_pct_W_cm': kap,
                        'escape_frac': float(r[f'escape_{s}']),
                        'eff_1mm_pct_W': kap * Leff_cm(0.1), 'eff_1cm_pct_W': kap * Leff_cm(1.0),
                        'eff_inf_pct_W': kap * 1e2 / (2 * a)})
    return pd.DataFrame(out)


if __name__ == '__main__':
    cases = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'runs', 'cerenkov_fixwin', 'cerenkov_cases.csv')
    run = sys.argv[2] if len(sys.argv) > 2 else 'cerenkov_fixwin'
    g = {r: guided_best(r) for r in GUIDED}
    print('GUIDED rows -- best loss-limited peak efficiency [%/W] (window-filtered, refined):')
    for r, v in sorted(g.items(), key=lambda kv: -kv[1]['peak_pct_per_W']):
        print(f"  {GUIDED[r][0]:36s} {v['peak_pct_per_W']:10.3e} %/W  (L_opt {v['L_opt_mm']:.3g} mm, {v['pair']}, "
              f"NCE {v['nce']:.4g})  [{GUIDED[r][1]}]")
    best_g = max(v['peak_pct_per_W'] for v in g.values())
    df = cerenkov_rows(cases, run)
    out_csv = os.path.join(HERE, 'runs', run, 'cerenkov_fom.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nCERENKOV (eff_inf = pump-loss-limited long-device value, per 1 W pump, BEFORE extraction):")
    show = df[df['d33_case'].isin(['yoshioka', 'frac_0.5', 'mbe_like'])]
    piv = show.pivot_table(index=['comp_sc', 'pump', 'k_case'], columns='d33_case', values='eff_inf_pct_W')
    pd.set_option('display.width', 200)
    print(piv.to_string(float_format=lambda x: f'{x:.2e}'))
    print(f"\nbest guided (any row) = {best_g:.3e} %/W; ratio Cerenkov(eff_inf, yoshioka) / best guided:")
    y = df[df['d33_case'] == 'yoshioka'].copy()
    y['vs_best_guided'] = y['eff_inf_pct_W'] / best_g
    print(y.pivot_table(index=['comp_sc', 'pump'], columns='k_case', values='vs_best_guided')
          .to_string(float_format=lambda x: f'{x:.2f}'))
    print('wrote', out_csv)
