"""Row 8 re-run after the EMode-window fix (2026-10-19). The phase-2 run's 2000 nm substrate
points were solved with the SiO2 top clad cut off by the EMode window (Ridge.window_margin now
auto-expands), so its 10-200x 'kappa jump at 2000 nm' was an artifact -- see PLAN.md.

Restricted to compositions where the TM pump can actually be BOUND in an AlN substrate
(n_eff > n_e(AlN, 450 nm) = 2.186): 23% (marginal/unbound -- kept as the negative control),
27.5% (INTERPOLATED composition, not a Baumler fit -- index = 50/50 blend of the 23% and 32% fitted
equations, d33/d31 = linear mid-point; flagged as such), 32%, 41%. Substrate heights 500/1000/2000
now include the control that the 2000 nm point must agree with 1000 nm for a bound ridge mode.

Run:  python survey.py cerenkov_fixwin survey_config_cerenkov_scaln_fixwin --pumps-only
      python cerenkov_run.py cerenkov_fixwin --config=survey_config_cerenkov_scaln_fixwin
"""
import json
import os

from survey_config_cerenkov_scaln_phase2 import SETTINGS as _P2, D33_D31_BY_COMP, H_CORE, W_CORE
import geometry as geo

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'ScAlN_Baumler2019_sellmeier_fits.json')) as _f:
    _FITS = json.load(_f)['fits']

_eq = lambda c: next(v for k, v in _FITS.items() if abs(float(k) - c) < 1e-9)['emode_equation_real']
_a, _b = D33_D31_BY_COMP[0.23], D33_D31_BY_COMP[0.32]
_mid = ((_a[0] + _b[0]) / 2, (_a[1] + _b[1]) / 2)

SETTINGS = {**_P2, 'd_tensors_pm': {**_P2['d_tensors_pm'],
            'ScAlN_0.28': {'d33': _mid[0], 'd31': _mid[1], 'd15': _mid[1]}}}  # 27.5% -> key 0.28

_ceq = lambda c: next(v for k, v in _FITS.items() if abs(float(k) - c) < 1e-9)['emode_equation_complex']
# real-only core equation -> complex (n + ik) equation, used by the FDFD only (cerenkov_run / cerenkov_scan)
_CORES = {0.23: (_eq(0.23), 'ScAlN_0.23'),
          0.275: (f"0.5*({_eq(0.23)})+0.5*({_eq(0.32)})", 'ScAlN_0.28'),
          0.32: (_eq(0.32), 'ScAlN_0.32'),
          0.41: (_eq(0.41), 'ScAlN_0.41')}
SUBSTRATE_HEIGHT_VALUES = (500.0, 1000.0, 2000.0)

GEOMETRIES = [('ridge', {'h_core': H_CORE, 'w_core': W_CORE, 'core_eq_o': eq, 'core_eq_e': eq,
                         'core_chi2': chi, 'substrate_eq_o': geo.AlN_EQ_O, 'substrate_eq_e': geo.AlN_EQ_E,
                         'substrate_height': h})
              for c, (eq, chi) in _CORES.items() for h in SUBSTRATE_HEIGHT_VALUES]
SMOKE = [GEOMETRIES[-1]]

CORE_COMPLEX = {_eq(0.23): _ceq(0.23), _eq(0.32): _ceq(0.32), _eq(0.41): _ceq(0.41),
                f"0.5*({_eq(0.23)})+0.5*({_eq(0.32)})": f"0.5*({_ceq(0.23)})+0.5*({_ceq(0.32)})"}
SETTINGS = {**SETTINGS, 'cerenkov_core_complex': CORE_COMPLEX}
