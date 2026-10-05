"""Fit a damped (complex) Sellmeier model to Siefke et al. 2016 TiO2 n, k (ALD thin film, the
dataset backing EMode's loaded-family strip_eq):

    eps(lam) = eps_inf + sum_j B_j lam^2 / (lam^2 - lam_j^2 - i g_j (lam_j/lam)^P lam),
    n + i k = sqrt(eps)

lam in um. Same model as materials/fit_baumler_sellmeier.py (see that file's docstring); here
there is a single composition (TiO2, no Sc fraction), fit directly to the literature table
instead of a digitized figure (TiO2_Siefke2016_nk.csv, pulled verbatim from
refractiveindex.info's Siefke dataset, 120-700 nm). EMode's built-in TiO2 material has k=0
everywhere (checked via em.refractive_index) -- it's a visible-range-only fit and silently drops
the strong UV absorption the SH band sees, hence this replacement.

Motivation / reference: T. Siefke et al., Adv. Opt. Mater. 4, 1780-1786 (2016); data via
refractiveindex.info (CC0), ALD TiO2, 350 nm film, universal dispersion model (Franta et al.,
Appl. Opt. 54, 9108, 2015) covering the UV absorption edge relevant from 215 nm (SH) to 470 nm
(pump).

Writes TiO2_Siefke2016_sellmeier_fit.json (params, fit-quality numbers, ready-to-use EMode
refractive-index equation strings, complex and real) and TiO2_Siefke2016_sellmeier_fit.png
(data vs fit).
"""

import json
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
LAM_MIN_NM, LAM_MAX_NM = 150.0, 600.0   # fit range: covers SH 215-235 and pump 430-470
N_BAND_WEIGHTS = ((420.0, 480.0, 5.0), (210.0, 240.0, 3.0))  # emphasise n at pump and SH
# k is real (measured) everywhere, not forced to zero -- but the data's own tail is already
# small (<=0.001) beyond ~390 nm, so it gets a much higher weight than the strong SH-band
# absorption to stop least-squares averaging it away (a shared power-law damping otherwise
# undershoots the SH edge or overshoots the pump-band tail).
K_TAIL_NM, K_TAIL_WEIGHT = 390.0, 15.0
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
    # oscillators: band edge (~0.32 um anatase gap region, damped), deeper UV, far UV, one free
    p0 = [1.0, 6.0, 0.5, 0.33, 0.02, 0.3, 0.22, 0.01, 1.5, 0.15, 0.02, 1.5, 0.12, 0.001]
    lo = [0.5, 0.0] + [0, 0.18, 0.0, 0, 0.14, 0.0, 0, 0.08, 0.0, 0, 0.03, 0.0]
    hi = [5.0, 40.0] + [10, 0.40, 0.3, 10, 0.30, 0.3, 10, 0.22, 0.3, 10, 0.15, 0.3]

    w_k = np.where(lam_um * 1000 >= K_TAIL_NM, K_TAIL_WEIGHT, K_WEIGHT)
    w_n = np.ones_like(n)
    for a, b, w in N_BAND_WEIGHTS:
        w_n = np.where((lam_um * 1000 >= a) & (lam_um * 1000 <= b), w, w_n)

    def resid(p):
        nm, km = nk_model(p, lam_um)
        return np.concatenate([w_n * (nm - n), w_k * (km - k)])

    best = None
    for P0 in (2.0, 6.0, 12.0, 20.0):
        for lam_edge in (0.30, 0.33, 0.36, 0.39):
            start = np.array(p0, float)
            start[1], start[3] = P0, lam_edge
            start = np.clip(start, lo, hi)
            r = least_squares(resid, start, bounds=(lo, hi), x_scale='jac', max_nfev=20000)
            if best is None or r.cost < best.cost:
                best = r
    return best.x


def emode_equation(p, complex_=True):
    """refractive_index_equation string in um (x = wavelength in um)."""
    terms = [f"{p[0]:.6g}"]
    P = p[1]
    for j in range(N_OSC):
        B, lam0, g = p[2 + 3 * j:5 + 3 * j]
        damp = f"-1j*{g:.6g}*({lam0:.6g}/x)**{P:.6g}*x" if (complex_ and g > 0) else ""
        terms.append(f"{B:.6g}*x**2/(x**2-{lam0 ** 2:.6g}{damp})")
    return f"({'+'.join(terms)})**0.5"


def main():
    import pandas as pd
    d = pd.read_csv(os.path.join(HERE, 'TiO2_Siefke2016_nk.csv'))
    lam_nm = d['wavelength_nm'].to_numpy()
    sel = (lam_nm >= LAM_MIN_NM) & (lam_nm <= LAM_MAX_NM)
    lam_um = lam_nm[sel] / 1000
    n, k = d['n'].to_numpy()[sel], d['k'].to_numpy()[sel]

    p = fit_one(lam_um, n, k)
    nm_, km_ = nk_model(p, lam_um)

    out = {
        'source': 'T. Siefke et al., Adv. Opt. Mater. 4, 1780-1786 (2016); ALD TiO2, 350 nm film; '
                  'table via refractiveindex.info (CC0), TiO2_Siefke2016_nk.csv',
        'model': 'eps = eps_inf + sum_j B_j lam^2/(lam^2 - lam_j^2 - 1j*g_j*(lam_j/lam)**P*lam); n+ik = sqrt(eps); lam in um',
        'fit_range_nm': [LAM_MIN_NM, LAM_MAX_NM], 'k_weight': K_WEIGHT,
        'note': 'EMode built-in TiO2 has k=0 everywhere (checked via em.refractive_index): a '
                'visible-range-only fit that silently drops the strong UV absorption at the SH band. '
                'This fit replaces it for the loaded-family strip_eq. SH-band (215-235 nm) n,k are '
                'well constrained and agree with the raw Siefke table to ~1-3%. Pump-band (430-470 nm) '
                'k has a residual of ~0.01-0.02 (alpha ~1.5-3e4 dB/cm) vs the real data\'s near-zero '
                '(~1e-4) -- a fit artifact of the shared power-law damping, not a real absorption '
                'feature; treat pump-mode loss from this strip_eq as an upper bound and cross-check '
                'against measured waveguide loss before trusting it quantitatively.',
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
    axs[0].plot(lam_nm[sel], n, 'o', ms=2.5, color='#0b0b0b', alpha=0.55, label='Siefke 2016 data')
    axs[0].plot(lam_f * 1000, nf, '-', lw=1.8, color='#e34948', label='damped-Sellmeier fit')
    axs[1].plot(lam_nm[sel], k, 'o', ms=2.5, color='#0b0b0b', alpha=0.55)
    axs[1].plot(lam_f * 1000, kf, '-', lw=1.8, color='#e34948')
    for ax, lab in zip(axs, ('refractive index n', 'extinction coefficient k')):
        ax.axvspan(215, 235, color='#eda100', alpha=0.12, lw=0)
        ax.axvspan(430, 470, color='#2a78d6', alpha=0.10, lw=0)
        ax.set_xlabel('wavelength [nm]')
        ax.set_ylabel(lab)
        ax.grid(True, color='#e1e0d9', lw=0.6)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    axs[0].legend(fontsize=8, frameon=False)
    fig.suptitle('TiO2 (Siefke 2016): data vs damped-Sellmeier fit (shaded: SH 215-235 nm, pump 430-470 nm)',
                fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'TiO2_Siefke2016_sellmeier_fit.png'), dpi=120)
    with open(os.path.join(HERE, 'TiO2_Siefke2016_sellmeier_fit.json'), 'w') as f:
        json.dump(out, f, indent=1)

    print(f"rms n={out['rms_n']:.4f} k={out['rms_k']:.4f}, max|dn| pump band={out['n_err_pump_band_max']:.4f}")
    for L in (215, 225, 235, 430, 450, 470):
        v = out['model_values'][str(L)]
        print(f"  {L} nm: n={v['n']}, k={v['k']}, alpha={v['alpha_dB_per_cm']:.3g} dB/cm")
    print('equation (complex, um):', out['emode_equation_complex'])
    print('wrote json + png')


if __name__ == '__main__':
    main()
