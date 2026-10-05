"""First 'hybrid' (AlN/SiNx) family sweep, adapted to this project's UV target (215-235 nm SH,
430-470 nm pump) rather than the Honda et al. 2025 paper's telecom demo (1550/775 nm) -- see
geometry.Hybrid's docstring for the structure.

Geometry convention (verified 2026-10-05 via em.plot(component='Index') against the smoke
geometry): both the SiNx shell and the AlN core are built with mask=width AND
etch_depth=<shape's own height> -- mask alone is a no-op in EMode's shape() API; etch_depth equal
to the shape's own height is what actually restricts it to a finite-width raised region instead of
filling the whole window (same convention geometry.Loaded's 'strip' already relied on). The AlN
core is drawn after the SiNx shell so it takes priority in their overlapping footprint ("later
shape wins").

AlN core dimensions start near this project's own established good range for `ridge` (trial_grid:
h=300-400, w=300-800 nm) rather than the paper's telecom-scale values (555/730 nm) -- the paper's
absolute core size optimizes confinement at 1550 nm pump, not 450 nm, so it's a starting point to
scale from, not a default to copy. SiNx shell sized with a flat margin around the core; both are
free parameters worth sweeping once the smoke test confirms the geometry is being built correctly.
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

GEOMETRIES = [('hybrid', {'h_core': h, 'w_core': w,
                          'sin_width': w + SHELL_MARGIN_W, 'sin_height': h + SHELL_MARGIN_H,
                          'shell_eq': SINX_SHELL_EQ, 'shell_loss_eq': SINX_SHELL_LOSS_EQ})
              for h in (300.0, 350.0, 400.0) for w in (400.0, 500.0)]

SMOKE = GEOMETRIES[:1]
