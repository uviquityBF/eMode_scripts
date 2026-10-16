"""Rib-loaded sweep with a HIGH-Sc ScAlN strip (Simulation Study Plan row 5, "high" composition
level of 2, per user direction 2026-10-13/14): 41% Sc, Baumler 2019's highest fitted index
composition -- the most extreme Sc level this project has index data for at all. Purpose per
user: "a much higher Sc concentration in which case I'd be looking for the d33 boost".

Same t_film/h_s/w_s grid as survey_config_loaded_sin.py (row 4) and survey_config_loaded_scaln_low.py
-- unchanged here.

ScAlN n+ik: materials/ScAlN_Baumln2019_sellmeier_fits.json, 41% Sc, POLE-FIXED emode_equation_real
(materials/fix_baumler_real_equation.py, 2026-10-14 -- see that file and row 5 low's docstring for
why the original real-only equation crashed EMode outright). Fit quality is WORSE here than at low
Sc: the true resonance sits close to/inside the SH band at this composition (that's why the
original fit had a pole there), so forcing it out distorts the nearby curve more -- SH-band
max|err| in n ~0.21 (n~3.07-3.15 true vs ~3.0-3.28 fit), pump-band max|err| ~0.035. Tried
tightening the pole-exclusion margin; made no meaningful difference (the limitation is the real
resonance's proximity to the band, not the margin choice) -- see fix_baumler_real_equation.py's
own pole-check output. BELIEVABLE (physically sane values, not the original disaster) but NOT
accurate in the way the low-Sc fit is; treat row 5 high's phase-matching wavelengths with more
skepticism than row 5 low's.

strip_chi2='ScAlN': d33=71.9, d31=d15=5.2 pm/V -- EXTRAPOLATED (not interpolated) from Yoshioka
2021's two highest REAL sputtered points (28%: d33=46.9/d31=3.4; 36%: d33=62.3/d31=4.5), linear
slope projected 5 points past the highest actually-measured composition (36%). Materially more at
risk than the established d33=54.6 (32%, interpolated BETWEEN two real points) value used
elsewhere in this project -- flagged distinctly, not the same "AT RISK" tier. core_chi2 stays
'AlN'.

sh_absorption_calibrated=True set from launch, per the 2026-10-12 standing SH-loss assumption.
"""

import json
import os

from survey_config import SETTINGS as _BASE_SETTINGS

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'ScAlN_Baumler2019_sellmeier_fits.json')) as _f:
    _fit = json.load(_f)['fits']['0.41']
SCALN_STRIP_EQ = _fit['emode_equation_real']
SCALN_STRIP_LOSS_EQ = _fit['emode_equation_complex']

SETTINGS = {**_BASE_SETTINGS, 'd_tensors_pm': {**_BASE_SETTINGS['d_tensors_pm'],
            'ScAlN': {'d33': 71.9, 'd31': 5.2, 'd15': 5.2}}}

T_FILM_VALUES = (354.0, 436.0, 518.0, 600.0)

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': 0.0, 'strip_eq': SCALN_STRIP_EQ,
                          'strip_loss_eq': SCALN_STRIP_LOSS_EQ, 'strip_chi2': 'ScAlN',
                          'h_s': hs, 'w_s': ws, 'sh_absorption_calibrated': True})
              for t in T_FILM_VALUES for hs in (70.0, 150.0) for ws in (500.0, 1000.0)]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
