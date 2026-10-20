"""Bandwidth study for the Cerenkov channel (row 8, 2026-10-20): pump-only solves at SH wavelengths
215..235 nm for the best thin-core geometries, so kappa(lambda) can be computed with the FDFD.
The SH window centre is set by the environment variable LAMBDA_SH (nm); the run name encodes it.
  for L in 215 220 225 230 235; do LAMBDA_SH=$L python survey.py cerenkov_bw_$L survey_config_cerenkov_scaln_bw --pumps-only; done
d33 is held constant with wavelength (no dispersion data) -- a stated limitation.
"""
import os

from survey_config_cerenkov_scaln_fixwin import SETTINGS as _S, _CORES, CORE_COMPLEX  # noqa: F401
import geometry as geo

_L = float(os.environ.get('LAMBDA_SH', '225'))
SETTINGS = {**_S, 'lambda_sh_min': _L - 0.5, 'lambda_sh_max': _L + 0.5, 'pump_points': 3}

_GEOM = [(0.41, 200.0, 300.0), (0.41, 200.0, 400.0), (0.32, 200.0, 600.0), (0.41, 350.0, 400.0)]
GEOMETRIES = [('ridge', {'h_core': h, 'w_core': w, 'core_eq_o': _CORES[c][0], 'core_eq_e': _CORES[c][0],
                         'core_chi2': _CORES[c][1], 'substrate_eq_o': geo.AlN_EQ_O,
                         'substrate_eq_e': geo.AlN_EQ_E, 'substrate_height': 1000.0})
              for c, h, w in _GEOM]
SMOKE = GEOMETRIES[:1]
