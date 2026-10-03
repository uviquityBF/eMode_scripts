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


FAMILIES = {'ridge': Ridge}


def make_geometry(family, params):
    return FAMILIES[family](**params)


def fingerprint(geom, survey_settings, d_tensors_pm, version='step1-v1'):
    """Stable hash of everything that determines a geometry's results."""
    blob = json.dumps({'family': geom.family, 'params': geom.params, 'settings': survey_settings,
                       'd': d_tensors_pm, 'version': version}, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]
