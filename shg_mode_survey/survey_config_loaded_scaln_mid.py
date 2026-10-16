"""Rib-loaded sweep with a MIDDLE-Sc ScAlN strip (Simulation Study Plan row 5.3, 3rd of 3
composition levels per user direction 2026-10-14): 23% Sc -- the Baumler-fitted composition
closest to the low (9%, row 5.1) / high (41%, row 5.2) midpoint, chosen to fill the gap between
them now that both ends are done.

Same t_film/h_s/w_s grid as row 4 / row 5.1 / row 5.2 -- unchanged here.

ScAlN n+ik: materials/ScAlN_Baumler2019_sellmeier_fits.json, 23% Sc, POLE-FIXED emode_equation_real
(materials/fix_baumler_real_equation.py, 2026-10-14). Fit quality here is BETTER than row 5.2's:
SH-band max|err| in n ~0.056 (vs. 5.2's ~0.21) -- the true resonance sits further from the band at
this composition, so less distortion was needed to keep the pole out.

strip_chi2='ScAlN': d33=44.2, d31=d15=2.8 pm/V -- INTERPOLATED (not extrapolated) from Yoshioka
2021's two REAL sputtered points bracketing 23% (20%: d33=42.5/d31=2.4; 28%: d33=46.9/d31=3.4),
linear interpolation. Lower risk than row 5.2's extrapolated value -- same treatment as the
original 32%-Sc working value (interpolated between real 28%/36% points).

sh_absorption_calibrated=True set from launch, per the 2026-10-12 standing SH-loss assumption.
"""

import json
import os

from survey_config import SETTINGS as _BASE_SETTINGS

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'ScAlN_Baumler2019_sellmeier_fits.json')) as _f:
    _fit = json.load(_f)['fits']['0.23']
SCALN_STRIP_EQ = _fit['emode_equation_real']
SCALN_STRIP_LOSS_EQ = _fit['emode_equation_complex']

SETTINGS = {**_BASE_SETTINGS, 'd_tensors_pm': {**_BASE_SETTINGS['d_tensors_pm'],
            'ScAlN': {'d33': 44.2, 'd31': 2.8, 'd15': 2.8}}}

T_FILM_VALUES = (354.0, 436.0, 518.0, 600.0)

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': 0.0, 'strip_eq': SCALN_STRIP_EQ,
                          'strip_loss_eq': SCALN_STRIP_LOSS_EQ, 'strip_chi2': 'ScAlN',
                          'h_s': hs, 'w_s': ws, 'sh_absorption_calibrated': True})
              for t in T_FILM_VALUES for hs in (70.0, 150.0) for ws in (500.0, 1000.0)]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
