"""Independent 1D reference for the driven Cerenkov problem in the wide-core limit (no EMode, no 2D
FDFD code shared). Layered medium along y (substrate | film | top clad), invariant along x, fixed
kz = n_p k0, source P_y(y) = eps0 * d33 * Ey(y)^2 in the film. e^{-i omega t}, e^{+i kz z}.

With Hx the only magnetic component:   d/dy[(1/eps) dHx/dy] + (k0^2 - kz^2/eps) Hx = omega kz Py / eps
(derivation in PLAN.md 2026-10-19 entry). Exact outgoing Robin conditions in the uniform
half-spaces (H' = -+ i q H, q = sqrt(k0^2 eps - kz^2), Im q > 0), so no PML and the only numerical
parameter is the fine grid spacing in the film (converges as d^2; use d <= 0.5 nm).

Returns escaping flux per unit x-width into the substrate / clad and the source work per width,
[W per m of length per m of width] for 1 (V/m) pump field profile as given.
"""
import numpy as np

EPS0 = 8.8541878128e-12
MU0 = 1.25663706212e-6
C0 = 299792458.0


def solve_1d(lam_nm, n_p, eps_sub, eps_film, eps_clad, h_nm, ey_of_y, d33_m_per_V, d_nm=0.5, pad_nm=20.0):
    """ey_of_y(y_nm) -> pump Ey [V/m] over 0 < y < h_nm (film from y=0 to h). eps_* complex."""
    k0 = 2 * np.pi / (lam_nm * 1e-9)
    kz = n_p * k0
    omega = C0 * k0
    d = d_nm * 1e-9
    y = np.arange(-pad_nm, h_nm + pad_nm + 1e-9, d_nm)
    n = len(y)
    yh = 0.5 * (y[1:] + y[:-1])                      # half nodes for the flux form
    eps_at = lambda yy: np.where(yy < 0, eps_sub, np.where(yy > h_nm, eps_clad, eps_film))
    eps = eps_at(y).astype(complex)
    a = 1.0 / eps_at(yh).astype(complex)
    Py = np.where((y >= 0) & (y <= h_nm), EPS0 * d33_m_per_V * ey_of_y(np.clip(y, 0, h_nm)) ** 2, 0.0)
    rhs = omega * kz * Py / eps
    main = np.zeros(n, complex); lo = np.zeros(n - 1, complex); up = np.zeros(n - 1, complex)
    main[:] = k0 ** 2 - kz ** 2 / eps
    main[1:] -= a / d ** 2
    main[:-1] -= a / d ** 2
    lo[:] = a / d ** 2
    up[:] = a / d ** 2
    q_s = np.sqrt(k0 ** 2 * eps_sub - kz ** 2 + 0j); q_s = q_s if q_s.imag >= 0 else -q_s
    q_c = np.sqrt(k0 ** 2 * eps_clad - kz ** 2 + 0j); q_c = q_c if q_c.imag >= 0 else -q_c
    # boundary rows: one-sided Robin  H' = -i q_s H (bottom), H' = +i q_c H (top)
    # half-cell finite volume at the ends: (a_half * (H1-H0)/d - a_edge * H'_edge)/(d/2) + (k0^2 - kz^2/eps0) H0 = rhs0
    a_edge_s = 1.0 / eps[0]
    main[0] = (-a[0] / d) / (d / 2) + (a_edge_s * 1j * q_s) / (d / 2) + (k0 ** 2 - kz ** 2 / eps[0])
    up[0] = (a[0] / d) / (d / 2)
    a_edge_c = 1.0 / eps[-1]
    main[-1] = (-a[-1] / d) / (d / 2) - (a_edge_c * 1j * q_c) / (d / 2) + (k0 ** 2 - kz ** 2 / eps[-1])
    lo[-1] = (a[-1] / d) / (d / 2)
    from scipy.linalg import solve_banded
    ab = np.zeros((3, n), complex)
    ab[0, 1:] = up
    ab[1, :] = main
    ab[2, :-1] = lo
    H = solve_banded((1, 1), ab, rhs.astype(complex))
    # flux: S_y = 1/2 Re(Ez Hx*), Ez = -i H'/(omega eps0 eps) in the source-free half-spaces
    Ez_s = -1j * (-1j * q_s * H[0]) / (omega * EPS0 * eps[0])
    Ez_c = -1j * (1j * q_c * H[-1]) / (omega * EPS0 * eps[-1])
    S_sub = -0.5 * np.real(Ez_s * np.conj(H[0]))      # outward = -y
    S_clad = 0.5 * np.real(Ez_c * np.conj(H[-1]))
    # source work per width: omega/2 * int Im(conj(P) . E) dy, Ey = -(kz Hx/(omega eps0) + Py/eps0)/eps
    Ey = -(kz * H / (omega * EPS0) + Py / EPS0) / eps
    work = 0.5 * omega * np.sum(np.imag(np.conj(Py) * Ey)) * d
    return {'to_substrate': float(S_sub), 'to_clad': float(S_clad), 'work': float(work)}
