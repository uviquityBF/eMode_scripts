"""ARCHIVAL record, 2026-10-09/10 -- kept for reproducibility under its honest family name after
the 2026-10-10 fix (see PLAN.md and survey_config_pedestal.py's docstring): the AlN core this
config actually built was stacked on top of the SiNx shell, not embedded in it -- archived as
`pedestal_vertical1`. Identical to `survey_config_hybrid_vertical.py` except `family='pedestal'`;
not meant to be run again -- see `survey_config_hybrid_vertical.py` for the config reused
(unchanged) in the corrected re-run campaign.

Original docstring, 2026-10-09/10, left as written at the time:

Vertical-dimension 'hybrid' sweep: decouples sin_height from h_core the same way
survey_config_hybrid_sweep.py decoupled sin_width from w_core, rather than just re-running the
lateral grid at one new thickness (user explicitly asked for the former, not the latter -- see
PLAN.md's "Targeted hybrid sweep" entry, which flagged that the lateral sweep never touched
vertical dimensions at all).

Lateral dimensions fixed at the best-performing combo from the lateral sweep (w_core=400,
sin_width=700, 25.2 %/W/cm^2, TM01->TM81) -- this sweep is specifically asking "does changing
vertical confinement/dispersion open up a crossing (TM00->TM20 or otherwise) that the lateral
sweep's one fixed h_core=400/sin_height=700 couldn't reach," not re-searching the lateral space.

h_core in {250,300,350,400,450} nm x sin_height in {500,650,800,950,1100} nm, kept where
sin_height >= h_core + 200 (same 200 nm minimum shell margin convention as the lateral sweep) --
22 geometries. num_sh_modes raised to 45 for the same reason as the lateral sweep (coverage risk
for whichever SH mode ends up mattering); a taller sin_height can pack in more vertical modes the
same way a wider sin_width packed in more lateral ones.
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
SIN_HEIGHT_VALUES = (500.0, 650.0, 800.0, 950.0, 1100.0)
MIN_SHELL_MARGIN = 200.0  # nm, sin_height - h_core floor

GEOMETRIES = [('pedestal', {'h_core': h, 'w_core': W_CORE, 'sin_width': SIN_WIDTH, 'sin_height': sh,
                          'shell_eq': SINX_SHELL_EQ, 'shell_loss_eq': SINX_SHELL_LOSS_EQ})
              for h in H_CORE_VALUES for sh in SIN_HEIGHT_VALUES if sh >= h + MIN_SHELL_MARGIN]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
