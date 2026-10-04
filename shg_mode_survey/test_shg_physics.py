"""Checks for shg_physics.py that don't need EMode. Run: python test_shg_physics.py"""

import numpy as np

import shg_physics as sp


def tophat_mode(x, y, n, half_w, half_h, pol='y', lobes=1):
    """Ey- (or Ex-) polarized top-hat 'mode' in a uniform medium, H = (n/eta0) z x E.
    lobes=2 makes it antisymmetric in x (sign flip at x=0)."""
    X, Y = np.meshgrid(x, y)
    E = ((np.abs(X) <= half_w) & (np.abs(Y) <= half_h)).astype(complex)
    if lobes == 2:
        E *= np.sign(X + 1e-9)
    zero = np.zeros_like(E)
    if pol == 'y':
        return {'Ex': zero, 'Ey': E, 'Ez': zero, 'Hx': -n * E / sp.ETA0, 'Hy': zero, 'Hz': zero}
    return {'Ex': E, 'Ey': zero, 'Ez': zero, 'Hx': zero, 'Hy': n * E / sp.ETA0, 'Hz': zero}


def test_plane_wave_limit():
    x = np.linspace(-1000, 1000, 401)
    y = np.linspace(-1000, 1000, 401)
    dA = sp.cell_areas_m2(x, y)
    n_p, n_s, lam_sh = 2.1, 2.1, 225.0
    p = sp.normalize_to_1W(tophat_mode(x, y, n_p, 300, 200), dA)
    s = sp.normalize_to_1W(tophat_mode(x, y, n_s, 300, 200), dA)
    d = {'d33': 4.7e-12, 'd31': 0.0, 'd15': 0.0}
    eta = sp.eta_norm_per_W_m2(sp.shg_overlap(s, p, d, dA), lam_sh)
    area = np.sum(np.abs(p['Ey']) > 0) * dA[0, 0]
    expected = 8 * np.pi**2 * (4.7e-12)**2 / (sp.EPS0 * sp.C0 * n_p**2 * n_s * (2 * lam_sh * 1e-9)**2 * area)
    assert abs(eta / expected - 1) < 1e-6, (eta, expected)
    a_shg = sp.shg_effective_area_um2(eta, n_p, n_s, 2 * lam_sh, 4.7e-12)
    assert abs(a_shg / (area * 1e12) - 1) < 1e-6
    assert abs(sp.overlap_shape_factor(s, p, d, dA) - 1) < 1e-9
    print(f"plane-wave limit OK: eta={sp.eta_to_pct_per_W_cm2(eta):.1f} %/W/cm^2, A={area * 1e12:.3f} um^2")


def test_symmetry_forbidden():
    x = np.linspace(-1000, 1000, 400)  # no point exactly at x=0
    y = np.linspace(-1000, 1000, 400)
    dA = sp.cell_areas_m2(x, y)
    d = {'d33': 4.7e-12, 'd31': 0.1e-12, 'd15': 0.1e-12}
    p_odd = sp.normalize_to_1W(tophat_mode(x, y, 2.0, 300, 200, lobes=2), dA)  # "TM10"-like pump
    s_odd = sp.normalize_to_1W(tophat_mode(x, y, 2.3, 300, 200, lobes=2), dA)  # odd-class SH
    s_even = sp.normalize_to_1W(tophat_mode(x, y, 2.3, 300, 200), dA)
    o_forbidden = abs(sp.shg_overlap(s_odd, p_odd, d, dA))
    o_allowed = abs(sp.shg_overlap(s_even, p_odd, d, dA))
    assert o_forbidden < 1e-12 * o_allowed, (o_forbidden, o_allowed)
    print(f"symmetry OK: odd-pump->odd-SH {o_forbidden:.2e} vs ->even-SH {o_allowed:.2e}")


def test_loss_limited_length():
    L, leff, peak = sp.loss_limited_length(1.0, 0.0, 0.0, l_max_m=0.01)
    assert abs(leff - 0.01) < 1e-9 and abs(peak - 1e-4) < 1e-9
    L, leff, _ = sp.loss_limited_length(1.0, 500.0, 5000.0)  # 5 / 50 dB/cm
    assert 0 < L < 0.2 and leff < L
    print(f"loss-limited OK: 5 dB/cm pump, 50 dB/cm SH -> L_opt={L * 1e3:.2f} mm, L_eff={leff * 1e3:.2f} mm")


def test_overlap_terms():
    rng = np.random.default_rng(0)
    shp = (40, 50)
    dA = np.full(shp, 1e-16)
    rnd = lambda: rng.normal(size=shp) + 1j * rng.normal(size=shp)  # noqa: E731
    Es = {k: rnd() for k in ('Ex', 'Ey', 'Ez')}
    Ep = {k: rnd() for k in ('Ex', 'Ey', 'Ez')}
    d = {'d33': 4.7e-12, 'd31': 0.3e-12, 'd15': 0.2e-12}
    t = sp.overlap_terms(Es, Ep, d, dA, 225.0)
    assert abs(t['overlap_abs'] - abs(sp.shg_overlap(Es, Ep, d, dA))) < 1e-9 * t['overlap_abs']
    assert abs(t['share_d33'] + t['share_d31'] + t['share_d15'] - 1) < 1e-12
    print(f"overlap terms OK: shares d33/d31/d15 = {t['share_d33']:.3f}/{t['share_d31']:.3f}/{t['share_d15']:.3f}")


if __name__ == '__main__':
    test_plane_wave_limit()
    test_symmetry_forbidden()
    test_loss_limited_length()
    test_overlap_terms()
    print('all passed')
