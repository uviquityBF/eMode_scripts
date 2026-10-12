"""ARCHIVAL record of the first 'hybrid'-named sweep, 2026-10-05 -- kept for reproducibility under
its honest family name after the 2026-10-10 fix (see PLAN.md). This is NOT the Honda et al. AlN-
embedded-in-SiNx structure: `Hybrid.build()` never set an explicit `position` on the AlN core shape
until 2026-10-10, so EMode auto-stacked it on top of the SiNx shell instead of embedding it within
the shell's footprint. The results this config originally produced (archived as `pedestal1`, still
in `runs/`) are valid for THIS stacked structure (an AlN strip loaded on an etched SiNx rib) -- a
real, different waveguide, just not the one this config's own docstring (below, left as written at
the time) describes. Identical to `survey_config_hybrid.py` except `family='pedestal'` and this
note; not meant to be run again (the original run is already archived) -- see
`survey_config_hybrid.py` for the config actually reused in the corrected re-run campaign.

Original docstring, 2026-10-05: First 'hybrid' (AlN/SiNx) family sweep, adapted to this project's
UV target (215-235 nm SH, 430-470 nm pump) rather than the Honda et al. 2025 paper's telecom demo
(1550/775 nm). Geometry convention (verified 2026-10-05 via em.plot(component='Index') against the
smoke geometry): both the SiNx shell and the AlN core are built with mask=width AND
etch_depth=<shape's own height> -- mask alone is a no-op in EMode's shape() API; etch_depth equal
to the shape's own height is what actually restricts it to a finite-width raised region instead of
filling the whole window (same convention geometry.Loaded's 'strip' already relied on). The AlN
core is drawn after the SiNx shell so it takes priority in their overlapping footprint ("later
shape wins") -- true, but incomplete: priority only matters where shapes actually overlap, and
(unknown at the time) they didn't. AlN core dimensions start near this project's own established
good range for `ridge` (trial_grid: h=300-400, w=300-800 nm) rather than the paper's telecom-scale
values (555/730 nm). SiNx shell sized with a flat margin around the core.
"""

import json
import os

from survey_config import SETTINGS  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'SiNx_Beliaev2022_sellmeier_fit.json')) as _f:
    _fit = json.load(_f)
SINX_SHELL_EQ = _fit['emode_equation_real']
SINX_SHELL_LOSS_EQ = _fit['emode_equation_complex']

SHELL_MARGIN_W, SHELL_MARGIN_H = 400.0, 300.0  # nm, shell outer box beyond the AlN core's own bbox

GEOMETRIES = [('pedestal', {'h_core': h, 'w_core': w,
                          'sin_width': w + SHELL_MARGIN_W, 'sin_height': h + SHELL_MARGIN_H,
                          'shell_eq': SINX_SHELL_EQ, 'shell_loss_eq': SINX_SHELL_LOSS_EQ})
              for h in (300.0, 350.0, 400.0) for w in (400.0, 500.0)]

SMOKE = GEOMETRIES[:1]
