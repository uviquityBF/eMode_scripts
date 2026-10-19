"""Slab-proxy (1D wide-film) envelope of the escaping SH flux vs film index, film thickness and k
-- cheap, converged (Richardson d->0), EMode-free. Shows how robust each loss case is to the
unavoidable thickness / index uncertainty. Source: Ey uniform across the film (proxy; the real
ridge pump profile differs, so use RATIOS across cases, not absolute values).
Prints, per composition, for each k-case: median, min, max of flux over n*(1+-tol) x h +-dh
(normalised to the 'fit' median) and the fraction of grid points within 2x of the median.
Usage: python cerenkov_1d_map.py"""
import json
import numpy as np
import cerenkov_1d as c1
import cerenkov_scenarios as sc

LAM, N_P = 225.0, 2.22
EPS_S, EPS_C = 2.637 ** 2, 1.524 ** 2
COMPS = {'27.5%': (3.0173, 0.4624, 2.1935), '32%': (3.0307, 0.5894, 2.2216), '41%': (3.1224, 0.7375, 2.2766)}
# (n_real(225), k_fit(225), pump n_eff)  -- real index from the pole-fixed equation EMode used


def flux(n, k, h, n_p, d_nm=0.25):
    f = lambda y: 1e5 * np.ones_like(y)
    a = c1.solve_1d(LAM, n_p, EPS_S, (n + 1j * k) ** 2, EPS_C, h, f, 30e-12, d_nm=d_nm)['to_substrate']
    b = c1.solve_1d(LAM, n_p, EPS_S, (n + 1j * k) ** 2, EPS_C, h, f, 30e-12, d_nm=d_nm / 2)['to_substrate']
    return 2 * b - a


if __name__ == '__main__':
    tol_n, dh = 0.02, 15.0
    for name, (n0, kfit, n_p) in COMPS.items():
        ns = n0 * (1 + np.linspace(-tol_n, tol_n, 9))
        hs = 350.0 + np.linspace(-dh, dh, 7)
        base = np.median([flux(n, kfit, h, n_p) for n in ns for h in hs])
        print(f"\n{name} (n={n0}, k_fit={kfit}), pump n_eff={n_p}; grid n +-{tol_n:.0%} x h 350+-{dh:g} nm; "
              f"'fit' median = {base:.3e} (=1.0)")
        print(f"{'case':10s} {'k':>6s} {'median':>8s} {'min':>9s} {'max':>8s} {'at nominal':>11s} {'frac>=0.5x fit-median':>22s}")
        for case, s in sc.K_SCALES.items():
            v = np.array([[flux(n, s * kfit, h, n_p) for h in hs] for n in ns]) / base
            print(f"{case:10s} {s * kfit:6.3f} {np.median(v):8.2f} {v.min():9.3g} {v.max():8.2f} "
                  f"{flux(n0, s * kfit, 350.0, n_p) / base:11.2f} {np.mean(v >= 0.5):22.2f}", flush=True)
