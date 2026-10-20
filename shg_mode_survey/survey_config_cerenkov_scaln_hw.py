"""Row 8 geometry sweep (2026-10-19): h_core x w_core for the ScAlN-core ridge on an AlN substrate,
32% and 41% Sc, 1000 nm substrate (bound-pump results are identical for 500/1000/2000 nm after the
window fix). Purpose: map where the TM00/TE pump is BOUND (n_eff > n_AlN(450) on its axis) and where
the Cerenkov kappa peaks -- the skin-limited emission suggests thin cores may lose little.

Run:  python survey.py cerenkov_hw survey_config_cerenkov_scaln_hw --pumps-only
      python cerenkov_cases.py cerenkov_hw --config=survey_config_cerenkov_scaln_hw \
             --k-cases=fit_x0.25,fit_x0.5,fit,fit_x2 --d=7.5 --min-core=0.3
"""
from survey_config_cerenkov_scaln_fixwin import (SETTINGS, _CORES, CORE_COMPLEX)  # noqa: F401
import geometry as geo

H_VALUES = (200.0, 250.0, 300.0, 350.0, 450.0)
W_VALUES = (300.0, 400.0, 600.0, 800.0)
COMPS = (0.32, 0.41)

GEOMETRIES = [('ridge', {'h_core': h, 'w_core': w, 'core_eq_o': _CORES[c][0], 'core_eq_e': _CORES[c][0],
                         'core_chi2': _CORES[c][1], 'substrate_eq_o': geo.AlN_EQ_O,
                         'substrate_eq_e': geo.AlN_EQ_E, 'substrate_height': 1000.0})
              for c in COMPS for h in H_VALUES for w in W_VALUES]
SMOKE = [g for g in GEOMETRIES if g[1]['h_core'] == 350.0 and g[1]['w_core'] == 400.0][:1]
