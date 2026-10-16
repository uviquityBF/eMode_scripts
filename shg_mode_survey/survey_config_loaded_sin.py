"""Rib-loaded sweep with a SiN strip instead of TiO2 (Simulation Study Plan row 4) -- TiO2 (row 3)
was run and found bad (SH-absorbing, collapses real efficiency far below ridge's).

t_film grid bumped from 2 points {354, 600} (survey_config_loaded.py's TiO2 sweep, row 3) to 4
evenly-spaced points spanning the same real range, per user direction 2026-10-13: 2 points along
each of 3 dimensions (8 geometries total) wasn't enough resolution on the thickness dependence.
h_s/w_s left at their original 2-point extremes {70,150}/{500,1000} for now -- user flagged film
thickness specifically ("at least"), not a blanket 3-4x on every dimension; 32 geometries (4x2x2)
here + 32 in row 5 (ScAlN) is already ~2x row 3/4's original combined cost. Revisit h_s/w_s
resolution later if this run's results motivate it.

etch_depth stays fixed at 0 (unetched film, full loading) -- sweeping it is the "pure rib, no
loading" idea discussed 2026-10-13 (h_A swept with the strip removed entirely), deliberately
deferred to its own follow-up rather than folded in here.

SiN n+ik: materials/SiNx_Beliaev2022_sellmeier_fit.json (same fit used for the hybrid family's
shell, Beliaev et al. 2022), same real-eq/complex-eq split as the TiO2 config for the same EMode
reason (a complex refractive_index_equation crashes em.FDM() outright; the complex form is only
ever evaluated in Python for the post-solve bulk-loss perturbation, never given to EMode).

sh_absorption_calibrated=True set from launch, per the 2026-10-12 standing SH-loss assumption
(build_assumptions_report.py section 3b) -- not added after the fact.
"""

import json
import os

from survey_config import SETTINGS  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'SiNx_Beliaev2022_sellmeier_fit.json')) as _f:
    _fit = json.load(_f)
SIN_STRIP_EQ = _fit['emode_equation_real']
SIN_STRIP_LOSS_EQ = _fit['emode_equation_complex']

T_FILM_VALUES = (354.0, 436.0, 518.0, 600.0)

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': 0.0, 'strip_eq': SIN_STRIP_EQ,
                          'strip_loss_eq': SIN_STRIP_LOSS_EQ, 'h_s': hs, 'w_s': ws,
                          'sh_absorption_calibrated': True})
              for t in T_FILM_VALUES for hs in (70.0, 150.0) for ws in (500.0, 1000.0)]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
