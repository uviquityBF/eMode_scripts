"""Geometry families for the SHG survey: family name + params dict -> EMode shapes + the metadata
the physics needs (chi(2) map, absorption mask, Cerenkov regions, symmetry). See PLAN.md
"Geometry interface". Step 1 implements only `ridge` (the existing trapezoidal AlN ridge).
"""

import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'phase_matching_pipeline'))
sys.path.insert(0, os.path.join(HERE, '..', 'loss_vs_dimensions'))
import emode_helpers as pmh  # noqa: E402
from emode_export import build_core_mask_from_geometry  # noqa: E402

# AlN Sellmeier (ordinary / extraordinary), same as loss_vs_dimensions -- x in um.
AlN_EQ_O = ('(1+2.8032/(1-0.015287/x**2)+0.36335/(1-0.036095/x**2)'
            '-33508000/(1+367200000/x**2))**0.5')
AlN_EQ_E = ('(1+0.017061/(1-0.043855/x**2)+3.1976/(1-0.022642/x**2)'
            '-57269000/(1-74226000/x**2))**0.5')


def eval_index_equation(eq, wavelength_nm):
    x = wavelength_nm / 1000.0  # noqa: F841 -- used by eval
    return float(np.real(eval(eq, {'__builtins__': {}}, {'x': x})))


def eval_complex_index_equation(eq, wavelength_nm):
    """Like eval_index_equation but keeps the imaginary (k) part -- for Python-side loss
    bookkeeping only; EMode's FDM solver itself cannot consume a complex
    refractive_index_equation (crashes, confirmed EMode bug as of v1.0.5 -- see PLAN.md), so bulk
    material loss has to be computed here and fed in separately via shape(loss_dB_per_m=...)."""
    x = wavelength_nm / 1000.0  # noqa: F841 -- used by eval
    return complex(eval(eq, {'__builtins__': {}}, {'x': x}))


def material_loss_dB_per_m(k, wavelength_nm):
    """Bulk power-absorption loss [dB/m] from a material's own extinction coefficient k at this
    wavelength (not a modal/confinement-weighted value -- EMode's shape(loss_dB_per_m=...) applies
    the confinement weighting once this is fed in as the shape's bulk loss)."""
    k0 = 2 * np.pi / (wavelength_nm * 1e-9)
    alpha_per_m = 2 * k0 * max(float(k), 0.0)
    return alpha_per_m * 10.0 / np.log(10.0)


def _scalar_index(value):
    """em.refractive_index() may return a scalar or [n_x, n_y, n_z]; take the largest."""
    arr = np.real(np.atleast_1d(np.asarray(value, dtype=complex)))
    return float(arr.max())


class Ridge:
    """Trapezoidal AlN ridge (full etch) on a sapphire substrate, conformal SiO2 top clad --
    exactly emode_helpers.setup_waveguide's geometry. Params (nm / deg):
    h_core, w_core, sidewall_angle=5, substrate_height=1000, topclad_height=800.
    """
    family = 'ridge'
    symmetric_x = True
    defaults = {'sidewall_angle': 5.0, 'substrate_height': 1000.0, 'topclad_height': 800.0,
                'substrate_material': 'Al2O3', 'topclad_material': 'SiO2',
                'core_eq_o': AlN_EQ_O, 'core_eq_e': AlN_EQ_E, 'core_chi2': 'AlN'}

    def __init__(self, **params):
        self.params = {**self.defaults, **params}
        for k in ('h_core', 'w_core'):
            if k not in self.params:
                raise ValueError(f"ridge needs {k}")

    @property
    def window_width(self):
        return max(2000.0, self.params['w_core'] + 1600.0)

    def build(self, em, roughness_rms=(0.0, 0.0), correlation_length=(0.0, 0.0)):
        p = self.params
        aniso = f"[{p['core_eq_o']},{p['core_eq_e']},{p['core_eq_o']}]"
        pmh.setup_waveguide(em, aniso, p['h_core'], p['w_core'],
                            window_width=self.window_width, boundary_condition='0A',
                            substrate_material=p['substrate_material'],
                            substrate_height=p['substrate_height'],
                            topclad_material=p['topclad_material'],
                            topclad_height=p['topclad_height'],
                            sidewall_angle=p['sidewall_angle'])
        if any(roughness_rms):
            em.shape(name='core', roughness_rms=list(roughness_rms),
                     correlation_length=list(correlation_length))

    def core_mask(self, x, y):
        p = self.params
        # Core sits directly on the substrate at y = substrate_height (confirmed in the
        # loss_vs_dimensions pipeline via em.plot(component='Shapes')).
        return build_core_mask_from_geometry(x, y, p['h_core'], p['w_core'], p['sidewall_angle'],
                                             p['substrate_height'])

    def region_masks(self, x, y):
        """{name: (mask, material_label)} tiling the whole cross-section -- for plotting (e.g.
        plot_geometry.py), no EMode needed."""
        p = self.params
        xx, yy = np.meshgrid(np.asarray(x, float), np.asarray(y, float))
        core = self.core_mask(x, y)
        substrate = (yy < p['substrate_height']) & ~core
        topclad = (yy >= p['substrate_height']) & ~core
        return {'Substrate': (substrate, p['substrate_material']),
                'core': (core, 'AlN'),
                'TopClad': (topclad, p['topclad_material'])}

    def chi2_map(self, x, y, d_tensors_pm):
        """{'d33','d31','d15'} arrays [m/V], shape (ny, nx), nonzero only in chi(2) regions."""
        mask = self.core_mask(x, y).astype(float)
        t = d_tensors_pm[self.params['core_chi2']]
        d15 = t.get('d15', t['d31'])
        return {'d33': mask * t['d33'] * 1e-12, 'd31': mask * t['d31'] * 1e-12,
                'd15': mask * d15 * 1e-12}

    def eps_fn(self, wavelength_sh_nm, n_regions):
        """eps(X, Y, comp) at lambda_SH for the driven Cerenkov solve. `n_regions` maps
        'substrate' / 'topclad' to their index at lambda_SH (from EMode, stored with the pump
        export). The top clad is treated as semi-infinite (thick in the real device)."""
        p = self.params
        n_o = eval_index_equation(p['core_eq_o'], wavelength_sh_nm)
        n_e = eval_index_equation(p['core_eq_e'], wavelength_sh_nm)
        core_eps = {'Ex': n_o ** 2, 'Ey': n_e ** 2, 'Ez': n_o ** 2}

        def f(X, Y, comp):
            core = self.core_mask(X[0, :], Y[:, 0])
            sub = Y < p['substrate_height']
            return np.where(core, core_eps[comp],
                            np.where(sub, n_regions['substrate'] ** 2,
                                     n_regions['topclad'] ** 2)).astype(complex)
        return f

    def d_fn(self, d_tensors_pm):
        def f(X, Y):
            return self.chi2_map(X[0, :], Y[:, 0], d_tensors_pm)
        return f

    def bbox(self):
        """(x0, x1, y0, y1) [nm] of the core in EMode grid coordinates."""
        p = self.params
        return (-p['w_core'] / 2, p['w_core'] / 2, p['substrate_height'],
                p['substrate_height'] + p['h_core'])

    def cerenkov_regions(self, em, wavelength_sh_nm):
        """Regions SH could radiate into, with their index at lambda_SH and bulk/finite extent.
        Substrate and top clad are treated as bulk (thick in the real device)."""
        p = self.params
        out = []
        for name, mat in (('substrate', p['substrate_material']), ('topclad', p['topclad_material'])):
            n = _scalar_index(em.refractive_index(material=mat, wavelength=wavelength_sh_nm))
            out.append({'name': f"{name}:{mat}", 'n': n, 'extent': 'bulk'})
        return out

    def describe(self):
        p = self.params
        return f"ridge h={p['h_core']:g} w={p['w_core']:g} sw={p['sidewall_angle']:g}"


def _trapezoid(xx, yy, y0, height, w_bottom, sidewall_angle, x_center=0.0):
    """Trapezoid mask: bottom width w_bottom at y0, narrowing upward by sidewall_angle."""
    above = yy - y0
    inside = (above >= 0) & (above <= height)
    half = w_bottom / 2 - np.clip(above, 0, height) * np.tan(np.radians(sidewall_angle))
    return inside & (np.abs(xx - x_center) <= half)


class Loaded:
    """Loaded / rib-loaded / hybrid AlN guide (John Carlson deck, 2026-09, slides 10-15):

        strip (strip_material, h_s, w_s, strip_sidewall, strip_offset)
        AlN film of thickness t_film, etched to etch_depth outside a rib of width w_rib
        sapphire substrate, conformal SiO2 top clad

    etch_depth = 0 -> pure loaded (unetched AlN, e.g. Zetian Mi / John's proposal);
    etch_depth = t_film -> strip on a full AlN ridge; in between -> etched rib-loaded (FBH).
    strip_material: an EMode database name (e.g. 'TiO2'), or set strip_eq (isotropic index
    equation in um) to add it as a custom material -- strip_eq must be REAL-only (a complex
    refractive_index_equation crashes em.FDM() outright, confirmed EMode bug as of v1.0.5). For a
    lossy strip, also set strip_loss_eq (a separate, complex n+ik equation, same string format as
    strip_eq); survey.py applies its bulk loss as a post-solve perturbation (lossy_mask() +
    lossy_bulk_loss_dB_per_m(), see their docstrings) rather than feeding it into EMode and
    re-solving -- re-solving with TiO2's large SH-band loss was found to corrupt SH-mode
    re-identification. strip_chi2: key into d_tensors_pm if the strip is nonlinear (AlGaN/ScAlN),
    else None.

    UNVERIFIED (check with em.plot(component='Index') once): EMode's mask/etch_depth convention
    for a partial etch (mask = unetched rib width, slab = t_film - etch_depth outside) and that
    mask_offset shifts the strip laterally -- same conventions as the ridge, but not yet
    confirmed for these two cases.
    """
    family = 'loaded'
    defaults = {'etch_depth': 0.0, 'w_rib': None, 'sidewall_angle': 5.0,
                'strip_material': 'TiO2', 'strip_eq': None, 'strip_loss_eq': None,
                'strip_chi2': None, 'strip_sidewall': 5.0, 'strip_offset': 0.0,
                'substrate_height': 1000.0, 'topclad_height': 800.0,
                'substrate_material': 'Al2O3', 'topclad_material': 'SiO2',
                'core_eq_o': AlN_EQ_O, 'core_eq_e': AlN_EQ_E, 'core_chi2': 'AlN'}

    def __init__(self, **params):
        self.params = {**self.defaults, **params}
        for k in ('t_film', 'h_s', 'w_s'):
            if k not in self.params:
                raise ValueError(f"loaded needs {k}")
        if self.params['w_rib'] is None:
            self.params['w_rib'] = self.params['w_s']

    @property
    def symmetric_x(self):
        return abs(self.params['strip_offset']) < 1e-9

    @property
    def window_width(self):
        p = self.params
        return max(2400.0, max(p['w_s'], p['w_rib']) + 2 * abs(p['strip_offset']) + 2000.0)

    @property
    def scatter_shapes(self):
        """Shapes with etched sidewalls (for EMode-native roughness scattering)."""
        return ['strip'] + (['film'] if self.params['etch_depth'] > 0 else [])

    def _strip_material_name(self):
        return 'custom_strip' if self.params['strip_eq'] else self.params['strip_material']

    def build(self, em, roughness_rms=(0.0, 0.0), correlation_length=(0.0, 0.0)):
        p = self.params
        aniso = f"[{p['core_eq_o']},{p['core_eq_e']},{p['core_eq_o']}]"
        em.add_material(name='custom_AlN', refractive_index_equation=aniso, wavelength_unit='um')
        if p['strip_eq']:
            em.add_material(name='custom_strip', refractive_index_equation=p['strip_eq'],
                            wavelength_unit='um')
        total = p['t_film'] + p['h_s']
        em.settings(window_width=self.window_width, window_height=total + 2000.0,
                    boundary_condition='0A')
        em.shape(name='Substrate', material=p['substrate_material'], height=p['substrate_height'])
        rough = ({'roughness_rms': list(roughness_rms), 'correlation_length': list(correlation_length)}
                 if any(roughness_rms) else {})
        em.shape(name='film', material='custom_AlN', height=p['t_film'], mask=p['w_rib'],
                 etch_depth=p['etch_depth'], sidewall_angle=p['sidewall_angle'],
                 **(rough if p['etch_depth'] > 0 else {}))
        em.shape(name='strip', material=self._strip_material_name(), height=p['h_s'],
                 mask=p['w_s'], mask_offset=p['strip_offset'], etch_depth=p['h_s'],
                 sidewall_angle=p['strip_sidewall'], **rough)
        em.shape(name='TopClad', material=p['topclad_material'], height=p['topclad_height'],
                 shape_type='conformal')

    def lossy_mask(self, x, y):
        """The strip mask, for confinement-weighted bulk absorption -- None if strip_loss_eq
        isn't set (lossless strip, e.g. plain n only, or a non-absorbing strip material).

        NOTE: bulk loss is applied as a pure post-solve perturbation (survey.py computes
        Gamma = fraction of the ALREADY-SOLVED lossless mode's power in this mask, times
        lossy_bulk_loss_dB_per_m()) rather than by feeding shape(loss_dB_per_m=...) into EMode
        and re-solving. An earlier version did the latter and it corrupted SH-mode
        re-identification at refine time: TiO2's SH-band loss is so large (alpha ~3e8 dB/m) that
        re-solving with it set shifts the solver's returned candidate modes enough that the
        argmax-similarity match picks a genuinely different mode (confirmed 2026-10-04: overlap_
        shape for nominally the same crossing dropped from 0.051 to 0.0036, SH label changed
        TM165? -> TM183). Perturbation theory (first-order, valid since TiO2 is a thin
        low-confinement region for every mode seen so far) sidesteps that entirely and is also
        cheaper -- no extra EMode solve at all.
        """
        return self._masks(x, y)[1] if self.params['strip_loss_eq'] else None

    def lossy_bulk_loss_dB_per_m(self, wavelength_nm):
        """The strip material's own bulk absorption [dB/m] at this wavelength (not yet
        confinement-weighted -- multiply by the mode's power fraction in lossy_mask()). 0.0 if
        strip_loss_eq isn't set."""
        p = self.params
        if not p['strip_loss_eq']:
            return 0.0
        k = eval_complex_index_equation(p['strip_loss_eq'], wavelength_nm).imag
        return material_loss_dB_per_m(k, wavelength_nm)

    def _masks(self, x, y):
        p = self.params
        xx, yy = np.meshgrid(np.asarray(x, float), np.asarray(y, float))
        y_sub = p['substrate_height']
        slab = p['t_film'] - p['etch_depth']
        film = ((yy >= y_sub) & (yy <= y_sub + slab)) | _trapezoid(
            xx, yy, y_sub + slab, p['etch_depth'], p['w_rib'], p['sidewall_angle'])
        strip = _trapezoid(xx, yy, y_sub + p['t_film'], p['h_s'], p['w_s'], p['strip_sidewall'],
                           p['strip_offset'])
        return film, strip

    def core_mask(self, x, y):
        """The AlN film (the growth-interface / chi(2) reference region)."""
        return self._masks(x, y)[0]

    def region_masks(self, x, y):
        """{name: (mask, material_label)} tiling the whole cross-section -- for plotting (e.g.
        plot_geometry.py), no EMode needed."""
        p = self.params
        xx, yy = np.meshgrid(np.asarray(x, float), np.asarray(y, float))
        film, strip = self._masks(x, y)
        substrate = (yy < p['substrate_height']) & ~film & ~strip
        topclad = (yy >= p['substrate_height']) & ~film & ~strip
        return {'Substrate': (substrate, p['substrate_material']),
                'film': (film, 'AlN'),
                'strip': (strip, self._strip_material_name()),
                'TopClad': (topclad, p['topclad_material'])}

    def chi2_map(self, x, y, d_tensors_pm):
        film, strip = self._masks(x, y)
        out = {k: np.zeros(film.shape) for k in ('d33', 'd31', 'd15')}
        for mask, key in ((film, self.params['core_chi2']), (strip, self.params['strip_chi2'])):
            if key:
                t = d_tensors_pm[key]
                for k, v in (('d33', t['d33']), ('d31', t['d31']), ('d15', t.get('d15', t['d31']))):
                    out[k] = out[k] + mask * v * 1e-12
        return out

    def _strip_n(self, em, wavelength_nm):
        if self.params['strip_eq']:
            return eval_index_equation(self.params['strip_eq'], wavelength_nm)
        return _scalar_index(em.refractive_index(material=self.params['strip_material'],
                                                 wavelength=wavelength_nm))

    def cerenkov_regions(self, em, wavelength_sh_nm):
        p = self.params
        out = []
        for name, mat in (('substrate', p['substrate_material']), ('topclad', p['topclad_material'])):
            n = _scalar_index(em.refractive_index(material=mat, wavelength=wavelength_sh_nm))
            out.append({'name': f"{name}:{mat}", 'n': n, 'extent': 'bulk'})
        if p['etch_depth'] < p['t_film']:  # laterally extended AlN slab: SH can couple into it
            out.append({'name': 'slab:AlN', 'extent': 'finite',
                        'n': eval_index_equation(p['core_eq_e'], wavelength_sh_nm)})
        return out

    def eps_fn(self, wavelength_sh_nm, n_regions):
        p = self.params
        n_o = eval_index_equation(p['core_eq_o'], wavelength_sh_nm)
        n_e = eval_index_equation(p['core_eq_e'], wavelength_sh_nm)
        core_eps = {'Ex': n_o ** 2, 'Ey': n_e ** 2, 'Ez': n_o ** 2}
        n_strip = n_regions['strip']

        def f(X, Y, comp):
            film, strip = self._masks(X[0, :], Y[:, 0])
            sub = Y < p['substrate_height']
            return np.where(film, core_eps[comp], np.where(strip, n_strip ** 2, np.where(
                sub, n_regions['substrate'] ** 2, n_regions['topclad'] ** 2))).astype(complex)
        return f

    def d_fn(self, d_tensors_pm):
        def f(X, Y):
            return self.chi2_map(X[0, :], Y[:, 0], d_tensors_pm)
        return f

    def bbox(self):
        p = self.params
        w = max(p['w_s'], p['w_rib']) + 2 * abs(p['strip_offset'])
        return (-w / 2, w / 2, p['substrate_height'],
                p['substrate_height'] + p['t_film'] + p['h_s'])

    def export_regions(self, em, wavelength_sh_nm):
        """Indices stored with pump exports for the Cerenkov solve."""
        return {'strip': self._strip_n(em, wavelength_sh_nm)}

    def describe(self):
        p = self.params
        return (f"loaded t={p['t_film']:g} e={p['etch_depth']:g} {p['strip_material'] if not p['strip_eq'] else 'custom'}"
                f" h_s={p['h_s']:g} w_s={p['w_s']:g}" + (f" off={p['strip_offset']:g}" if p['strip_offset'] else ''))


Ridge.symmetric_x = True
Ridge.scatter_shapes = ['core']
Ridge.export_regions = lambda self, em, lam: {}
Ridge.lossy_mask = lambda self, x, y: None  # no lossy shape in this family yet
Ridge.lossy_bulk_loss_dB_per_m = lambda self, wavelength_nm: 0.0

FAMILIES = {'ridge': Ridge, 'loaded': Loaded}


def make_geometry(family, params):
    return FAMILIES[family](**params)


def fingerprint(geom, survey_settings, d_tensors_pm, version='step1-v1'):
    """Stable hash of everything that determines a geometry's results."""
    blob = json.dumps({'family': geom.family, 'params': geom.params, 'settings': survey_settings,
                       'd': d_tensors_pm, 'version': version}, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]
