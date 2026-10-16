"""Ridge baseline refresh (Simulation Study Plan row 1), replacing row1_ridge_v1/
row1_ridge_v1_wide_window (formerly trial_grid/wide_window) as the current baseline.
row1_ridge_v1's own progress.log shows 36 "SH n_eff window too narrow" warnings across its 18
geometries -- the identical under-coverage symptom later found and fixed for the hybrid campaign
by raising num_sh_modes 30->45 (see survey_config_hybrid_sweep.py's docstring). row1_ridge_v1
predates that fix, so its reported best crossings carried the same unconfirmed-miss risk the
hybrid first pass had before the fix was applied. row1_ridge_v1 also predates the 2026-10-12
SH-loss calibration (sh_absorption_calibrated=True) that every current-era run now launches with,
so its numbers weren't on the same footing as row6_hybrid_lateral/row6_hybrid_vertical for
comparison either.

Same geometry grid as row1_ridge_v1 (survey_config_grid.py / survey_config.TRIAL_GRID): h_core in
{300, 350, 400} nm x w_core 300-800 nm step 100 nm, 18 geometries -- deliberately unchanged, this
is a settings refresh of row 1 (closing a correctness gap), not a re-search of the dimensional
space.

Run under a NEW run_name ('row1_ridge', originally launched as 'ridge_sweep1' then renamed
2026-10-13 along with the other run directories -- see PLAN.md), not reusing 'row1_ridge_v1':
num_sh_modes and sh_absorption_calibrated are both hashed into each geometry's fingerprint
(geo.fingerprint), so reusing the old run_name would have appended new rows alongside the old
(num_sh_modes=30, uncalibrated) rows for the same (h_core, w_core) pairs in the same crossings.csv,
with no tooling able to tell the two apart. row1_ridge_v1/row1_ridge_v1_wide_window are left
untouched on disk (same treatment the pedestal family got when hybrid replaced it as the
embedded-AlN result).

RESULT (2026-10-13): completed, 18/18 ok, 0 errors, 183.7 min. Best crossing unchanged from
row1_ridge_v1: TM10->TM60 @ 221.6 nm, h=350/w=400, NCE 14.9 %/W/cm^2 -- the coverage gap was real
(warnings fired on most geometries) but didn't hide a better point than row1_ridge_v1 already found.
"""

import numpy as np

from survey_config import SETTINGS as _BASE_SETTINGS

SETTINGS = {**_BASE_SETTINGS, 'num_sh_modes': 45}

GEOMETRIES = [('ridge', {'h_core': float(h), 'w_core': float(w), 'sh_absorption_calibrated': True})
              for h in (300.0, 350.0, 400.0) for w in np.arange(300.0, 801.0, 100.0)]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
