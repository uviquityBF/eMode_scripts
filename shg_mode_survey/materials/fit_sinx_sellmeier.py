"""Fit a damped (complex) Sellmeier model to Siefke et al. 2022 Beliaev SiNx n, k (PECVD thin
film, the dataset backing the 'hybrid' AlN/SiNx geometry family's strip_eq/strip_loss_eq):

    eps(lam) = eps_inf + sum_j B_j lam^2 / (lam^2 - lam_j^2 - i g_j (lam_j/lam)^P lam),
    n + i k = sqrt(eps)

lam in um. Same model/approach as materials/fit_tio2_sellmeier.py (see that file's docstring for
the general rationale); here the source data is already essentially zero in the pump band
(k ~ 1e-4 by 420 nm, exactly 0 by 450 nm in the raw table), so no special pump-band tail weighting
is needed the way TiO2's residual-tail artifact required.

Motivation / reference: L. Yu. Beliaev, E. Shkondin, A. V. Lavrinenko, O. Takayama, "Optical,
structural and composition properties of silicon nitride films deposited by reactive RF
sputtering, LPCVD and PECVD," Thin Solid Films 763, 139568 (2022); data via refractiveindex.info
(CC0), 100 nm PECVD film ("certain recipe as an example" -- the paper covers multiple deposition
methods/recipes; this is one, not necessarily the best or worst case for a given real process).

Writes SiNx_Beliaev2022_sellmeier_fit.json (params, fit-quality numbers, ready-to-use EMode
refractive-index equation strings, complex and real) and SiNx_Beliaev2022_sellmeier_fit.png.
"""

import json
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
LAM_MIN_NM, LAM_MAX_NM = 150.0, 600.0   # fit range: covers SH 215-235 and pump 430-470
N_BAND_WEIGHTS = ((420.0, 480.0, 5.0), (210.0, 240.0, 3.0))  # emphasise n at pump and SH
N_OSC = 4
K_WEIGHT = 3.0


def eps_model(p, lam_um):
    eps = p[0] + 0j
    P = p[1]
    for j in range(N_OSC):
        B, lam0, g = p[2 + 3 * j:5 + 3 * j]
        eps = eps + B * lam_um ** 2 / (lam_um ** 2 - lam0 ** 2 - 1j * g * (lam0 / lam_um) ** P * lam_um)
    return eps


def nk_model(p, lam_um):
    nk = np.sqrt(eps_model(p, lam_um))
    return nk.real, nk.imag


def fit_one(lam_um, n, k):
    # oscillators: band edge (~0.17 um, damped), deeper UV, far UV (~lossless), one free
    p0 = [1.0, 6.0, 0.5, 0.18, 0.02, 0.3, 0.14, 0.01, 1.5, 0.10, 0.02, 1.5, 0.08, 0.001]
    lo = [0.5, 0.0] + [0, 0.12, 0.0, 0, 0.09, 0.0, 0, 0.06, 0.0, 0, 0.03, 0.0]
    hi = [5.0, 40.0] + [10, 0.28, 0.3, 10, 0.22, 0.3, 10, 0.16, 0.3, 10, 0.12, 0.3]

    w_k = np.full_like(k, K_WEIGHT)
    w_n = np.ones_like(n)
    for a, b, w in N_BAND_WEIGHTS:
        w_n = np.where((lam_um * 1000 >= a) & (lam_um * 1000 <= b), w, w_n)

    def resid(p):
        nm, km = nk_model(p, lam_um)
        return np.concatenate([w_n * (nm - n), w_k * (km - k)])

    best = None
    for P0 in (2.0, 6.0, 12.0, 20.0):
        for lam_edge in (0.14, 0.17, 0.20, 0.23):
            start = np.array(p0, float)
            start[1], start[3] = P0, lam_edge
            start = np.clip(start, lo, hi)
            r = least_squares(resid, start, bounds=(lo, hi), x_scale='jac', max_nfev=20000)
            if best is None or r.cost < best.cost:
                best = r
    return best.x


def _fixed(v, sig=6):
    """Format a float to `sig` significant figures WITHOUT scientific notation -- EMode's
    refractive_index_equation parser rejects 'e' notation outright (ArgumentError: 'invalid
    syntax, disallowed character'), which a near-zero fitted oscillator coefficient can trigger
    via Python's default %g formatting (caught 2026-10-05 fitting SiNx: a dead 4th oscillator
    parked at B ~ 9.8e-08)."""
    if v == 0:
        return '0'
    import math
    decimals = max(0, sig - 1 - int(math.floor(math.log10(abs(v)))))
    return f"{v:.{decimals}f}"


def emode_equation(p, complex_=True):
    """refractive_index_equation string in um (x = wavelength in um)."""
    terms = [_fixed(p[0])]
    P = p[1]
    for j in range(N_OSC):
        B, lam0, g = p[2 + 3 * j:5 + 3 * j]
        damp = f"-1j*{_fixed(g)}*({_fixed(lam0)}/x)**{_fixed(P)}*x" if (complex_ and g > 0) else ""
        terms.append(f"{_fixed(B)}*x**2/(x**2-{_fixed(lam0 ** 2)}{damp})")
    return f"({'+'.join(terms)})**0.5"


def main():
    import pandas as pd
    d = pd.read_csv(os.path.join(HERE, 'SiNx_Beliaev2022_nk.csv'))
    lam_nm = d['wavelength_nm'].to_numpy()
    sel = (lam_nm >= LAM_MIN_NM) & (lam_nm <= LAM_MAX_NM)
    lam_um = lam_nm[sel] / 1000
    n, k = d['n'].to_numpy()[sel], d['k'].to_numpy()[sel]

    p = fit_one(lam_um, n, k)
    nm_, km_ = nk_model(p, lam_um)

    out = {
        'source': 'L. Yu. Beliaev et al., Thin Solid Films 763, 139568 (2022); 100 nm PECVD SiNx '
                  'film; table via refractiveindex.info (CC0), SiNx_Beliaev2022_nk.csv',
        'model': 'eps = eps_inf + sum_j B_j lam^2/(lam^2 - lam_j^2 - 1j*g_j*(lam_j/lam)**P*lam); n+ik = sqrt(eps); lam in um',
        'fit_range_nm': [LAM_MIN_NM, LAM_MAX_NM], 'k_weight': K_WEIGHT,
        'note': 'Unlike TiO2, the raw data itself is ~0 in the pump band (k < 1e-4 by 420 nm, '
                'exactly 0 by 450 nm in the table) so no pump-band tail-weighting trick was needed '
                '-- SiNx genuinely looks transparent there, not just a fit artifact.',
        'params': {'eps_inf': p[0], 'damping_power_P': p[1], 'oscillators': [
            {'B': p[2 + 3 * j], 'lam0_um': p[3 + 3 * j], 'g_um': p[4 + 3 * j]} for j in range(N_OSC)]},
        'rms_n': float(np.sqrt(np.mean((nm_ - n) ** 2))),
        'rms_k': float(np.sqrt(np.mean((km_ - k) ** 2))),
        'max_abs_err_n': float(np.max(np.abs(nm_ - n))),
        'max_abs_err_k': float(np.max(np.abs(km_ - k))),
        'n_err_pump_band_max': float(np.max(np.abs((nm_ - n)[(lam_nm[sel] >= 420) & (lam_nm[sel] <= 480)]))),
        'model_values': {}, 'emode_equation_complex': emode_equation(p, True),
        'emode_equation_real': emode_equation(p, False),
    }
    for L in (215, 225, 235, 430, 450, 470):
        nn, kk = nk_model(p, np.array([L / 1000]))
        out['model_values'][str(L)] = {
            'n': round(float(nn[0]), 4), 'k': round(float(kk[0]), 4),
            'alpha_dB_per_cm': round(float(4 * np.pi * kk[0] / (L * 1e-7) * 10 / np.log(10)), 1)}

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    lam_f = np.linspace(LAM_MIN_NM, LAM_MAX_NM, 400) / 1000
    nf, kf = nk_model(p, lam_f)
    axs[0].plot(lam_nm[sel], n, 'o', ms=2.5, color='#0b0b0b', alpha=0.55, label='Beliaev 2022 data')
    axs[0].plot(lam_f * 1000, nf, '-', lw=1.8, color='#1baf7a', label='damped-Sellmeier fit')
    axs[1].plot(lam_nm[sel], k, 'o', ms=2.5, color='#0b0b0b', alpha=0.55)
    axs[1].plot(lam_f * 1000, kf, '-', lw=1.8, color='#1baf7a')
    for ax, lab in zip(axs, ('refractive index n', 'extinction coefficient k')):
        ax.axvspan(215, 235, color='#eda100', alpha=0.12, lw=0)
        ax.axvspan(430, 470, color='#2a78d6', alpha=0.10, lw=0)
        ax.set_xlabel('wavelength [nm]')
        ax.set_ylabel(lab)
        ax.grid(True, color='#e1e0d9', lw=0.6)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    axs[0].legend(fontsize=8, frameon=False)
    fig.suptitle('SiNx (Beliaev 2022, PECVD): data vs damped-Sellmeier fit (shaded: SH 215-235 nm, pump 430-470 nm)',
                fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'SiNx_Beliaev2022_sellmeier_fit.png'), dpi=120)
    with open(os.path.join(HERE, 'SiNx_Beliaev2022_sellmeier_fit.json'), 'w') as f:
        json.dump(out, f, indent=1)

    print(f"rms n={out['rms_n']:.4f} k={out['rms_k']:.4f}, max|dn| pump band={out['n_err_pump_band_max']:.4f}")
    for L in (215, 225, 235, 430, 450, 470):
        v = out['model_values'][str(L)]
        print(f"  {L} nm: n={v['n']}, k={v['k']}, alpha={v['alpha_dB_per_cm']:.3g} dB/cm")
    print('equation (complex, um):', out['emode_equation_complex'])
    print('wrote json + png')


if __name__ == '__main__':
    main()
