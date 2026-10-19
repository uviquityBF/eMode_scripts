"""No-EMode tests for the Ridge window fix and the FDFD substrate options (aniso / k / finite
layer), using a synthetic Gaussian TM-like pump. Run: python test_cerenkov_model.py"""
import numpy as np
import cerenkov_fdfd as cf
import cerenkov_run as cr
import geometry as geo

LAM = 225.0
N_EFF = 2.22


def ridge(sub_h, **kw):
    return geo.Ridge(h_core=350.0, w_core=400.0, substrate_height=sub_h,
                     substrate_eq_o=geo.AlN_EQ_O, substrate_eq_e=geo.AlN_EQ_E, core_chi2='AlN', **kw)


def kappa(g, d_nm=10.0, **opts):
    n_reg = {'substrate': geo.eval_index_equation(geo.AlN_EQ_E, LAM), 'topclad': 1.524}
    x = np.arange(-600.0, 600.1, 10.0)
    y = np.arange(g.params['substrate_height'] - 300.0, g.params['substrate_height'] + 650.1, 10.0)
    X, Y = np.meshgrid(x, y)
    yc = g.params['substrate_height'] + 175.0
    ey = np.exp(-(X / 150.0) ** 2 - ((Y - yc) / 120.0) ** 2).astype(complex) * 1e5
    pump = {'x': x, 'y': y, 'Ex': 0 * ey, 'Ey': ey, 'Ez': 0 * ey}
    grid = cr.domain_for(g, d_nm, finite_layer=opts.get('under_n') is not None)
    eps = g.eps_fn(LAM, n_reg, **opts)
    d_fn = g.d_fn({'AlN': {'d33': 30.0, 'd31': 1.0, 'd15': 1.0}})
    return cf.cerenkov_from_pump(grid, eps, d_fn, pump, LAM, N_EFF)


def test_window():
    assert ridge(500.0).window_margin == 2000.0 and ridge(1000.0).window_margin == 2000.0  # legacy kept
    g = ridge(2000.0)
    assert g.window_margin == 3000.0
    g.check_window()
    # the legacy window would have cut the clad off
    assert 2000.0 + 350.0 + 800.0 + g.WINDOW_SPARE_NM > 350.0 + 2000.0
    print('window OK: legacy margin kept <=1000 nm substrate, 2000 nm auto-expands to 3000')


def test_layer_matches_halfspace():
    g = ridge(1000.0)
    ref = kappa(g)
    # under_n == substrate index everywhere: a "finite layer" with no contrast is the half-space
    same = kappa(g, under_n=geo.eval_index_equation(geo.AlN_EQ_E, LAM))
    r = same['total_W_per_m'] / ref['total_W_per_m']
    assert abs(r - 1) < 0.02, r
    print(f'layer-without-contrast == half-space OK (ratio {r:.4f}, kappa {ref["total_W_per_m"]:.3e})')


def test_absorption():
    g = ridge(1000.0)
    a = kappa(g)
    b = kappa(g, substrate_k=0.02)
    assert b['total_W_per_m'] < a['total_W_per_m']
    absorbed = b['source_work_W_per_m'] - b['total_W_per_m']
    assert absorbed > 0
    print(f"substrate k=0.02 OK: escaping flux {b['total_W_per_m'] / a['total_W_per_m']:.3f} of lossless; "
          f"absorbed {absorbed / b['source_work_W_per_m']:.2f} of source work")


def test_thickness_oscillation():
    ks = []
    for h in (500.0, 540.0, 580.0, 620.0, 660.0, 700.0):
        r = kappa(ridge(h), under_n=1.85)
        ks.append(r['total_W_per_m'])
        assert 0.97 < r['total_W_per_m'] / r['source_work_W_per_m'] < 1.03
    print('sapphire-backed layer, kappa vs H:', ['%.3e' % k for k in ks])
    assert max(ks) / min(ks) > 1.1, 'expected Fabry-Perot modulation of kappa with layer thickness'
    print('finite-layer thickness modulation OK (max/min = %.2f)' % (max(ks) / min(ks)))


def test_aniso_changes_result():
    g = ridge(1000.0)
    a, b = kappa(g), kappa(g, aniso_substrate=True)
    print(f"aniso substrate kappa / scalar-n_e kappa = {b['total_W_per_m'] / a['total_W_per_m']:.3f}")
    assert b['total_W_per_m'] != a['total_W_per_m']


if __name__ == '__main__':
    test_window(); test_layer_matches_halfspace(); test_absorption()
    test_aniso_changes_result(); test_thickness_oscillation()
    print('all passed')
