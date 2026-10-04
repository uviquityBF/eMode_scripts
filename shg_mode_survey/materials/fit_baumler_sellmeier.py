"""Fit a damped (complex) Sellmeier model to the digitized Baumler 2019 Al(1-x)Sc(x)N n, k:

    eps(lam) = eps_inf + sum_j B_j lam^2 / (lam^2 - lam_j^2 - i g_j (lam_j/lam)^P lam),
    n + i k = sqrt(eps)

lam in um. With all g_j = 0 this is an ordinary Sellmeier equation; the damping g_j > 0
produces absorption (k > 0) near/above the gap. The (lam_j/lam)^P factor makes the damping
die off steeply below the resonances, so k -> 0 in the transparent region (a plain Lorentz
tail would put spurious absorption at the pump wavelength); P is fitted per curve. It is a
phenomenological model (not Kramers-Kronig exact) meant to reproduce n and k over 200-600 nm. Fit range 207-600 nm (pump 430-470 nm and SH
215-235 nm inside; starts above AlN's sharp ~203 nm resonance peak), simultaneous least squares on n and k (k weighted x3 so the absorption edge
-- the part that matters for SH loss -- is not traded away for n).

Writes ScAlN_Baumler2019_sellmeier_fits.json: for each x the sampled data used in the fit
(lam, n, k), the parameters, fit-quality numbers, and ready-to-use EMode refractive-index
equation strings (complex, in um), plus ScAlN_Baumler2019_sellmeier_fits.png (data vs fit).

NOTE on EMode: the complex equation uses Python's 1j; EMode's docs say imaginary numbers take a
preceding 'j' and do not state its n +/- ik sign convention -- verify once (refractive_index()
of the custom material at 225 nm should return the tabulated k with a loss-producing sign),
and see 'emode_equation_real' for a lossless alternative.
"""

import json
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
X = [0.00, 0.06, 0.09, 0.14, 0.17, 0.23, 0.32, 0.41]
LAM_MIN_NM, LAM_MAX_NM = 207.0, 600.0
TRANSPARENT_NM = 300.0   # k forced ~0 beyond this wherever the data is < K_ZERO (1-px noise)
K_ZERO = 0.01
N_BAND_WEIGHTS = ((420.0, 480.0, 5.0), (210.0, 240.0, 3.0))  # emphasise n at pump and SH
OUTLIER_N, OUTLIER_K = 0.02, 0.03   # drop samples this far from a 9-point rolling median
K_TRANSPARENT_WEIGHT = 100.0
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


def clean(lam_nm, n, k):
    """Mask samples far from a 9-point rolling median (stray pixels from figure text)."""
    import pandas as pd
    rn = pd.Series(n).rolling(9, center=True, min_periods=3).median().to_numpy()
    rk = pd.Series(k).rolling(9, center=True, min_periods=3).median().to_numpy()
    return (np.abs(n - rn) <= OUTLIER_N) & (np.abs(k - rk) <= OUTLIER_K)


def fit_one(lam_um, n, k):
    # oscillators: band edge (~0.20 um, damped), deeper UV, far UV (~lossless), one free
    p0 = [1.0, 6.0, 0.3, 0.205, 0.01, 0.3, 0.24, 0.01, 1.5, 0.15, 0.02, 1.5, 0.10, 0.001]
    lo = [0.5, 0.0] + [0, 0.12, 0.0, 0, 0.12, 0.0, 0, 0.08, 0.0, 0, 0.03, 0.0]
    hi = [3.0, 40.0] + [10, 0.30, 0.2, 10, 0.32, 0.2, 10, 0.22, 0.3, 10, 0.15, 0.3]

    lam_nm = lam_um * 1000
    force0 = (lam_nm >= TRANSPARENT_NM) & (k < K_ZERO)
    w_k = np.where(force0, K_TRANSPARENT_WEIGHT, K_WEIGHT)
    k_target = np.where(force0, 0.0, k)
    w_n = np.ones_like(n)
    for a, b, w in N_BAND_WEIGHTS:
        w_n = np.where((lam_nm >= a) & (lam_nm <= b), w, w_n)

    def resid(p):
        nm, km = nk_model(p, lam_um)
        return np.concatenate([w_n * (nm - n), w_k * (km - k_target)])

    best = None
    for P0 in (2.0, 6.0, 12.0, 20.0):
        for lam_edge in (0.195, 0.205, 0.215, 0.23):
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
    d = pd.read_csv(os.path.join(HERE, 'ScAlN_Baumler2019_nk_digitized.csv'))
    lam_nm = d['wavelength_nm'].to_numpy()
    sel = (lam_nm >= LAM_MIN_NM) & (lam_nm <= LAM_MAX_NM)
    out = {'source': 'Baumler et al., J. Appl. Phys. 126, 045715 (2019), Fig. n/k; digitized by '
                     'digitize_baumler.py (k resolution ~0.008; k=0 below 3.5 eV)',
           'model': 'eps = eps_inf + sum_j B_j lam^2/(lam^2 - lam_j^2 - 1j*g_j*(lam_j/lam)**P*lam); n+ik = sqrt(eps); lam in um',
           'fit_range_nm': [LAM_MIN_NM, LAM_MAX_NM], 'k_weight': K_WEIGHT,
           'transparent_nm': TRANSPARENT_NM, 'k_transparent_weight': K_TRANSPARENT_WEIGHT,
           'note': 'k beyond transparent_nm is fitted to 0: the digitized data cannot resolve k < ~0.01, '
                   'so pump-band absorption must come from waveguide-loss data, not this fit.',
           'fits': {}}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    cols = ['#0b0b0b', '#e34948', '#1baf7a', '#2a78d6', '#3fb8c9', '#e87ba4', '#9a8a00', '#4a3aa7']
    lam_f = np.linspace(LAM_MIN_NM, LAM_MAX_NM, 400) / 1000
    for x, c in zip(X, cols):
        n = d[f'n_x{x:.2f}'].to_numpy()
        k = d[f'k_x{x:.2f}'].to_numpy()
        m = sel & ~np.isnan(n) & ~np.isnan(k)
        keep = clean(lam_nm[m], n[m], k[m])
        n_dropped = int((~keep).sum())
        m[np.where(m)[0][~keep]] = False
        lam_um = lam_nm[m] / 1000
        p = fit_one(lam_um, n[m], k[m])
        nm_, km_ = nk_model(p, lam_um)
        at = {}
        for L in (215, 225, 235, 430, 450, 470):
            nn, kk = nk_model(p, np.array([L / 1000]))
            at[str(L)] = {'n': round(float(nn[0]), 4), 'k': round(float(kk[0]), 4),
                          'alpha_dB_per_um': round(float(4 * np.pi * kk[0] / (L * 1e-3) * 10 / np.log(10)), 4)}
        out['fits'][f'{x:.2f}'] = {
            'Sc_fraction': x,
            'params': {'eps_inf': p[0], 'damping_power_P': p[1], 'oscillators': [
                {'B': p[2 + 3 * j], 'lam0_um': p[3 + 3 * j], 'g_um': p[4 + 3 * j]} for j in range(N_OSC)]},
            'rms_n': float(np.sqrt(np.mean((nm_ - n[m]) ** 2))),
            'rms_k': float(np.sqrt(np.mean((km_ - k[m]) ** 2))),
            'max_abs_err_n': float(np.max(np.abs(nm_ - n[m]))),
            'max_abs_err_k': float(np.max(np.abs(km_ - k[m]))),
            'n_err_pump_band_max': float(np.max(np.abs((nm_ - n[m])[(lam_nm[m] >= 420) & (lam_nm[m] <= 480)]))),
            'outlier_samples_dropped': n_dropped,
            'model_values': at,
            'emode_equation_complex': emode_equation(p, True),
            'emode_equation_real': emode_equation(p, False),
            'samples': {'wavelength_nm': [round(float(v), 3) for v in lam_nm[m]],
                        'n': [round(float(v), 5) for v in n[m]],
                        'k': [round(float(v), 5) for v in k[m]]},
        }
        nf, kf = nk_model(p, lam_f)
        axs[0].plot(lam_nm[m], n[m], 'o', ms=2.2, color=c, alpha=0.55)
        axs[0].plot(lam_f * 1000, nf, '-', lw=1.6, color=c, label=f'x = {x:.2f}')
        axs[1].plot(lam_nm[m], k[m], 'o', ms=2.2, color=c, alpha=0.55)
        axs[1].plot(lam_f * 1000, kf, '-', lw=1.6, color=c)
        print(f"x={x:.2f}: dropped {n_dropped}, max|dn| pump {out['fits'][f'{x:.2f}']['n_err_pump_band_max']:.4f}, rms n {out['fits'][f'{x:.2f}']['rms_n']:.4f}, rms k "
              f"{out['fits'][f'{x:.2f}']['rms_k']:.4f} | 225 nm n={at['225']['n']} k={at['225']['k']} "
              f"| 450 nm n={at['450']['n']} k={at['450']['k']}")
    for ax, lab in zip(axs, ('refractive index n', 'extinction coefficient k')):
        ax.axvspan(215, 235, color='#eda100', alpha=0.12, lw=0)
        ax.axvspan(430, 470, color='#2a78d6', alpha=0.10, lw=0)
        ax.set_xlabel('wavelength [nm]')
        ax.set_ylabel(lab)
        ax.grid(True, color='#e1e0d9', lw=0.6)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    axs[0].legend(fontsize=7, frameon=False, ncol=2)
    fig.suptitle('AlScN (Baumler 2019): digitized points vs damped-Sellmeier fits '
                 '(shaded: SH 215-235 nm, pump 430-470 nm)', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'ScAlN_Baumler2019_sellmeier_fits.png'), dpi=120)
    with open(os.path.join(HERE, 'ScAlN_Baumler2019_sellmeier_fits.json'), 'w') as f:
        json.dump(out, f, indent=1)
    print('wrote json + png')


if __name__ == '__main__':
    main()
