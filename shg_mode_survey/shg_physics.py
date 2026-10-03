"""SHG figures of merit from exported mode fields -- pure numpy, no EMode dependency.

Conventions (see PLAN.md):
  - Lab axes as in EMode: x lateral, y vertical, z propagation. Wurtzite c-axis along y.
  - Fields are complex phasors in the Re-convention, E(t) = Re[E e^{-i w t}], arrays of shape
    (ny, nx) on a grid with x, y in nm. EMode returns E in V/m and H in A/m consistently
    (checked: 0.5 Re(E x H*) integrates to ~1.05x the paraxial n|E_t|^2 / (2 eta0) estimate).
  - EMode normalizes each mode so that integral(Sz) dA = 1 [nm^2 units] with Sz = Re(E x H*)_z
    (no 1/2 -- confirmed: int Sz / int 0.5 Re(E x H*) = 2.000). We do NOT rely on that: every
    mode is renormalized here to a physical power 0.5 Re int (E x H*)_z dA = 1 W.

Coupled-mode result (undepleted pump, perfect phase matching), with modes normalized to 1 W:
    dA_SH/dz = (w_SH eps0 / 4) * O * A_p^2,  O = int E_SH* . (d : E_p E_p) dA     [chi(2) regions]
    eta_norm = (w_SH eps0 / 4)^2 |O|^2                                                  [1/(W m^2)]
which reduces to the textbook 8 pi^2 d^2 / (eps0 c n_p^2 n_SH lambda_p^2 A) for plane waves of
area A (see test_shg_physics.py).
"""

import numpy as np

EPS0 = 8.8541878128e-12
C0 = 299792458.0
ETA0 = 376.730313668

# Wurtzite (6mm) tensor in pm/V. Kleinman d15 = d31 unless given separately (PLAN.md caveat).
D_TENSORS_PM_PER_V = {
    'AlN': {'d33': 4.7, 'd31': 0.1, 'd15': 0.1},
}


def wurtzite_d_components(d33, d31, d15=None):
    """{'d33', 'd31', 'd15'} in m/V from pm/V inputs (d15 defaults to d31 -- Kleinman)."""
    d15 = d31 if d15 is None else d15
    return {'d33': d33 * 1e-12, 'd31': d31 * 1e-12, 'd15': d15 * 1e-12}


def cell_areas_m2(x_nm, y_nm):
    """Per-pixel area [m^2], shape (ny, nx), for a (possibly non-uniform) tensor grid."""
    dx = np.gradient(np.asarray(x_nm, dtype=float))
    dy = np.gradient(np.asarray(y_nm, dtype=float))
    return dy[:, None] * dx[None, :] * 1e-18


def mode_power_W(f, dA):
    """Physical power 0.5 Re int (E x H*)_z dA [W] (for E in V/m, H in A/m)."""
    return 0.5 * np.sum(np.real(f['Ex'] * np.conj(f['Hy']) - f['Ey'] * np.conj(f['Hx'])) * dA)


def normalize_to_1W(f, dA):
    """Copy of field dict `f` (Ex, Ey, Ez, Hx, Hy, Hz, ...) scaled to carry 1 W."""
    p = mode_power_W(f, dA)
    if not p > 0:
        raise ValueError(f"non-positive mode power {p!r} -- backward or evanescent mode?")
    s = 1.0 / np.sqrt(p)
    return {k: (v * s if k[0] in 'EH' else v) for k, v in f.items()}


def nonlinear_source(Ep, d):
    """d : E_p E_p for wurtzite with c along y -- the vector (Px, Py, Pz) / eps0, in V/m units
    times m/V. `d` is a dict of (ny, nx) arrays (or scalars) 'd33', 'd31', 'd15' in m/V, zero
    outside chi(2) regions.

    Crystal frame (a, b, c) -> lab (x, z, y):  P_c = d31 (E_a^2 + E_b^2) + d33 E_c^2,
    P_a = 2 d15 E_a E_c, P_b = 2 d15 E_b E_c.
    """
    Ex, Ey, Ez = Ep['Ex'], Ep['Ey'], Ep['Ez']
    Px = 2 * d['d15'] * Ex * Ey
    Py = d['d31'] * (Ex * Ex + Ez * Ez) + d['d33'] * Ey * Ey
    Pz = 2 * d['d15'] * Ez * Ey
    return Px, Py, Pz


def shg_overlap(Es, Ep, d, dA):
    """O = int E_SH* . (d : E_p E_p) dA for 1 W-normalized modes. Complex, units m/V * (V/m)^3 m^2."""
    Px, Py, Pz = nonlinear_source(Ep, d)
    return np.sum((np.conj(Es['Ex']) * Px + np.conj(Es['Ey']) * Py + np.conj(Es['Ez']) * Pz) * dA)


def overlap_shape_factor(Es, Ep, d, dA):
    """Dimensionless 0..1: |O| / sqrt(int|E_SH|^2 dA * int|d:E_pE_p|^2 dA), integrals over the
    chi(2) region only (where any d != 0). 1 means the SH mode's field inside the nonlinear
    material is exactly proportional to the driving polarization -- pure 'shape' overlap,
    independent of how big d is (NCE carries that).
    """
    Px, Py, Pz = nonlinear_source(Ep, d)
    nl = (np.abs(d['d33']) + np.abs(d['d31']) + np.abs(d['d15'])) * np.ones_like(np.real(Px)) > 0
    O = np.sum((np.conj(Es['Ex']) * Px + np.conj(Es['Ey']) * Py + np.conj(Es['Ez']) * Pz) * dA)
    es2 = np.sum((np.abs(Es['Ex'])**2 + np.abs(Es['Ey'])**2 + np.abs(Es['Ez'])**2) * dA * nl)
    p2 = np.sum((np.abs(Px)**2 + np.abs(Py)**2 + np.abs(Pz)**2) * dA)
    if es2 <= 0 or p2 <= 0:
        return 0.0
    return float(np.abs(O) / np.sqrt(es2 * p2))


def eta_norm_per_W_m2(O, wavelength_sh_nm):
    """Normalized conversion efficiency [1/(W m^2)] from the overlap O of 1 W-normalized modes."""
    w_sh = 2 * np.pi * C0 / (wavelength_sh_nm * 1e-9)
    return float((w_sh * EPS0 / 4) ** 2 * np.abs(O) ** 2)


def eta_to_pct_per_W_cm2(eta):
    return eta * 100.0 / 1e4


def shg_effective_area_um2(eta, n_p, n_sh, wavelength_pump_nm, d_ref_m_per_V):
    """A_SHG [um^2] defined by eta = 8 pi^2 d_ref^2 / (eps0 c n_p^2 n_SH lambda_p^2 A_SHG) --
    the plane-wave-equivalent interaction area for a reference d (AlN d33); smaller is better.
    """
    if eta <= 0:
        return np.inf
    lam = wavelength_pump_nm * 1e-9
    return float(8 * np.pi**2 * d_ref_m_per_V**2 / (EPS0 * C0 * n_p**2 * n_sh * lam**2 * eta) * 1e12)


def intensity_effective_area_um2(f, dA):
    """Standard A_eff = (int |E|^2 dA)^2 / int |E|^4 dA [um^2], whole window."""
    e2 = np.abs(f['Ex'])**2 + np.abs(f['Ey'])**2 + np.abs(f['Ez'])**2
    return float(np.sum(e2 * dA) ** 2 / np.sum(e2**2 * dA) * 1e12)


def transverse_similarity(fa, fb, dA):
    """|<Et_a, Et_b>| / (|Et_a| |Et_b|) in 0..1 -- for tracking the same mode between nearby
    wavelengths (cheap, numpy-only; avoids EMode's overlap() which has crashed under load).
    """
    num = np.abs(np.sum((np.conj(fa['Ex']) * fb['Ex'] + np.conj(fa['Ey']) * fb['Ey']) * dA))
    na = np.sum((np.abs(fa['Ex'])**2 + np.abs(fa['Ey'])**2) * dA)
    nb = np.sum((np.abs(fb['Ex'])**2 + np.abs(fb['Ey'])**2) * dA)
    return float(num / np.sqrt(na * nb)) if na > 0 and nb > 0 else 0.0


def db_per_m_to_per_m(db):
    return db * np.log(10) / 10.0


def loss_limited_length(eta, alpha_p_db_m, alpha_s_db_m, l_max_m=0.2):
    """With power-loss coefficients alpha_p (pump) and alpha_s (SH):
        P_SH(L) = eta P_p^2 L_eff^2,  L_eff = e^{-a_s L/2} (e^{D L} - 1)/D,  D = a_s/2 - a_p.
    Returns (L_opt [m], L_eff at L_opt [m], peak efficiency eta*L_eff^2 [1/W]). If the optimum
    is beyond l_max_m (e.g. lossless), it is reported at l_max_m.
    """
    a_p = db_per_m_to_per_m(max(alpha_p_db_m, 0.0))
    a_s = db_per_m_to_per_m(max(alpha_s_db_m, 0.0))
    L = np.linspace(1e-6, l_max_m, 20001)
    D = a_s / 2 - a_p
    if abs(D) < 1e-12:
        leff = L * np.exp(-a_s * L / 2)
    else:  # = e^{-a_s L/2} (e^{D L} - 1) / D, written without overflow
        leff = (np.exp(-a_p * L) - np.exp(-a_s * L / 2)) / D
    i = int(np.argmax(leff))
    return float(L[i]), float(leff[i]), float(eta * leff[i] ** 2)


def _dominant_component(f):
    ex2 = np.sum(np.abs(f['Ex'])**2)
    ey2 = np.sum(np.abs(f['Ey'])**2)
    return f['Ey'] if ey2 >= ex2 else f['Ex']


def _sign_changes(line, thresh):
    s = np.sign(line[np.abs(line) > thresh])
    return int(np.sum(s[1:] != s[:-1])) if s.size > 1 else 0


def _typical_count(lines, thresh, weights):
    """Power-weighted most common sign-change count over a set of 1D cuts, and the weight
    fraction that agrees with it (low = hybrid / ambiguous mode)."""
    tally = {}
    for line, wgt in zip(lines, weights):
        c = _sign_changes(line, thresh)
        tally[c] = tally.get(c, 0.0) + wgt
    if not tally:
        return 0, 1.0
    best = max(tally, key=tally.get)
    return best, tally[best] / sum(tally.values())


def count_nodes(f, mask=None, rel_threshold=0.08):
    """(m, n, agreement) = (lateral, vertical) node counts of the dominant transverse
    component: sign changes along each row (lateral) / column (vertical) through the core,
    ignoring pixels below rel_threshold * max, taking the power-weighted most common count.
    `agreement` (0..1) is the smaller of the two consensus fractions -- below ~0.6 the mode is
    a hybrid without a clean TMmn identity. Heuristic -- check field plots when it matters.
    """
    F = _dominant_component(f)
    k = np.argmax(np.abs(F))
    F = np.real(F * np.exp(-1j * np.angle(F.flat[k])))
    thresh = rel_threshold * np.abs(F).max()
    rows = np.where(mask.any(axis=1))[0] if mask is not None else np.arange(F.shape[0])
    cols = np.where(mask.any(axis=0))[0] if mask is not None else np.arange(F.shape[1])
    m, am = _typical_count([F[r, :] for r in rows], thresh, [np.sum(F[r, :] ** 2) for r in rows])
    n, an = _typical_count([F[:, c] for c in cols], thresh, [np.sum(F[:, c] ** 2) for c in cols])
    return m, n, min(am, an)


def mode_label(f, te_fraction, mask=None):
    """'TMmn' / 'TEmn' (m lateral, n vertical nodes); suffix '?' when the node pattern is
    ambiguous (hybrid mode, agreement < 0.6)."""
    m, n, agree = count_nodes(f, mask)
    return f"{'TE' if te_fraction >= 0.5 else 'TM'}{m}{n}{'' if agree >= 0.6 else '?'}"


def cerenkov_flags(n_eff_pump, regions_n_sh):
    """For each cladding/substrate region: is n_region(lambda_SH) > n_eff,pump (Cerenkov SH
    allowed into that region) and at what angle to the waveguide axis.

    `regions_n_sh` = list of {'name', 'n', 'extent': 'bulk'|'finite'}. Returns list of dicts
    with 'allowed' and 'angle_deg' (NaN if not allowed).
    """
    out = []
    for r in regions_n_sh:
        allowed = r['n'] > n_eff_pump
        out.append({'name': r['name'], 'extent': r['extent'], 'n_region_sh': r['n'],
                    'allowed': bool(allowed),
                    'angle_deg': float(np.degrees(np.arccos(n_eff_pump / r['n']))) if allowed else np.nan})
    return out
