"""y-discretization-only validation of cerenkov_fdfd against the 1D reference: the 2D solver is run
with PERIODIC x (4 cells, kx=0, uniform source) so it is exactly a 1D problem, isolating the
second-order Yee phase error in y inside the high-index core from lateral (slab-mode) physics.
Usage: python validate_cerenkov_1d_periodic.py [d1,d2,...] ["3.03+0j;3.03+0.1j"]"""
import sys
import numpy as np
import cerenkov_1d as c1
import cerenkov_fdfd as cf

LAM, N_P, H, D33, EY0 = 225.0, 2.22, 350.0, 30e-12, 1e5
EPS_S, EPS_C = 2.637 ** 2, 1.524 ** 2


def periodic_2d(n_film, d_nm, margin=500.0, npml=20):
    g = cf.YeeGrid(0.0, 4 * d_nm, -margin - npml * d_nm, H + margin + npml * d_nm, d_nm)
    film = lambda X, Y: (Y >= 0) & (Y <= H)
    ey = lambda Y: np.where(film(Y, Y), EY0, 0.0)
    P, eps = {}, {}
    for c in ('Ex', 'Ey', 'Ez'):
        X, Y = g.positions(c)
        eps[c] = np.where(film(X, Y), n_film ** 2, np.where(Y < 0, EPS_S, EPS_C)).astype(complex)
        P[c] = (D33 * ey(Y) ** 2 * film(X, Y)).astype(complex) if c == 'Ey' else np.zeros_like(X, dtype=complex)
    kz = 2 * np.pi * N_P / (LAM * 1e-9)
    sol = cf.solve(g, eps, P, LAM, kz, npml=npml, periodic_x=True)
    E, Hh = sol['E'], sol['H']
    Ex = cf._centre(E['Ex'], 0); Ez = cf._centre(cf._centre(E['Ez'], 0), 1)
    Hx = cf._centre(Hh['Hx'], 1); Hz = Hh['Hz']
    Sy = 0.5 * np.real(Ez * np.conj(Hx) - Ex * np.conj(Hz))
    j0 = npml + 4
    return -np.mean(Sy[j0, :])


def one_d(n_film):
    v = [c1.solve_1d(LAM, N_P, EPS_S, n_film ** 2, EPS_C, H, lambda y: EY0 * np.ones_like(y), D33, d_nm=d)['to_substrate']
         for d in (0.25, 0.125)]
    return 2 * v[1] - v[0]


if __name__ == '__main__':
    ds = [float(x) for x in (sys.argv[1] if len(sys.argv) > 1 else '10,7.5,5,3,2').split(',')]
    films = [complex(f) for f in (sys.argv[2].split(';') if len(sys.argv) > 2 else
                                  ['3.0307+0j', '3.0+0j', '3.0307+0.1j', '3.0307+0.2j', '3.0658+0.5894j'])]
    for n in films:
        ref = one_d(n)
        print(f"n={n}: 1D {ref:.4e}  2D(periodic)/1D  " +
              '  '.join(f"d={d:g}: {periodic_2d(n, d) / ref:.3f}" for d in ds), flush=True)
