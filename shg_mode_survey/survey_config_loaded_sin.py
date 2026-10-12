"""Rib-loaded sweep with a SiN strip instead of TiO2 (Simulation Study Plan row 4) -- TiO2 (row 3)
was run and found bad (SH-absorbing, collapses real efficiency far below ridge's). Same t_film/
h_s/w_s grid as survey_config_loaded.py's TiO2 sweep, deliberately unchanged, so the two are
directly comparable apples-to-apples: row 3 ruled TiO2 out on the material, not the geometry, so
there's no reason to re-search the dimensional space here.

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

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': 0.0, 'strip_eq': SIN_STRIP_EQ,
                          'strip_loss_eq': SIN_STRIP_LOSS_EQ, 'h_s': hs, 'w_s': ws,
                          'sh_absorption_calibrated': True})
              for t in (354.0, 600.0) for hs in (70.0, 150.0) for ws in (500.0, 1000.0)]

SMOKE = GEOMETRIES[:1]
