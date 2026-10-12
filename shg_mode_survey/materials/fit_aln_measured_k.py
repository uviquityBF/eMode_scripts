"""Fits AlN's measured k(lambda) (AM187-LT6 ellipsometry, both axes) as a standalone function of
wavelength -- deliberately NOT via the project's usual joint complex-eps damped-Sellmeier model
(fit_sinx_sellmeier.py etc.), because that model ties n and k together through a shared sqrt(eps)
-- and the explicit decision (2026-10-12) was to keep the EXISTING hardcoded AlN_EQ_O/AlN_EQ_E for
n (itself real measured data, just from an unidentified sample) and add ONLY k from AM187, for
continuity with every prior simulation result (phase-matching wavelength isn't this study's focus,
but n changes would shift it; k changes are the whole point of this update).

k(x) [x = wavelength in um] is fit as a sum of Lorentzian peaks -- bounded and pole-free everywhere
(unlike the Sellmeier denominator form used for n, which has a resonance pole requiring axis
clipping just to plot, see build_assumptions_report.py's note), appropriate since k only needs to
be a plausible, smooth, non-negative curve here, not a physically-derived oscillator model:
    k(x) = sum_j A_j / (1 + ((x - x0_j) / w_j)^2),  A_j >= 0
Two peaks per axis, matching the real double-feature shape seen in the data (a steep edge below
~200nm plus a broader, weaker feature peaking ~230-280nm that tails out past 600nm -- plausibly the
same kind of defect-related absorption band the literature review already flagged, Robinson et al./
Bickermann et al., PLAN.md's AlN k candidates table).

Final equation for Python-side loss use (emode_equation_complex): the EXISTING hardcoded real n
equation, PLUS i times this fit's k(x) -- literally added, not combined via sqrt(eps), since n and
k are being deliberately sourced independently here. emode_equation_real is just the unchanged
hardcoded n equation (included for completeness/symmetry with the other fit scripts, though nothing
downstream needs it to change).

Writes AlN_AM187_LT6_k_fit.json (params, fit quality, ready-to-use equation strings) and
AlN_AM187_LT6_k_fit.png (data vs fit, both axes).
"""
import json
import math
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
FIT_MIN_NM, FIT_MAX_NM = 192.5, 600.0
N_PEAKS = 3
# emphasise getting the two bands that actually matter right, same convention as
# fit_sinx_sellmeier.py/fit_tio2_sellmeier.py's N_BAND_WEIGHTS -- a 2-peak fit was found to leave
# a real, visible gap in part of the SH band (205-220nm, where the data dips between the edge
# feature and the broader defect-band hump) because the edge peak's tail didn't decay fast enough;
# a 3rd peak plus this weighting closes it.
BAND_WEIGHTS = ((215.0, 235.0, 8.0), (430.0, 470.0, 4.0))

AlN_EQ_O = ('(1+2.8032/(1-0.015287/x**2)+0.36335/(1-0.036095/x**2)'
            '-33508000/(1+367200000/x**2))**0.5')
AlN_EQ_E = ('(1+0.017061/(1-0.043855/x**2)+3.1976/(1-0.022642/x**2)'
            '-57269000/(1-74226000/x**2))**0.5')


def k_model(p, x_um):
    k = np.zeros_like(x_um)
    for j in range(N_PEAKS):
        A, x0, w = p[3 * j:3 * j + 3]
        k = k + A / (1 + ((x_um - x0) / w) ** 2)
    return k


def fit_one(x_um, k, wl_nm):
    # peak 1: steep edge just below the data's own short-wavelength limit (narrow). peak 2: the
    # dip-then-hump feature right in/near the SH band (narrower than the old 2-peak attempt, so
    # its tail actually decays before the SH band instead of overshooting through it). peak 3:
    # broad, weak, long tail extending well past 600nm.
    p0 = [0.5, 0.17, 0.015, 0.05, 0.23, 0.02, 0.02, 0.35, 0.15]
    lo = [0.0, 0.10, 0.004, 0.0, 0.205, 0.008, 0.0, 0.25, 0.05]
    hi = [5.0, 0.205, 0.05, 1.0, 0.26, 0.05, 1.0, 0.55, 0.6]

    w = np.ones_like(k)
    for a, b, wt in BAND_WEIGHTS:
        w = np.where((wl_nm >= a) & (wl_nm <= b), wt, w)

    def resid(p):
        return w * (k_model(p, x_um) - k)

    best = None
    for x0_1 in (0.14, 0.17, 0.195):
        for x0_2 in (0.21, 0.225, 0.24):
            start = np.array(p0, float)
            start[1], start[4] = x0_1, x0_2
            start = np.clip(start, lo, hi)
            r = least_squares(resid, start, bounds=(lo, hi), x_scale='jac', max_nfev=20000)
            if best is None or r.cost < best.cost:
                best = r
    return best.x


def _fixed(v, sig=6):
    """Fixed-point formatting, no scientific notation -- EMode's equation parser rejects 'e'
    notation outright (see materials/fit_sinx_sellmeier.py's docstring for where this was found)."""
    if v == 0:
        return '0'
    decimals = max(0, sig - 1 - int(math.floor(math.log10(abs(v)))))
    return f"{v:.{decimals}f}"


def k_equation(p):
    # a peak the optimizer collapsed to near-zero amplitude (overfit for axes that only need
    # fewer than N_PEAKS real features, e.g. k_o) contributes nothing physically -- drop it rather
    # than print it at _fixed()'s full sig-fig precision, which for a ~1e-17 value means 15+
    # leading zero decimals for a term that rounds to 0 everywhere anyway.
    terms = []
    for j in range(N_PEAKS):
        A, x0, w = p[3 * j:3 * j + 3]
        if A < 1e-4:
            continue
        terms.append(f"{_fixed(A)}/(1+((x-{_fixed(x0)})/{_fixed(w)})**2)")
    return '(' + '+'.join(terms) + ')'


def main():
    import pandas as pd
    d = pd.read_csv(os.path.join(HERE, 'AlN_AM187_LT6_measured_nk.csv'))
    wl_nm = d['wavelength_nm'].to_numpy()
    sel = (wl_nm >= FIT_MIN_NM) & (wl_nm <= FIT_MAX_NM)
    x_um = wl_nm[sel] / 1000.0
    k_o, k_e = d['k_o'].to_numpy()[sel], d['k_e'].to_numpy()[sel]

    p_o = fit_one(x_um, k_o, wl_nm[sel])
    p_e = fit_one(x_um, k_e, wl_nm[sel])
    ko_fit, ke_fit = k_model(p_o, x_um), k_model(p_e, x_um)

    eq_k_o, eq_k_e = k_equation(p_o), k_equation(p_e)
    out = {
        'source': 'materials/AlN_AM187_LT6_measured_nk.csv (sample AM187, MOCVD, new model, '
                  '6.4.26, position LT(6); raw WVASE export from github.com/uviquityBF/'
                  'ellipsometry_data, picked 2026-10-12 as the lowest non-negative k_e among all '
                  'MOCVD-labeled positions)',
        'model': 'k(x) = sum of 3 Lorentzian peaks, x = wavelength in um; fit to k ALONE, '
                 'decoupled from n -- see module docstring for why',
        'fit_range_nm': [FIT_MIN_NM, FIT_MAX_NM],
        'note': 'n is NOT refit here -- per 2026-10-12 decision, the existing hardcoded AlN_EQ_O/'
                'AlN_EQ_E (themselves real measured data, sample unidentified) are kept for '
                'continuity with every prior simulation result; only k changes.',
        'params_k_o': {'A': list(p_o[0::3]), 'x0_um': list(p_o[1::3]), 'w_um': list(p_o[2::3])},
        'params_k_e': {'A': list(p_e[0::3]), 'x0_um': list(p_e[1::3]), 'w_um': list(p_e[2::3])},
        'rms_k_o': float(np.sqrt(np.mean((ko_fit - k_o) ** 2))),
        'rms_k_e': float(np.sqrt(np.mean((ke_fit - k_e) ** 2))),
        'max_abs_err_k_o': float(np.max(np.abs(ko_fit - k_o))),
        'max_abs_err_k_e': float(np.max(np.abs(ke_fit - k_e))),
        'k_equation_o': eq_k_o, 'k_equation_e': eq_k_e,
        'hardcoded_n_equation_o': AlN_EQ_O, 'hardcoded_n_equation_e': AlN_EQ_E,
        'emode_equation_real_o': AlN_EQ_O, 'emode_equation_real_e': AlN_EQ_E,
        'emode_equation_complex_o': f"({AlN_EQ_O})+1j*{eq_k_o}",
        'emode_equation_complex_e': f"({AlN_EQ_E})+1j*{eq_k_e}",
        'model_values': {},
    }
    for L in (215, 225, 235, 430, 450, 470):
        xv = np.array([L / 1000.0])
        ko_v = float(k_model(p_o, xv)[0])
        ke_v = float(k_model(p_e, xv)[0])
        out['model_values'][str(L)] = {'k_o': round(ko_v, 5), 'k_e': round(ke_v, 5)}

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    xf_um = np.linspace(FIT_MIN_NM, FIT_MAX_NM, 400) / 1000.0
    axs[0].plot(wl_nm[sel], k_o, 'o', ms=2.5, color='#0b0b0b', alpha=0.5, label='AM187-LT6 measured')
    axs[0].plot(xf_um * 1000, k_model(p_o, xf_um), '-', lw=1.8, color='#c23a73', label='3-Lorentzian fit')
    axs[0].set_title('k_o (ordinary)')
    axs[1].plot(wl_nm[sel], k_e, 'o', ms=2.5, color='#0b0b0b', alpha=0.5)
    axs[1].plot(xf_um * 1000, k_model(p_e, xf_um), '-', lw=1.8, color='#c23a73')
    axs[1].set_title('k_e (extraordinary / c-axis, drives d33)')
    for ax in axs:
        ax.axvspan(215, 235, color='#eda100', alpha=0.12, lw=0)
        ax.axvspan(430, 470, color='#2a78d6', alpha=0.10, lw=0)
        ax.set_xlabel('wavelength [nm]')
        ax.set_ylabel('k')
        ax.grid(True, color='#e1e0d9', lw=0.6)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    axs[0].legend(fontsize=8, frameon=False)
    fig.suptitle('AlN measured k (AM187-LT6): data vs. 3-Lorentzian fit (shaded: SH 215-235nm, pump 430-470nm)',
                fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'AlN_AM187_LT6_k_fit.png'), dpi=120)
    with open(os.path.join(HERE, 'AlN_AM187_LT6_k_fit.json'), 'w') as f:
        json.dump(out, f, indent=1)

    print(f"rms k_o={out['rms_k_o']:.5f}  rms k_e={out['rms_k_e']:.5f}")
    for L in (215, 225, 235, 430, 450, 470):
        v = out['model_values'][str(L)]
        print(f"  {L} nm: k_o={v['k_o']}, k_e={v['k_e']}")
    print('k_equation_e:', eq_k_e)
    print('wrote json + png')


if __name__ == '__main__':
    main()
