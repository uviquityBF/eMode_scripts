"""Validation of cerenkov_fdfd.py against analytic line-source radiation (no EMode needed).

A z-directed polarization line Pz = p g(r) e^{i kz z} (g a narrow Gaussian, int g dA = 1) in a
homogeneous medium eps radiates, per unit length,
    P' = omega kt^2 |p|^2 / (8 eps0 eps) * exp(-kt^2 sigma^2),   kt^2 = k0^2 eps - kz^2
(from (lap_t + kt^2) Ez = -kt^2 Pz/(eps0 eps), Ez = (i/4) H0(kt r) * source, source work).
For kz above the medium's light line nothing radiates.
Run: python test_cerenkov_fdfd.py
"""

import time

import numpy as np

import cerenkov_fdfd as cf


def line_source_case(n_med, n_kz, d_nm=10.0, half=900.0, sigma=15.0, pol='Ez'):
    lam = 225.0
    g = cf.YeeGrid(-half, half, -half, half, d_nm)
    eps = {c: np.full((g.ny, g.nx), n_med ** 2, dtype=complex) for c in ('Ex', 'Ey', 'Ez')}
    P = {}
    p0 = 1.0  # V/m * m^2 units of P/eps0 integrated: arbitrary
    for c in ('Ex', 'Ey', 'Ez'):
        X, Y = g.positions(c)
        gauss = np.exp(-(X ** 2 + Y ** 2) / (2 * sigma ** 2)) / (2 * np.pi * (sigma * 1e-9) ** 2)
        P[c] = p0 * gauss if c == pol else np.zeros_like(X, dtype=complex)
    k0 = 2 * np.pi / (lam * 1e-9)
    kz = k0 * n_kz
    t0 = time.time()
    sol = cf.solve(g, eps, P, lam, kz, npml=20)
    res = cf.radiated_power(sol, P)
    kt2 = k0 ** 2 * n_med ** 2 - kz ** 2
    p = p0 * cf.EPS0  # actual dipole-line strength [C/m] since P_over_eps0 * eps0 = P
    expected = (sol['omega'] * kt2 * abs(p) ** 2 / (8 * cf.EPS0 * n_med ** 2)
                * np.exp(-kt2 * (sigma * 1e-9) ** 2)) if kt2 > 0 else 0.0
    return res, expected, time.time() - t0, g


def test_line_source():
    for n_med, n_kz in ((1.87, 1.80), (1.87, 1.50), (2.5, 2.1)):
        res, exp, dt, g = line_source_case(n_med, n_kz)
        ratio = res['total_W_per_m'] / exp
        print(f"n={n_med} n_kz={n_kz} grid {g.nx}x{g.ny} solve {dt:.1f}s: flux {res['total_W_per_m']:.4e} "
              f"work {res['source_work_W_per_m']:.4e} analytic {exp:.4e} ratio {ratio:.3f} "
              f"sides {{{', '.join(f'{k}: {v:.2e}' for k, v in res['sides_W_per_m'].items())}}}")
        assert abs(ratio - 1) < 0.05, ratio
        assert abs(res['source_work_W_per_m'] / exp - 1) < 0.05


def test_no_radiation_below_light_line():
    res, exp, dt, g = line_source_case(1.87, 1.95)
    ref, _, _, _ = line_source_case(1.87, 1.80)
    frac = abs(res['total_W_per_m']) / ref['total_W_per_m']
    print(f"evanescent case (n_kz > n_med): flux / radiating-case flux = {frac:.2e}")
    assert frac < 1e-3


def test_transverse_source_energy_balance():
    res, _, _, _ = line_source_case(1.87, 1.6, pol='Ey')
    r = res['total_W_per_m'] / res['source_work_W_per_m']
    print(f"Ey source: flux/work = {r:.3f}")
    assert abs(r - 1) < 0.05


if __name__ == '__main__':
    test_line_source()
    test_no_radiation_below_light_line()
    test_transverse_source_energy_balance()
    print('all passed')
