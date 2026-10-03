"""Step 1b: radiated (Cerenkov / leaky / slab-coupled) SH power from a guided pump, via a driven
2D full-vector FDFD solve. Pure numpy/scipy -- no EMode calls. See PLAN.md "Step 1b".

The pump mode (1 W, field E_p, effective index n_p at lambda_p = 2 lambda_SH) drives
    P_NL(x, y) e^{i kz z},   P_NL / eps0 = d : E_p E_p,   kz = 2 beta_p = 2 pi n_p / lambda_SH.
We solve, on the cross-section with SC-PML on all four sides,
    curl curl E - k0^2 eps(x, y) E = k0^2 P_NL / eps0          (d/dz -> i kz, k0 at lambda_SH)
for the steady-state SH field E(x, y) e^{i kz z}. Because kz is fixed by the pump, the SH is
NOT a guided mode: power leaves transversely at a constant rate per unit length,
    dP_SH/dz = kappa_C P_pump^2        (kappa_C reported in %/W/cm  ==  1/(W m) numerically)
measured as the Poynting flux through a box just inside the PML, split by side (substrate /
top clad / left / right), and cross-checked against the work done by the source,
    dP/dz = (omega / 2) int Im(P_NL* . E) dA     (= radiated + absorbed, if eps is complex).

If a *guided* SH mode has n_eff ~= n_p (true phase matching), the driven problem resonates --
that case belongs to the guided survey; `solve` reports the field energy so it can be spotted.

Grid: Yee layout on a uniform grid of nx x ny cells, coordinates in nm. Ex at (i+1/2, j),
Ey at (i, j+1/2), Ez at (i, j); Hx at (i, j+1/2), Hy at (i+1/2, j), Hz at (i+1/2, j+1/2).
eps is diagonal (anisotropic AlN: [n_o^2, n_e^2, n_o^2]) and sampled at each E component's
own position.
"""

import numpy as np
import scipy.sparse as sps
import scipy.sparse.linalg as spla

EPS0 = 8.8541878128e-12
MU0 = 1.25663706212e-6
C0 = 299792458.0


class YeeGrid:
    def __init__(self, x0_nm, x1_nm, y0_nm, y1_nm, d_nm):
        self.d = float(d_nm)
        self.nx = int(round((x1_nm - x0_nm) / d_nm))
        self.ny = int(round((y1_nm - y0_nm) / d_nm))
        self.x = x0_nm + d_nm * np.arange(self.nx)     # integer nodes
        self.y = y0_nm + d_nm * np.arange(self.ny)
        self.xh = self.x + 0.5 * d_nm                   # half nodes
        self.yh = self.y + 0.5 * d_nm

    def positions(self, comp):
        """(X, Y) meshgrids [nm], shape (ny, nx), for 'Ex','Ey','Ez','Hx','Hy','Hz'."""
        xs = {'Ex': self.xh, 'Ey': self.x, 'Ez': self.x, 'Hx': self.x, 'Hy': self.xh, 'Hz': self.xh}[comp]
        ys = {'Ex': self.y, 'Ey': self.yh, 'Ez': self.y, 'Hx': self.yh, 'Hy': self.y, 'Hz': self.yh}[comp]
        return np.meshgrid(xs, ys)


def _pml_s(n, npml, k0_um, d_um, half, R=1e-10, m=3):
    """Complex stretch factors along one axis at integer (half=False) or half (half=True)
    nodes. sigma ramps as (depth/L)^m inside npml cells at each end."""
    pos = np.arange(n) + (0.5 if half else 0.0)
    L = npml * d_um
    depth = np.zeros(n)
    left = npml - pos
    right = pos - (n - 1 - npml)
    depth = np.maximum(depth, np.maximum(left, 0)) + np.maximum(right, 0)
    depth = np.clip(depth * d_um, 0, L)
    sigma_max = -(m + 1) * np.log(R) / (2 * L)          # [1/um], normalized by k0 below
    return 1 + 1j * sigma_max * (depth / L) ** m / k0_um


def _deriv_1d(n, d_um):
    """Forward difference (f[i+1]-f[i])/d with a PEC wall beyond the last node."""
    return sps.diags([-np.ones(n), np.ones(n - 1)], [0, 1], shape=(n, n), format='csr') / d_um


def build_operators(grid, k0_um, kz_um, npml):
    """Sparse curl operators (in 1/um) with SC-PML. Returns (Ce, Ch) such that
    curl E = Ce @ [Ex,Ey,Ez] (H positions) and curl H = Ch @ [Hx,Hy,Hz] (E positions)."""
    nx, ny, d = grid.nx, grid.ny, grid.d * 1e-3
    Ix, Iy = sps.identity(nx, format='csr'), sps.identity(ny, format='csr')
    dxf, dyf = _deriv_1d(nx, d), _deriv_1d(ny, d)
    dxb, dyb = -dxf.T.tocsr(), -dyf.T.tocsr()
    # stretch: forward derivatives land on half nodes, backward on integer nodes
    sx_h, sx_i = _pml_s(nx, npml, k0_um, d, True), _pml_s(nx, npml, k0_um, d, False)
    sy_h, sy_i = _pml_s(ny, npml, k0_um, d, True), _pml_s(ny, npml, k0_um, d, False)
    Dxf = sps.kron(Iy, sps.diags(1 / sx_h) @ dxf)
    Dxb = sps.kron(Iy, sps.diags(1 / sx_i) @ dxb)
    Dyf = sps.kron(sps.diags(1 / sy_h) @ dyf, Ix)
    Dyb = sps.kron(sps.diags(1 / sy_i) @ dyb, Ix)
    N = nx * ny
    I = sps.identity(N, format='csr')
    Z = sps.csr_matrix((N, N))
    ikz = 1j * kz_um
    Ce = sps.bmat([[Z, -ikz * I, Dyf],
                   [ikz * I, Z, -Dxf],
                   [-Dyf, Dxf, Z]], format='csr')
    Ch = sps.bmat([[Z, -ikz * I, Dyb],
                   [ikz * I, Z, -Dxb],
                   [-Dyb, Dxb, Z]], format='csr')
    return Ce, Ch


def solve(grid, eps, P_over_eps0, lam_sh_nm, kz_per_m, npml=20):
    """Driven solve. eps / P_over_eps0: dicts 'Ex','Ey','Ez' -> (ny, nx) arrays at the Yee
    positions (P_over_eps0 in V/m for a 1 W pump). Returns dict with E, H fields (SI),
    and diagnostics (see radiated_power)."""
    k0_um = 2 * np.pi / (lam_sh_nm * 1e-3)
    kz_um = kz_per_m * 1e-6
    Ce, Ch = build_operators(grid, k0_um, kz_um, npml)
    epsv = np.concatenate([eps[c].ravel() for c in ('Ex', 'Ey', 'Ez')])
    A = (Ch @ Ce - k0_um ** 2 * sps.diags(epsv)).tocsc()
    b = k0_um ** 2 * np.concatenate([P_over_eps0[c].ravel() for c in ('Ex', 'Ey', 'Ez')])
    e = spla.spsolve(A, b)
    omega = 2 * np.pi * C0 / (lam_sh_nm * 1e-9)
    h = (Ce @ e) * 1e6 / (1j * omega * MU0)             # curl in 1/um -> 1/m
    N = grid.nx * grid.ny
    shp = (grid.ny, grid.nx)
    E = {c: e[i * N:(i + 1) * N].reshape(shp) for i, c in enumerate(('Ex', 'Ey', 'Ez'))}
    H = {c: h[i * N:(i + 1) * N].reshape(shp) for i, c in enumerate(('Hx', 'Hy', 'Hz'))}
    return {'E': E, 'H': H, 'omega': omega, 'npml': npml, 'grid': grid}


def _centre(a, axis):
    """Average neighbours along axis (half-node -> integer node shift by +1/2 cell)."""
    return 0.5 * (a + np.roll(a, -1, axis=axis))


def radiated_power(sol, P_over_eps0, margin=4):
    """Transverse Poynting flux [W/m per W^2 of pump] out of a box `margin` cells inside the
    PML, per side, plus the source-work cross-check. All quantities at cell corners
    (i+1/2, j+1/2) after averaging."""
    g, E, H, npml = sol['grid'], sol['E'], sol['H'], sol['npml']
    d_m = g.d * 1e-9
    # bring everything to (i+1/2, j+1/2)
    Ex = _centre(E['Ex'], 0)
    Ey = _centre(E['Ey'], 1)
    Ez = _centre(_centre(E['Ez'], 0), 1)
    Hx = _centre(H['Hx'], 1)
    Hy = _centre(H['Hy'], 0)
    Hz = H['Hz']
    Sx = 0.5 * np.real(Ey * np.conj(Hz) - Ez * np.conj(Hy))
    Sy = 0.5 * np.real(Ez * np.conj(Hx) - Ex * np.conj(Hz))
    i0, i1 = npml + margin, g.nx - npml - margin - 1
    j0, j1 = npml + margin, g.ny - npml - margin - 1
    sides = {
        'bottom': -np.sum(Sy[j0, i0:i1]) * d_m,
        'top': np.sum(Sy[j1, i0:i1]) * d_m,
        'left': -np.sum(Sx[j0:j1, i0]) * d_m,
        'right': np.sum(Sx[j0:j1, i1]) * d_m,
    }
    # source work: (omega/2) int Im(P* . E) dA, P = eps0 * P_over_eps0
    work = 0.5 * sol['omega'] * EPS0 * sum(
        np.sum(np.imag(np.conj(P_over_eps0[c]) * E[c])) for c in ('Ex', 'Ey', 'Ez')) * d_m ** 2
    total = sum(sides.values())
    return {'total_W_per_m': total, 'sides_W_per_m': sides, 'source_work_W_per_m': work,
            'kappa_pct_per_W_cm': total}  # 1/(W m) == %/(W cm)


# ------------------------------------------------------------------ pump -> source, geometry
def sample_on(grid, x_nm, y_nm, field, comp):
    """Bilinear interpolation of a (ny, nx) complex field from an EMode grid onto a Yee
    component's positions (zero outside the source grid)."""
    from scipy.interpolate import RegularGridInterpolator
    X, Y = grid.positions(comp)
    pts = np.column_stack([Y.ravel(), X.ravel()])
    out = np.zeros(X.size, dtype=complex)
    for part, mult in ((np.real(field), 1), (np.imag(field), 1j)):
        f = RegularGridInterpolator((y_nm, x_nm), part, bounds_error=False, fill_value=0.0)
        out += mult * f(pts)
    return out.reshape(X.shape)


def cerenkov_from_pump(grid, eps_fn, d_fn, pump, lam_sh_nm, n_eff_pump, npml=20):
    """Radiated SH power for a 1 W pump.
    eps_fn(X, Y, comp) -> eps array at those positions (lambda_SH); d_fn(X, Y) -> dict of d33,
    d31, d15 [m/V] arrays; pump = {'x','y','Ex','Ey','Ez'} (1 W normalized, nm grid)."""
    Ep = {c: {comp: sample_on(grid, pump['x'], pump['y'], pump[comp], c) for comp in ('Ex', 'Ey', 'Ez')}
          for c in ('Ex', 'Ey', 'Ez')}
    P = {}
    for c in ('Ex', 'Ey', 'Ez'):
        X, Y = grid.positions(c)
        d = d_fn(X, Y)
        ex, ey, ez = Ep[c]['Ex'], Ep[c]['Ey'], Ep[c]['Ez']
        P[c] = {'Ex': 2 * d['d15'] * ex * ey,
                'Ey': d['d31'] * (ex * ex + ez * ez) + d['d33'] * ey * ey,
                'Ez': 2 * d['d15'] * ez * ey}[c]
    eps = {c: eps_fn(*grid.positions(c), c) for c in ('Ex', 'Ey', 'Ez')}
    kz = 2 * np.pi * n_eff_pump / (lam_sh_nm * 1e-9)
    sol = solve(grid, eps, P, lam_sh_nm, kz, npml=npml)
    res = radiated_power(sol, P)
    res['solution'] = sol
    return res
