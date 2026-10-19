"""Validate the 2D FDFD (cerenkov_fdfd) against the independent 1D layered reference
(cerenkov_1d) for a WIDE uniform film: flux density through the bottom of the box, central 1 um,
per unit width. Prints 2D/1D for several film indices and cell sizes. No EMode.
Usage: python validate_cerenkov_1d.py [d1,d2,...] ["3+0.4j;3+0j"]"""
import sys
import numpy as np
import cerenkov_1d as c1
import cerenkov_fdfd as cf

LAM, N_P, H, D33, EY0 = 225.0, 2.22, 350.0, 30e-12, 1e5
EPS_S, EPS_C = 2.637 ** 2, 1.524 ** 2


def two_d(n_film, d_nm, half_src=900.0, margin=500.0, npml=20, ss=1):
    x0, x1 = -half_src - margin - npml * d_nm, half_src + margin + npml * d_nm
    y0, y1 = -margin - npml * d_nm, H + margin + npml * d_nm
    g = cf.YeeGrid(x0, x1, y0, y1, d_nm)
    xs = np.arange(-half_src, half_src + 0.1, 5.0)
    ys = np.arange(0.0, H + 0.1, 5.0)
    ey = np.full((len(ys), len(xs)), EY0, dtype=complex)
    pump = {'x': xs, 'y': ys, 'Ex': 0 * ey, 'Ey': ey, 'Ez': 0 * ey}
    film = lambda X, Y: (Y >= 0) & (Y <= H)
    eps_fn = lambda X, Y, comp: np.where(film(X, Y), n_film ** 2, np.where(Y < 0, EPS_S, EPS_C)).astype(complex)
    d_fn = lambda X, Y: {'d33': film(X, Y) * D33, 'd31': 0 * X, 'd15': 0 * X}
    res = cf.cerenkov_from_pump(g, eps_fn, d_fn, pump, LAM, N_P, npml=npml, supersample=ss)
    sol = res['solution']
    E, Hh = sol['E'], sol['H']
    Ex = cf._centre(E['Ex'], 0); Ey_ = cf._centre(E['Ey'], 1); Ez = cf._centre(cf._centre(E['Ez'], 0), 1)
    Hx = cf._centre(Hh['Hx'], 1); Hz = Hh['Hz']
    Sy = 0.5 * np.real(Ez * np.conj(Hx) - Ex * np.conj(Hz))
    j0 = npml + 4
    xc = g.x + 0.5 * d_nm
    sel = np.abs(xc) < 300.0
    flux_per_width = -np.sum(Sy[j0, sel]) * (d_nm * 1e-9) / (sel.sum() * d_nm * 1e-9)
    return flux_per_width


def one_d(n_film):
    out = []
    for d in (0.5, 0.25):
        r = c1.solve_1d(LAM, N_P, EPS_S, n_film ** 2, EPS_C, H, lambda y: EY0 * np.ones_like(y), D33, d_nm=d)
        out.append(r['to_substrate'])
    return 2 * out[1] - out[0]  # first-order Richardson


if __name__ == '__main__':
    ds = [float(x) for x in (sys.argv[1] if len(sys.argv) > 1 else '10,7.5,5').split(',')]
    films = [complex(f) for f in (sys.argv[2].split(';') if len(sys.argv) > 2 else
                                  ['3+0.4j', '3.138+0.738j', '3+0.1j', '3+0j'])]
    for n_film in films:
        ref = one_d(n_film)
        row = []
        for d in ds:
            row.append(f"d={d:g}: {two_d(n_film, d) / ref:.3f}")
        print(f"film n={n_film}: 1D reference {ref:.4e} W/m^2 ;  2D/1D  " + '  '.join(row), flush=True)
