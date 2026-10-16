"""Rib-loaded sweep with a LOW-Sc ScAlN strip (Simulation Study Plan row 5, "low" composition
level of 2, per user direction 2026-10-13/14): 9% Sc, chosen specifically because it sits right at
Yoshioka 2021's real measured 10%-Sc sputtered point (d33=15.8, d31=0.84 pm/V) -- using that value
directly needs no interpolation at all, the lowest-risk d33 source in this project. Purpose per
user: "a low composition that is simply large enough to increase the index and pull the mode up"
-- the chi(2) contribution here is a bonus, not the point (compare against row 5 "high").

Same t_film/h_s/w_s grid as survey_config_loaded_sin.py (row 4) and the 2026-10-13 t_film bump to
4 points -- unchanged here, see that file's docstring.

ScAlN n+ik: materials/ScAlN_Baumler2019_sellmeier_fits.json, 9% Sc. Uses the POLE-FIXED
emode_equation_real (materials/fix_baumler_real_equation.py, 2026-10-14) -- the original
real-only equation had literal poles landing inside the SH band for several compositions
(dropping the damping term from a fitted damped-Lorentzian turns a smooth peak into a true
divergence), which is what actually crashed EMode's eigenvalue solver during the row-5 smoke test
(its "not enough memory" message was misleading; the machine has >1TB free). At 9% Sc this fix is
essentially exact (SH-band max|err| in n ~0.016, see the json's real_equation_fix block) -- the
resonance structure sits well clear of 215-235nm at this composition.

strip_chi2='ScAlN': d33=15.8, d31=d15=0.84 pm/V (Yoshioka 2021 sputtered, real 10%-Sc point, used
near-directly -- NOT the same AT RISK/interpolated treatment as the d33=54.6 (32%) value used
elsewhere; this is the closest this project gets to an unextrapolated measured d33). core_chi2
stays 'AlN' -- both AlN (d33=4.7) and this strip contribute to the same crossing's overlap.

sh_absorption_calibrated=True set from launch, per the 2026-10-12 standing SH-loss assumption.
"""

import json
import os

from survey_config import SETTINGS as _BASE_SETTINGS

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'ScAlN_Baumler2019_sellmeier_fits.json')) as _f:
    _fit = json.load(_f)['fits']['0.09']
SCALN_STRIP_EQ = _fit['emode_equation_real']
SCALN_STRIP_LOSS_EQ = _fit['emode_equation_complex']

SETTINGS = {**_BASE_SETTINGS, 'd_tensors_pm': {**_BASE_SETTINGS['d_tensors_pm'],
            'ScAlN': {'d33': 15.8, 'd31': 0.84, 'd15': 0.84}}}

T_FILM_VALUES = (354.0, 436.0, 518.0, 600.0)

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': 0.0, 'strip_eq': SCALN_STRIP_EQ,
                          'strip_loss_eq': SCALN_STRIP_LOSS_EQ, 'strip_chi2': 'ScAlN',
                          'h_s': hs, 'w_s': ws, 'sh_absorption_calibrated': True})
              for t in T_FILM_VALUES for hs in (70.0, 150.0) for ws in (500.0, 1000.0)]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
