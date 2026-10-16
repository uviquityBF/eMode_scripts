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


# AlN's own intrinsic bulk absorption, previously assumed lossless everywhere. Extraordinary-axis
# k_e only (not k_o) -- the axis d33 couples (Py = d33*Ey^2) and the larger of the two measured
# values, so this is the conservative/dominant choice for the TM-polarized modes this survey
# studies, not a field-direction-resolved split; see PLAN.md's 2026-10-12 "AlN anisotropy model"
# decision. 3-Lorentzian fit to AM187-LT6 measured k_e (x in um) -- see
# materials/fit_aln_measured_k.py -> materials/AlN_AM187_LT6_k_fit.json's k_equation_e.
AlN_K_E_EQ = ('(0.450766/(1+((x-0.198721)/0.00610201)**2)'
              '+0.0336577/(1+((x-0.233588)/0.00800000)**2)'
              '+0.0152550/(1+((x-0.387876)/0.122966)**2))')


def aln_core_loss_dB_per_m(wavelength_nm):
    """AlN's own intrinsic bulk absorption [dB/m] at this wavelength, from AlN_K_E_EQ above. Not
    confinement-weighted -- multiply by the mode's power fraction in geom.core_mask() (see
    survey.py's bulk_absorption_loss / reprocess_run.py, same pattern as the shell/strip
    lossy_bulk_loss_dB_per_m methods below)."""
    return material_loss_dB_per_m(eval_index_equation(AlN_K_E_EQ, wavelength_nm), wavelength_nm)


def k_from_loss_dB_per_m(loss_dB_per_m, wavelength_nm):
    """Inverse of material_loss_dB_per_m -- the extinction coefficient k a bulk material would
    need to produce this [dB/m] power loss at this wavelength. Reporting/plotting use only (e.g.
    showing SH_ABSORPTION_CALIBRATED_DB_PER_CM on the same k axis as measured ellipsometry data in
    build_assumptions_report.py) -- the simulation itself works in dB/m throughout, never needs
    this converted back to k."""
    k0 = 2 * np.pi / (wavelength_nm * 1e-9)
    alpha_per_m = loss_dB_per_m * np.log(10.0) / 10.0
    return alpha_per_m / (2 * k0)


# Empirically-calibrated flat SH-band bulk absorption -- NOT from ellipsometry. AM187-LT6's
# measured k_e implies ~100,000 dB/cm of SH-band AlN absorption for a representative crossing
# (ridge h=350 w=500nm, TM00->TM04 -- the closest match in this project's dataset to real
# fabricated/tested devices), but inverting this project's own loss-limited-efficiency model
# (shg_physics.loss_limited_length) against REAL measured SH output (a fabricated device's ~200nW
# best case / ~20nW typical floor, at 100mW pump power and a real 2mm interaction length, 10-50%
# input-coupling efficiency unknown) bounds the actual SH loss to roughly 15-680 dB/cm depending
# on the (unmeasured) coupling efficiency -- 3-4 orders of magnitude below the AM187 number. See
# PLAN.md's 2026-10-12 "empirical SH-loss bound" entries for the full derivation.
#
# 100 dB/cm is the team's chosen round-number working value within that empirically-bounded
# range (2026-10-12 decision) -- not a measurement of any specific physical mechanism, just a
# placeholder pending either better coupling-efficiency data or new loss-specific measurements
# (e.g. a cutback measurement on real device material). Confinement-weighted by geom.core_mask()
# exactly like aln_core_loss_dB_per_m above (same reasoning: treat it as if it were a bulk
# material property, even though its physical origin -- absorption, additional scattering not
# captured by the native roughness model, or something else -- is genuinely unknown). Applies
# ONLY to the SH band (215-235nm) -- never to pump -- since it was back-calculated purely from
# SH output; see survey.py's bulk_absorption_loss for the SH-only gate.
SH_ABSORPTION_CALIBRATED_DB_PER_CM = 100.0


def sh_absorption_calibrated_dB_per_m(wavelength_nm):
    """SH_ABSORPTION_CALIBRATED_DB_PER_CM converted to dB/m -- flat (wavelength-independent) by
    construction, since it's a single round-number working value, not a fitted spectral shape."""
    return SH_ABSORPTION_CALIBRATED_DB_PER_CM * 100.0


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

    NO-STRIP MODE (added 2026-10-14, study plan row 1.2): omit h_s/w_s (or pass h_s=0) for a bare
    partially-etched rib with no loading strip at all -- the B=0 edge case of this topology, w_rib
    becomes REQUIRED in this mode (there's no w_s to fall back to). `has_strip` is False and every
    method that touches the strip (build, _masks, chi2_map, eps_fn, region_masks, bbox, describe)
    degrades to a harmless no-op for it rather than erroring on a zero-height EMode shape (an
    untested path EMode itself has never been asked to handle, unlike this class's existing
    etch_depth convention, which at least has real runs behind it).
    """
    family = 'loaded'
    defaults = {'etch_depth': 0.0, 'w_rib': None, 'sidewall_angle': 5.0,
                'strip_material': 'TiO2', 'strip_eq': None, 'strip_loss_eq': None,
                'strip_chi2': None, 'strip_sidewall': 5.0, 'strip_offset': 0.0,
                'h_s': 0.0, 'w_s': 0.0,
                'substrate_height': 1000.0, 'topclad_height': 800.0,
                'substrate_material': 'Al2O3', 'topclad_material': 'SiO2',
                'core_eq_o': AlN_EQ_O, 'core_eq_e': AlN_EQ_E, 'core_chi2': 'AlN'}

    def __init__(self, **params):
        self.params = {**self.defaults, **params}
        if 't_film' not in self.params:
            raise ValueError("loaded needs t_film")
        if self.params['w_rib'] is None:
            if self.params['h_s'] <= 0:
                raise ValueError("loaded needs w_rib when h_s <= 0 (no strip width to fall back to)")
            self.params['w_rib'] = self.params['w_s']

    @property
    def has_strip(self):
        return self.params['h_s'] > 0

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
        return (['strip'] if self.has_strip else []) + (['film'] if self.params['etch_depth'] > 0 else [])

    def _strip_material_name(self):
        return 'custom_strip' if self.params['strip_eq'] else self.params['strip_material']

    def build(self, em, roughness_rms=(0.0, 0.0), correlation_length=(0.0, 0.0)):
        p = self.params
        aniso = f"[{p['core_eq_o']},{p['core_eq_e']},{p['core_eq_o']}]"
        em.add_material(name='custom_AlN', refractive_index_equation=aniso, wavelength_unit='um')
        if self.has_strip and p['strip_eq']:
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
        if self.has_strip:
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
        if self.has_strip:
            strip = _trapezoid(xx, yy, y_sub + p['t_film'], p['h_s'], p['w_s'], p['strip_sidewall'],
                               p['strip_offset'])
        else:
            strip = np.zeros_like(film, dtype=bool)
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
        if not self.has_strip:
            return f"loaded(no-strip) t={p['t_film']:g} e={p['etch_depth']:g} w_rib={p['w_rib']:g}"
        return (f"loaded t={p['t_film']:g} e={p['etch_depth']:g} {p['strip_material'] if not p['strip_eq'] else 'custom'}"
                f" h_s={p['h_s']:g} w_s={p['w_s']:g}" + (f" off={p['strip_offset']:g}" if p['strip_offset'] else ''))


Ridge.symmetric_x = True
Ridge.scatter_shapes = ['core']
Ridge.export_regions = lambda self, em, lam: {}
Ridge.lossy_mask = lambda self, x, y: None  # no lossy shape in this family yet
Ridge.lossy_bulk_loss_dB_per_m = lambda self, wavelength_nm: 0.0


class Hybrid:
    """AlN/SiNx hybrid waveguide (Honda et al., "Second harmonic generation in horizontally
    aligned AlN/SiNx hybrid waveguide for integrated wavelength converter," Appl. Phys. Express
    18, 122001 (2025)): a trapezoidal AlN core (full etch, same shape convention as `Ridge`)
    embedded within a wider, taller SiNx "shell" block, on sapphire, SiO2 top clad. The paper
    demonstrates TM00->TM20 phase matching at telecom wavelengths (1550/775 nm) by positioning
    the AlN specifically where TM20's transverse E-field keeps one sign (between its two interior
    nodes), avoiding the overlap cancellation that normally kills a TM00->TM02/TM20 match in a
    plain ridge (see PLAN.md: "No TM02/TM20 SH partner phase-matches anywhere in 215-235 nm" for
    `ridge` -- this family exists to re-attempt that in the project's actual UV band, not to
    reproduce the paper's telecom demo).

    The paper describes fabrication narratively (conformal SiNx deposition, RIE side-core etch,
    CMP planarization), not as a simple target cross-section. This models the simplest
    mode-solver-natural reading of it: an AlN trapezoid sitting on the substrate, embedded in a
    SiNx rectangle of width `sin_width` x height `sin_height` that also sits on the substrate (so
    SiNx occupies every point inside that bounding box NOT already AlN -- beside AND above the
    core), then SiO2 outside/above. Confirmed 2026-10-05 via em.plot(component='Index') on the
    smoke geometry: EMode's render matches `_masks` exactly (core trapezoid embedded in the shell
    rectangle, nothing defaulting to full window width -- see `build`'s etch_depth comment for the
    convention that makes this work).

    Params (nm / deg), all but the materials/chi2 keys required (no natural default for a new
    engineered structure -- the paper's own telecom-scale values are a starting point, not
    necessarily right for this project's UV band): h_core, w_core (AlN trapezoid bottom width),
    sidewall_angle=16.5 (~paper's implied angle from its reported top/bottom/height), sin_width,
    sin_height (SiNx shell outer bounding box -- must be >= h_core/w_core respectively).
    shell_material: an EMode database name (default 'SiN' -- confirmed present in EMode's
    database; 'SiNx'/'Si3N4' are not), or set shell_eq (REAL-only -- see `Loaded`'s
    strip_eq/strip_loss_eq docstring for why) + shell_loss_eq (complex, Python-only) for a custom
    lossy material the same way. shell_chi2: key into d_tensors_pm if the shell is nonlinear,
    else None (SiNx is amorphous/centrosymmetric -- chi(2) = 0 is the physically-expected default,
    matching the paper, which uses only AlN's d33).
    """
    family = 'hybrid'
    defaults = {'sidewall_angle': 16.5, 'shell_material': 'SiN', 'shell_eq': None,
                'shell_loss_eq': None, 'shell_chi2': None,
                'substrate_height': 1000.0, 'topclad_height': 800.0,
                'substrate_material': 'Al2O3', 'topclad_material': 'SiO2',
                'core_eq_o': AlN_EQ_O, 'core_eq_e': AlN_EQ_E, 'core_chi2': 'AlN'}

    def __init__(self, **params):
        self.params = {**self.defaults, **params}
        for k in ('h_core', 'w_core', 'sin_width', 'sin_height'):
            if k not in self.params:
                raise ValueError(f"hybrid needs {k}")
        if self.params['sin_width'] < self.params['w_core'] or self.params['sin_height'] < self.params['h_core']:
            raise ValueError("hybrid: sin_width/sin_height must be >= w_core/h_core (the SiNx "
                             "shell has to be at least as large as the AlN core it contains)")

    @property
    def symmetric_x(self):
        return True  # both the AlN core and the SiNx shell are x-centered rectangles/trapezoids

    @property
    def window_width(self):
        return max(2000.0, self.params['sin_width'] + 1600.0)

    @property
    def scatter_shapes(self):
        return ['core', 'shell']

    def _shell_material_name(self):
        return 'custom_shell' if self.params['shell_eq'] else self.params['shell_material']

    def build(self, em, roughness_rms=(0.0, 0.0), correlation_length=(0.0, 0.0)):
        p = self.params
        aniso = f"[{p['core_eq_o']},{p['core_eq_e']},{p['core_eq_o']}]"
        em.add_material(name='custom_AlN', refractive_index_equation=aniso, wavelength_unit='um')
        if p['shell_eq']:
            em.add_material(name='custom_shell', refractive_index_equation=p['shell_eq'],
                            wavelength_unit='um')
        em.settings(window_width=self.window_width, window_height=p['sin_height'] + 2000.0,
                    boundary_condition='0A')
        em.shape(name='Substrate', material=p['substrate_material'], height=p['substrate_height'])
        rough = ({'roughness_rms': list(roughness_rms), 'correlation_length': list(correlation_length)}
                 if any(roughness_rms) else {})
        # shell: a rectangular block. etch_depth == height (same convention Loaded's 'strip'
        # uses) is required for mask to actually restrict the width at all -- without it, mask
        # alone is a no-op and the shape fills the full window (found 2026-10-05 via
        # em.plot(component='Index') rendering a full-width flat layer instead of a block).
        em.shape(name='shell', material=self._shell_material_name(), height=p['sin_height'],
                 mask=p['sin_width'], etch_depth=p['sin_height'], sidewall_angle=0.0, **rough)
        # core: drawn after the shell, so it takes priority in their overlapping footprint
        # (same "later shape wins" convention already relied on by Loaded's film-then-strip).
        # position=(x, y) is REQUIRED and y is CENTER-referenced -- shape()'s default position is
        # (0, 'auto'), which auto-stacks a shape on top of whatever's already there within its own
        # mask width (real-fab-style sequential deposition); without it, 'core' silently stacked on
        # TOP of the already-drawn 'shell' instead of embedding laterally within it. Confirmed
        # 2026-10-10 via em.plot(component='Index') + a controlled position sweep: position=(0,
        # substrate_height) (tried first, assuming bottom-referenced like the implicit stacking
        # default) centered the core on substrate_height instead, straddling into the substrate;
        # substrate_height + h_core/2 is what actually lands the core's bottom edge at
        # substrate_height, matching _masks()'s convention and the Honda et al. mechanism (AlN
        # surrounded by SiNx on the sides and above, not stacked on top of it). This bug silently
        # affected every 'hybrid' geometry run before this fix -- see PLAN.md.
        em.shape(name='core', material='custom_AlN', height=p['h_core'], mask=p['w_core'],
                 position=(0, p['substrate_height'] + p['h_core'] / 2),
                 etch_depth=p['h_core'], sidewall_angle=p['sidewall_angle'], **rough)
        em.shape(name='TopClad', material=p['topclad_material'], height=p['topclad_height'],
                 shape_type='conformal')

    def _masks(self, x, y):
        p = self.params
        xx, yy = np.meshgrid(np.asarray(x, float), np.asarray(y, float))
        y_sub = p['substrate_height']
        shell_box = (yy >= y_sub) & (yy <= y_sub + p['sin_height']) & (np.abs(xx) <= p['sin_width'] / 2)
        core = _trapezoid(xx, yy, y_sub, p['h_core'], p['w_core'], p['sidewall_angle'])
        shell = shell_box & ~core
        return core, shell

    def core_mask(self, x, y):
        """The AlN core (the chi(2) reference region)."""
        return self._masks(x, y)[0]

    def region_masks(self, x, y):
        """{name: (mask, material_label)} tiling the whole cross-section -- for plotting (e.g.
        plot_geometry.py), no EMode needed."""
        p = self.params
        xx, yy = np.meshgrid(np.asarray(x, float), np.asarray(y, float))
        core, shell = self._masks(x, y)
        substrate = (yy < p['substrate_height']) & ~core & ~shell
        topclad = (yy >= p['substrate_height']) & ~core & ~shell
        return {'Substrate': (substrate, p['substrate_material']),
                'core': (core, 'AlN'),
                'shell': (shell, self._shell_material_name()),
                'TopClad': (topclad, p['topclad_material'])}

    def lossy_mask(self, x, y):
        """The shell mask, for confinement-weighted bulk absorption -- see `Loaded.lossy_mask`'s
        docstring for why this is a post-solve perturbation (survey.bulk_absorption_loss), not an
        EMode re-solve. None if shell_loss_eq isn't set."""
        return self._masks(x, y)[1] if self.params['shell_loss_eq'] else None

    def lossy_bulk_loss_dB_per_m(self, wavelength_nm):
        p = self.params
        if not p['shell_loss_eq']:
            return 0.0
        k = eval_complex_index_equation(p['shell_loss_eq'], wavelength_nm).imag
        return material_loss_dB_per_m(k, wavelength_nm)

    def chi2_map(self, x, y, d_tensors_pm):
        core, shell = self._masks(x, y)
        out = {k: np.zeros(core.shape) for k in ('d33', 'd31', 'd15')}
        for mask, key in ((core, self.params['core_chi2']), (shell, self.params['shell_chi2'])):
            if key:
                t = d_tensors_pm[key]
                for k, v in (('d33', t['d33']), ('d31', t['d31']), ('d15', t.get('d15', t['d31']))):
                    out[k] = out[k] + mask * v * 1e-12
        return out

    def _shell_n(self, em, wavelength_nm):
        if self.params['shell_eq']:
            return eval_index_equation(self.params['shell_eq'], wavelength_nm)
        return _scalar_index(em.refractive_index(material=self.params['shell_material'],
                                                 wavelength=wavelength_nm))

    def cerenkov_regions(self, em, wavelength_sh_nm):
        p = self.params
        out = []
        for name, mat in (('substrate', p['substrate_material']), ('topclad', p['topclad_material'])):
            n = _scalar_index(em.refractive_index(material=mat, wavelength=wavelength_sh_nm))
            out.append({'name': f"{name}:{mat}", 'n': n, 'extent': 'bulk'})
        # the shell is finite (bounded by sin_width/sin_height, not laterally extended like
        # Loaded's unetched AlN slab), so it doesn't get its own bulk-radiation entry here.
        return out

    def eps_fn(self, wavelength_sh_nm, n_regions):
        p = self.params
        n_o = eval_index_equation(p['core_eq_o'], wavelength_sh_nm)
        n_e = eval_index_equation(p['core_eq_e'], wavelength_sh_nm)
        core_eps = {'Ex': n_o ** 2, 'Ey': n_e ** 2, 'Ez': n_o ** 2}
        n_shell = n_regions['shell']

        def f(X, Y, comp):
            core, shell = self._masks(X[0, :], Y[:, 0])
            sub = Y < p['substrate_height']
            return np.where(core, core_eps[comp], np.where(shell, n_shell ** 2, np.where(
                sub, n_regions['substrate'] ** 2, n_regions['topclad'] ** 2))).astype(complex)
        return f

    def d_fn(self, d_tensors_pm):
        def f(X, Y):
            return self.chi2_map(X[0, :], Y[:, 0], d_tensors_pm)
        return f

    def bbox(self):
        p = self.params
        return (-p['sin_width'] / 2, p['sin_width'] / 2, p['substrate_height'],
                p['substrate_height'] + p['sin_height'])

    def export_regions(self, em, wavelength_sh_nm):
        """Indices stored with pump exports for the Cerenkov solve."""
        return {'shell': self._shell_n(em, wavelength_sh_nm)}

    def describe(self):
        p = self.params
        return (f"hybrid h={p['h_core']:g} w={p['w_core']:g} "
                f"{p['shell_material'] if not p['shell_eq'] else 'custom'} "
                f"sin_w={p['sin_width']:g} sin_h={p['sin_height']:g}")


class Pedestal(Hybrid):
    """AlN ridge stacked on TOP of an SiNx rib/pedestal -- NOT embedded within it. This is the
    structure every 'hybrid' sweep actually built and solved before 2026-10-10's position fix
    (see PLAN.md): `em.shape()`'s `position` defaults to `(0, 'auto')`, which auto-stacks a new
    shape on top of whatever already occupies its mask footprint (real-fab-style sequential
    deposition); `Hybrid.build()`'s 'core' shape() call never set an explicit `position` until the
    fix, so it silently stacked on top of the already-drawn 'shell' instead of embedding laterally
    within it as intended. Renamed and kept as its own family rather than discarded or overwritten
    -- it's a real, different waveguide (an AlN strip loaded on an etched SiNx rib, closer in
    spirit to `Loaded` than to the embedded `Hybrid`, but using a finite rib instead of an unetched
    film and AlN instead of TiO2 as the loading strip) and its already-computed results remain
    valid *for this structure*, even though they don't test the Honda et al. TM00->TM20 mechanism
    `Hybrid` exists for. Archived runs: `pedestal1`, `pedestal_sweep1`, `pedestal_vertical1`
    (renamed from `hybrid1`/`hybrid_sweep1`/`hybrid_vertical1`).

    Only the geometry placement differs from `Hybrid` (`_masks`, `build`, `bbox`, `describe`) --
    every other method (loss, chi(2), Cerenkov, export) is inherited unchanged since they all key
    off `_masks()`/`bbox()` polymorphically.
    """
    family = 'pedestal'

    def build(self, em, roughness_rms=(0.0, 0.0), correlation_length=(0.0, 0.0)):
        p = self.params
        aniso = f"[{p['core_eq_o']},{p['core_eq_e']},{p['core_eq_o']}]"
        em.add_material(name='custom_AlN', refractive_index_equation=aniso, wavelength_unit='um')
        if p['shell_eq']:
            em.add_material(name='custom_shell', refractive_index_equation=p['shell_eq'],
                            wavelength_unit='um')
        em.settings(window_width=self.window_width, window_height=p['sin_height'] + 2000.0,
                    boundary_condition='0A')
        em.shape(name='Substrate', material=p['substrate_material'], height=p['substrate_height'])
        rough = ({'roughness_rms': list(roughness_rms), 'correlation_length': list(correlation_length)}
                 if any(roughness_rms) else {})
        em.shape(name='shell', material=self._shell_material_name(), height=p['sin_height'],
                 mask=p['sin_width'], etch_depth=p['sin_height'], sidewall_angle=0.0, **rough)
        # No explicit `position` -- this is the (original, unfixed) auto-stacking behavior that
        # defines this family: 'core' lands on top of 'shell' within its own mask width.
        em.shape(name='core', material='custom_AlN', height=p['h_core'], mask=p['w_core'],
                 etch_depth=p['h_core'], sidewall_angle=p['sidewall_angle'], **rough)
        em.shape(name='TopClad', material=p['topclad_material'], height=p['topclad_height'],
                 shape_type='conformal')

    def _masks(self, x, y):
        p = self.params
        xx, yy = np.meshgrid(np.asarray(x, float), np.asarray(y, float))
        y_sub = p['substrate_height']
        shell_box = (yy >= y_sub) & (yy <= y_sub + p['sin_height']) & (np.abs(xx) <= p['sin_width'] / 2)
        core = _trapezoid(xx, yy, y_sub + p['sin_height'], p['h_core'], p['w_core'], p['sidewall_angle'])
        # shell_box's top (yy <= y_sub+sin_height) and core's bottom (yy >= y_sub+sin_height) are
        # both inclusive at that exact shared boundary line -- `& ~core` (same defensive pattern
        # Hybrid's _masks uses) avoids double-counting it, same as Hybrid needs even though the two
        # aren't supposed to overlap "by construction" in either class.
        return core, shell_box & ~core

    def bbox(self):
        p = self.params
        return (-p['sin_width'] / 2, p['sin_width'] / 2, p['substrate_height'],
                p['substrate_height'] + p['sin_height'] + p['h_core'])

    def describe(self):
        p = self.params
        return (f"pedestal h={p['h_core']:g} w={p['w_core']:g} "
                f"{p['shell_material'] if not p['shell_eq'] else 'custom'} "
                f"sin_w={p['sin_width']:g} sin_h={p['sin_height']:g}")


FAMILIES = {'ridge': Ridge, 'loaded': Loaded, 'hybrid': Hybrid, 'pedestal': Pedestal}


def make_geometry(family, params):
    return FAMILIES[family](**params)


def fingerprint(geom, survey_settings, d_tensors_pm, version='step1-v1'):
    """Stable hash of everything that determines a geometry's results."""
    blob = json.dumps({'family': geom.family, 'params': geom.params, 'settings': survey_settings,
                       'd': d_tensors_pm, 'version': version}, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]
