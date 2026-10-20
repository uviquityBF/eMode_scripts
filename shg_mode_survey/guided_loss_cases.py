"""Re-evaluate the guided ScAlN-strip rows (5.1 / 5.3 / 5.2) under the SAME ScAlN-loss cases and d33
scenarios as the Cerenkov study, from crossings.csv columns only (the field exports for these rows are
not on every machine, so no re-solve / field reprocessing is possible here).

APPROXIMATIONS (all flagged in the output):
 * SH loss: in these rows sh_absorption_dB_per_m (1e6..3e7 dB/m) is >99% the strip's bulk ScAlN k at
   225 nm (the other terms are ~1e3..1e4), so alpha_SH(s) = s * sh_absorption + sh_scattering +
   sh_calibrated (the calibrated 100 dB/cm film loss and scattering are not scaled).
 * Pump loss: pump_absorption_dB_per_m = growth-interface defects + strip k(450) with no way to split
   them from the CSV, so two bounds: variant A (pump absorption unscaled -- conservative) and B
   (pump absorption x s -- optimistic bound).
 * d33 scenarios: the three tensor-term overlaps are reconstructed from nce_d{33,31,15}_only and the
   signed shares (phases fixed by requiring the sum to be real), then each term is rescaled by
   d_scenario / d_Yoshioka. The d33 term sums the AlN-core AND strip contributions, which cannot be
   separated, so for reduced-d33 scenarios the AlN-core part (which should NOT scale) is lost:
   results for frac_* / mbe_like are LOWER BOUNDS for the guided rows. 'yoshioka' is exact.
 * The best crossing is re-selected per case (max peak efficiency over window-filtered refined rows).
Peak efficiency [%/W] = eta[%/W/cm^2] * L_eff[cm]^2 maximised over L (analytic optimum; the survey's
stored values use a 10-um grid, which is coarse when alpha_SH ~ 1e7 dB/m -- 's=1 check' prints both).
Usage: python guided_loss_cases.py
"""
import math
import os

import numpy as np
import pandas as pd

import cerenkov_scenarios as sc

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = {'row5_loaded_scaln_low': (0.09, (15.8, 0.84, 0.84)),
        'row5_3_loaded_scaln_mid': (0.23, (44.2, 2.8, 2.8)),
        'row5_loaded_scaln_high': (0.41, (71.9, 5.2, 5.2))}
MAX_SH_EDGE = 0.02


def db_m_to_per_m(x):
    return max(float(x), 0.0) * math.log(10) / 10


def peak_pct_per_W(eta_pct_cm2, a_p_db_m, a_s_db_m, l_max_m=0.2):
    """max over L of eta * L_eff^2 with L_eff = (e^{-a_p L} - e^{-a_s L/2}) / (a_s/2 - a_p)."""
    ap, as_ = db_m_to_per_m(a_p_db_m), db_m_to_per_m(a_s_db_m)
    h = as_ / 2
    if abs(h - ap) < 1e-9 * max(h, ap, 1.0):
        L = min(1 / ap, l_max_m) if ap > 0 else l_max_m
        leff = L * math.exp(-ap * L)
    elif ap == 0 or h == 0:
        L = l_max_m
        leff = (math.exp(-ap * L) - math.exp(-h * L)) / (h - ap)
    else:
        L = min(math.log(h / ap) / (h - ap), l_max_m)
        leff = (math.exp(-ap * L) - math.exp(-h * L)) / (h - ap)
    return eta_pct_cm2 * (leff * 100.0) ** 2, L, leff


def reconstruct_terms(r):
    """Complex tensor-term amplitudes u_i e^{i phi_i} in sqrt(NCE) units, summing to a real sqrt(eta)."""
    root = math.sqrt(max(r['eta_pct_per_W_cm2'], 0.0))
    u = np.array([math.sqrt(max(r[f'nce_d{k}_only_pct_per_W_cm2'], 0.0)) for k in ('33', '31', '15')])
    sh = np.array([r[f'share_d{k}'] for k in ('33', '31', '15')])
    best = None
    c = np.where(u > 0, np.clip(sh * root / np.where(u > 0, u, 1), -1, 1), 0.0)
    s_abs = np.sqrt(1 - c ** 2)
    for signs in np.ndindex(2, 2, 2):
        sg = np.array([1 if b else -1 for b in signs])
        resid = abs(np.sum(u * s_abs * sg))
        if best is None or resid < best[0]:
            best = (resid, sg)
    return u * (c + 1j * s_abs * best[1]), best[0] / max(root, 1e-30)


def load(run):
    c = pd.read_csv(os.path.join(HERE, 'runs', run, 'crossings.csv'))
    c = c[c['status'] == 'refined'].copy()
    edge = c['sh_edge_ratio'] if 'sh_edge_ratio' in c else pd.Series(np.nan, index=c.index)
    if 'sh_edge_ratio_screen' in c:
        edge = edge.fillna(c['sh_edge_ratio_screen'])
    return c[(edge <= MAX_SH_EDGE) | edge.isna()].reset_index(drop=True)


def evaluate(run, comp, dY, s, scen, d_scen, pump_variant):
    c = load(run)
    f = np.array(d_scen) / np.array(dY)
    best = None
    for _, r in c.iterrows():
        terms, _ = reconstruct_terms(r)
        eta = abs(np.sum(f * terms)) ** 2
        a_s = s * r['sh_absorption_dB_per_m'] + r['sh_scattering_dB_per_m'] + r['sh_calibrated_dB_per_m']
        a_p = r['pump_scattering_dB_per_m'] + (r['pump_absorption_dB_per_m'] if pump_variant == 'A'
                                               else s * r['pump_absorption_dB_per_m'])
        pk, L, _ = peak_pct_per_W(eta, a_p, a_s)
        if best is None or pk > best[0]:
            best = (pk, L, eta, f"{r['pump_label']}->{r['sh_label']}")
    return best


if __name__ == '__main__':
    print("s=1 / Yoshioka check vs stored peak_efficiency_pct_per_W (stored uses a coarse 10-um L grid):")
    for run, (comp, dY) in RUNS.items():
        c = load(run)
        stored = c['peak_efficiency_pct_per_W'].max()
        mine = evaluate(run, comp, dY, 1.0, 'yoshioka', dY, 'A')
        print(f"  {run:26s} stored {stored:.3e}   recomputed (analytic L) {mine[0]:.3e}   best {mine[3]}")
    rows = []
    for run, (comp, dY) in RUNS.items():
        scens = sc.d_scenarios(comp if comp in (0.23, 0.41) else 0.23)  # d33/d31 shapes only; 9% handled below
        if comp == 0.09:
            scens = {'yoshioka': dY, 'frac_0.5': (4.7 + 0.5 * (dY[0] - 4.7), 0.1 + 0.5 * (dY[1] - 0.1),) * 1 + (0.1 + 0.5 * (dY[1] - 0.1),),
                     'frac_0': (4.7, 0.1, 0.1), 'mbe_like': (0.3, 0.84 + 0.088 * (100 * comp - 10),) * 1 + (0.84 + 0.088 * (100 * comp - 10),)}
        else:
            scens['yoshioka'] = dY
            scens['mbe_like'] = (0.3, 0.84 + 0.088 * (100 * comp - 10), 0.84 + 0.088 * (100 * comp - 10))
        for case, s in sc.K_SCALES.items():
            for name in ('yoshioka', 'frac_0.5', 'frac_0', 'mbe_like'):
                for pv in ('A', 'B'):
                    pk, L, eta, pair = evaluate(run, comp, dY, s, name, scens[name], pv)
                    rows.append({'run': run, 'comp_sc': comp, 'k_case': case, 'k_scale': s, 'd33_case': name,
                                 'pump_variant': pv, 'peak_pct_per_W': pk, 'L_opt_cm': L * 100, 'nce': eta,
                                 'best_pair': pair})
    df = pd.DataFrame(rows)
    out = os.path.join(HERE, 'runs', 'guided_scaln_loss_cases.csv')
    df.to_csv(out, index=False)
    pd.set_option('display.width', 220)
    for pv in ('A', 'B'):
        print(f"\nGuided ScAlN strips, best peak efficiency [%/W], Yoshioka d33 (exact), pump variant {pv}:")
        t = df[(df.d33_case == 'yoshioka') & (df.pump_variant == pv)]
        print(t.pivot_table(index='comp_sc', columns='k_case', values='peak_pct_per_W')
              [list(sc.K_SCALES)].to_string(float_format=lambda x: f'{x:.2e}'))
    print("\nLOWER BOUNDS for reduced-d33 scenarios (variant B, k=fit and x0.25):")
    t = df[(df.pump_variant == 'B') & (df.k_case.isin(['fit', 'fit_x0.25']))]
    print(t.pivot_table(index=['comp_sc', 'k_case'], columns='d33_case', values='peak_pct_per_W').to_string(float_format=lambda x: f'{x:.2e}'))
    print('wrote', out)
