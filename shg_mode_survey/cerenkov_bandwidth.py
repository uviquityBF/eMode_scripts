"""Bandwidth / fabrication-tolerance comparison: Cerenkov vs guided phase matching (row 8), EMode-free.

CERENKOV: kappa(lambda_SH) from runs/cerenkov_bw_<L>/cerenkov_cases.csv (EMode pump solves at SH 215..235 nm,
FDFD per wavelength; d33 held constant with wavelength -- no dispersion data). There is no phase-matching
condition, only n_AlN(lambda_SH) > n_eff,pump, so the acceptance is the scanned window or wider.

GUIDED (order-of-magnitude estimate, NOT a mode solve): sinc^2 phase-matching with
    FWHM_pump = 0.221 * lambda_p^2 / (L * dn_g),   dn_g = n_g(SH) - n_g(pump)
dn_g from BULK AlN dispersion (o/e, evaluated from the project's index equations; guided-mode/waveguide
dispersion not included, so +-30% or so). L = effective interaction length (1.29 mm for the best guided
ridge row, from its L_opt). The PM wavelength moves with film thickness by dLam_SH/dh ~ 0.22 nm/nm
(the phase_matching_pipeline's own fits for TM04: 0.21-0.24), i.e. 0.44 nm of PUMP wavelength per nm of
thickness. Mean efficiency over a uniform spread R of PM wavelengths (R >> FWHM) of a FIXED-wavelength
pump = peak * 1.13 * FWHM / R   (integral of sinc^2 = FWHM / 0.886).
For a pulsed pump of bandwidth B: guided acceptance ~ min(1, 1.13 * FWHM / B); Cerenkov ~ 1.
Usage: python cerenkov_bandwidth.py
"""
import math
import os

import pandas as pd

import geometry as geo

HERE = os.path.dirname(os.path.abspath(__file__))
LAM_P = 450.0            # nm
DLAM_DH = 0.22           # nm SH per nm thickness (pipeline TM04 fits)
GUIDED_PEAK = 1.29e-2    # %/W, best guided row (row1 AlN ridge, d33 = 4.7)
L_EFF_MM = 1.29


def n_group(eq, lam, h=0.5):
    n = lambda l: geo.eval_index_equation(eq, l)
    return n(lam) - lam * (n(lam + h) - n(lam - h)) / (2 * h)


def guided_fwhm_pump_nm(L_mm, axis='e'):
    eq = geo.AlN_EQ_E if axis == 'e' else geo.AlN_EQ_O
    dng = n_group(eq, LAM_P / 2) - n_group(eq, LAM_P)
    return 0.221 * (LAM_P * 1e-9) ** 2 / (L_mm * 1e-3 * dng) * 1e9, dng


def cerenkov_kappa_table():
    fr = []
    for L in (215, 220, 225, 230, 235):
        p = os.path.join(HERE, 'runs', f'cerenkov_bw_{L}', 'cerenkov_cases.csv')
        if os.path.exists(p):
            c = pd.read_csv(p)
            c['lam_sh'] = L
            fr.append(c)
    d = pd.concat(fr)
    d['geom'] = (d.comp_sc.map('{:.2f}'.format) + ' h' + d.h_core.astype(int).astype(str) +
                 ' w' + d.w_core.astype(int).astype(str))
    return d


if __name__ == '__main__':
    d = cerenkov_kappa_table()
    print('Cerenkov kappa_yoshioka [%/W/cm] vs SH wavelength (TM00 pump); max/min over the scanned window:')
    for kc in ('fit', 'fit_x0.25', 'fit_x2'):
        t = d[d.k_case == kc].pivot_table(index='geom', columns='lam_sh', values='kappa_yoshioka')
        t['max/min'] = t.max(axis=1) / t.min(axis=1)
        print(f'\n[{kc}]'); print(t.to_string(float_format=lambda x: f'{x:.3g}'))
    print('\nGUIDED phase-matching acceptance (estimate):')
    for L in (1.29, 0.1, 0.01, 0.001):
        w, dng = guided_fwhm_pump_nm(L)
        print(f"  L_eff = {L:>6} mm: FWHM(pump) = {w:8.3g} nm  = {w * 0.5:8.3g} nm at the SH   (dn_g = {dng:.2f})")
    w, _ = guided_fwhm_pump_nm(L_EFF_MM)
    print(f"\nThickness tolerance for fixed-wavelength pumping (L = {L_EFF_MM} mm): FWHM_h = {w / (2 * DLAM_DH):.3g} nm")
    print('Mean guided efficiency of the best guided ridge for a FIXED pump wavelength, vs the spread of PM wavelengths')
    print('across devices set by film-thickness error sigma_h (R = 2 * 2*dLam_SH/dh * sigma_h at the pump):')
    for sig in (0.05, 0.5, 2.0, 5.0):
        R = 2 * (2 * DLAM_DH) * sig
        f = min(1.0, 1.13 * w / R)
        print(f"  sigma_h = {sig:4.2f} nm: PM spread +-{R / 2:.3g} nm (pump) -> mean {f:.3g} of peak = {GUIDED_PEAK * f:.2e} %/W")
    print('\nPulsed pump (transform-limited, 450 nm) -> guided acceptance of the spectrum:')
    for tau_fs in (1e5, 1e3, 100):
        B = 0.44 * (LAM_P * 1e-9) ** 2 / (3e8 * tau_fs * 1e-15) * 1e9
        print(f"  {tau_fs:>8g} fs: B = {B:8.3g} nm -> guided uses {min(1.0, 1.13 * w / B):.3g} of the pulse; Cerenkov ~1 (window >= 40 nm pump)")
