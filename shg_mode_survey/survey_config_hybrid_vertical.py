"""Vertical-dimension 'hybrid' sweep: decouples sin_height from h_core the same way
survey_config_hybrid_sweep.py decoupled sin_width from w_core, rather than just re-running the
lateral grid at one new thickness (user explicitly asked for the former, not the latter -- see
PLAN.md's "Targeted hybrid sweep" entry, which flagged that the lateral sweep never touched
vertical dimensions at all).

Lateral dimensions fixed at the best-performing combo from the lateral sweep (w_core=400,
sin_width=700, 25.2 %/W/cm^2, TM01->TM81) -- this sweep is specifically asking "does changing
vertical confinement/dispersion open up a crossing (TM00->TM20 or otherwise) that the lateral
sweep's one fixed h_core=400/sin_height=700 couldn't reach," not re-searching the lateral space.

h_core in {250,300,350,400,450} nm x sin_height in {450,500,650,800,950,1100} nm, kept where
sin_height >= h_core + 200 (same 200 nm minimum shell margin convention as the lateral sweep) --
23 geometries. num_sh_modes raised to 45 for the same reason as the lateral sweep (coverage risk
for whichever SH mode ends up mattering); a taller sin_height can pack in more vertical modes the
same way a wider sin_width packed in more lateral ones.

sin_height=450 added 2026-10-12: the pedestal-family archival data (same vertical range, before
the embedding fix) showed a "smaller sin_height keeps winning" trend across 500-1100 that never
bottomed out within the range tested -- this adds exactly one point (h_core=250/sin_height=450,
the smallest margin-valid combination, right at the 200nm floor) to check whether that trend
continues to the boundary under the corrected embedded geometry, without reopening the margin
convention itself.

sh_absorption_calibrated=True added 2026-10-12: the standing SH-loss assumption for every new run
from here on (geometry.sh_absorption_calibrated_dB_per_m, 100 dB/cm flat/confinement-weighted --
see build_assumptions_report.py section 3b). Stored separately as sh_calibrated_dB_per_m in
crossings.csv, not merged invisibly into sh_absorption_dB_per_m.
"""

import json
import os

from survey_config import SETTINGS as _BASE_SETTINGS

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'SiNx_Beliaev2022_sellmeier_fit.json')) as _f:
    _fit = json.load(_f)
SINX_SHELL_EQ = _fit['emode_equation_real']
SINX_SHELL_LOSS_EQ = _fit['emode_equation_complex']

SETTINGS = {**_BASE_SETTINGS, 'num_sh_modes': 45}

W_CORE, SIN_WIDTH = 400.0, 700.0
H_CORE_VALUES = (250.0, 300.0, 350.0, 400.0, 450.0)
SIN_HEIGHT_VALUES = (450.0, 500.0, 650.0, 800.0, 950.0, 1100.0)
MIN_SHELL_MARGIN = 200.0  # nm, sin_height - h_core floor

GEOMETRIES = [('hybrid', {'h_core': h, 'w_core': W_CORE, 'sin_width': SIN_WIDTH, 'sin_height': sh,
                          'shell_eq': SINX_SHELL_EQ, 'shell_loss_eq': SINX_SHELL_LOSS_EQ,
                          'sh_absorption_calibrated': True})
              for h in H_CORE_VALUES for sh in SIN_HEIGHT_VALUES if sh >= h + MIN_SHELL_MARGIN]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
