"""Checks for geometry.py that don't need EMode. Run: python test_geometry.py"""

import numpy as np

import geometry as geo
import shg_physics as sp

# A toy complex index equation: n=2.0, k=0.5 at every wavelength (x unused).
CONST_EQ = '2.0+0.5j+0*x'


def test_eval_complex_index_equation():
    v = geo.eval_complex_index_equation(CONST_EQ, 225.0)
    assert abs(v.real - 2.0) < 1e-12 and abs(v.imag - 0.5) < 1e-12, v
    # eval_index_equation (real-only, used for EMode's own equation) drops k entirely
    assert abs(geo.eval_index_equation(CONST_EQ, 225.0) - 2.0) < 1e-12
    print(f"eval_complex_index_equation OK: {v!r}")


def test_material_loss_matches_shg_physics():
    # geometry.material_loss_dB_per_m and shg_physics.bulk_loss_dB_per_m are independent
    # implementations of the same alpha = 2 k0 k formula -- they must agree, and must agree with
    # a hand-written closed form.
    k, lam_nm = 1.4, 225.0
    expected = 4 * np.pi * k / (lam_nm * 1e-9) * 10 / np.log(10)
    a = geo.material_loss_dB_per_m(k, lam_nm)
    b = sp.bulk_loss_dB_per_m(1j * k, lam_nm)
    assert abs(a / expected - 1) < 1e-9, (a, expected)
    assert abs(a / b - 1) < 1e-9, (a, b)
    assert geo.material_loss_dB_per_m(-k, lam_nm) == 0.0  # never negative/gain
    print(f"material_loss_dB_per_m OK: k={k} @ {lam_nm} nm -> {a:.3e} dB/m (matches shg_physics)")


def test_loaded_lossy_mask_and_loss():
    base = dict(t_film=354.0, etch_depth=0.0, h_s=70.0, w_s=500.0)
    g_lossless = geo.make_geometry('loaded', base)  # no strip_loss_eq
    g_lossy = geo.make_geometry('loaded', {**base, 'strip_loss_eq': CONST_EQ})

    x = np.linspace(-1200, 1200, 241)
    y = np.linspace(900, 1500, 61)  # spans substrate_height=1000 up through the strip

    assert g_lossless.lossy_mask(x, y) is None
    assert g_lossless.lossy_bulk_loss_dB_per_m(225.0) == 0.0

    mask = g_lossy.lossy_mask(x, y)
    assert mask is not None and mask.any() and mask.shape == (len(y), len(x))
    # the mask should match _masks()'s own strip region exactly
    _, strip = g_lossy._masks(x, y)
    assert np.array_equal(mask, strip)

    loss = g_lossy.lossy_bulk_loss_dB_per_m(225.0)
    assert abs(loss - geo.material_loss_dB_per_m(0.5, 225.0)) < 1e-6 * loss
    print(f"loaded lossy_mask/lossy_bulk_loss_dB_per_m OK: strip area frac="
          f"{mask.mean():.3f}, bulk_loss(225nm)={loss:.3e} dB/m")


def test_region_masks_tile_the_cross_section():
    x = np.linspace(-1200, 1200, 241)
    y = np.linspace(0, 2200, 221)
    for fam, params in (('ridge', {'h_core': 350.0, 'w_core': 400.0}),
                        ('loaded', {'t_film': 354.0, 'etch_depth': 0.0, 'h_s': 70.0, 'w_s': 500.0})):
        g = geo.make_geometry(fam, params)
        regions = g.region_masks(x, y)
        total = sum(mask.astype(int) for mask, _ in regions.values())
        assert np.all(total == 1), (fam, 'regions overlap or leave gaps')
        assert regions['Substrate'][0][0, 0]  # bottom-left corner is substrate
        print(f"{fam} region_masks OK: {list(regions)} tile the cross-section with no gaps/overlaps")


def test_ridge_has_no_lossy_region():
    g = geo.make_geometry('ridge', {'h_core': 350.0, 'w_core': 400.0})
    x = np.linspace(-1000, 1000, 101)
    y = np.linspace(900, 1400, 51)
    assert g.lossy_mask(x, y) is None
    assert g.lossy_bulk_loss_dB_per_m(225.0) == 0.0
    print("ridge lossy defaults OK: no lossy region (AlN k not wired in yet)")


def test_tio2_fit_equation_sanity():
    """The actual TiO2 fit used by survey_config_loaded.py: SH band should be strongly
    absorbing (k of order 1), pump band should be nearly transparent (k << 1)."""
    import json
    import os
    with open(os.path.join(geo.HERE, 'materials', 'TiO2_Siefke2016_sellmeier_fit.json')) as f:
        eq = json.load(f)['emode_equation_complex']
    k_sh = geo.eval_complex_index_equation(eq, 225.0).imag
    k_pump = geo.eval_complex_index_equation(eq, 450.0).imag
    assert k_sh > 1.0, k_sh
    assert k_pump < 0.1, k_pump
    print(f"TiO2 fit sanity OK: k(225nm)={k_sh:.3f} (strongly absorbing), "
          f"k(450nm)={k_pump:.4f} (near-transparent)")


if __name__ == '__main__':
    test_eval_complex_index_equation()
    test_material_loss_matches_shg_physics()
    test_loaded_lossy_mask_and_loss()
    test_region_masks_tile_the_cross_section()
    test_ridge_has_no_lossy_region()
    test_tio2_fit_equation_sanity()
    print('all passed')
