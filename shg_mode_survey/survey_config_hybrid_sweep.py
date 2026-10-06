"""Targeted 'hybrid' (AlN/SiNx) sweep, searching for the Honda et al. 2025 TM00->TM20 mechanism
itself (or any higher-lateral-order analogue) rather than the arbitrary-margin first pass in
survey_config_hybrid.py (see PLAN.md, "hybrid_smoke + first 6-geometry hybrid sweep": that run's
6 geometries used sin_width/sin_height as a fixed offset above w_core/h_core, found 0 window
artifacts but also no TM00->TM20 anywhere in 2290 crossings -- not evidence the mechanism fails in
the UV band, just that nothing in that grid was built to trigger it).

Mechanism this sweep targets: TM20 (m=2 lateral nodes) has a lateral E-field sign pattern with
3 lobes, e.g. (-,+,-). d33 couples Ey*Ey (pump, single-signed) into Py, so the SHG overlap
integral only picks up the SH field where chi(2) (i.e. AlN) is actually present; AlN spread across
all 3 lobes self-cancels (the mechanism the paper exists to fix, and the reason a plain ridge can't
reach TM00->TM02/TM20 -- see PLAN.md's ridge findings). The fix is positioning AlN (here: sized by
`w_core`, centered) so it only occupies one sign region, not matching the shell's absolute size to
the core's. That's a function of the *shell width* (which sets how many lateral modes fit, and
each one's lobe width) crossed with the *core-to-shell width ratio* (which sets how much of
whichever lobe pattern gets AlN) -- hence this sweep decouples sin_width from w_core entirely
(previously `sin_width = w_core + 400` by construction, so this ratio was never actually varied)
and scans both independently, at fixed h_core/sin_height (vertical dimensions mainly set
confinement strength and n=0 vertical order, secondary to the lateral-matching question this sweep
targets -- deferred to a follow-up if this finds something worth refining).

h_core fixed at 400 nm (best NCE, 21.1 %/W/cm^2, among the first pass's 6 geometries).
sin_height fixed at 700 nm (= h_core + 300, same margin convention as the first pass).
w_core in {200, 300, 400, 500, 600} nm x sin_width in {700, 900, 1100, 1300, 1500} nm, kept where
sin_width >= w_core + 200 (at least 100 nm SiNx margin on each side, so it's recognizably a core
embedded in a shell and not just a marginally-larger ridge) -- 24 geometries.

num_sh_modes raised 30 -> 45: the first-pass sweep logged "SH n_eff window too narrow" warnings on
every geometry (21-42 group-steps affected, worse for wider shells), meaning the default 30-mode
window sometimes didn't span the full pump-n_eff +/- margin range at a given step -- a real
coverage gap, not cosmetic, and a real risk of missing the exact higher-lateral-order SH mode this
sweep exists to find. Costs roughly 1.5x the SH-scan time per step; accepted given this sweep's
whole point is not to miss that mode. sh_window_margin left at survey_config's default (0.10) --
phase-matching crossings are by definition near-equal-n_eff, so margin isn't the limiting factor
here, mode-count-per-step is.
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

H_CORE, SIN_HEIGHT = 400.0, 700.0
W_CORE_VALUES = (200.0, 300.0, 400.0, 500.0, 600.0)
SIN_WIDTH_VALUES = (700.0, 900.0, 1100.0, 1300.0, 1500.0)
MIN_SHELL_MARGIN = 200.0  # nm, sin_width - w_core floor

GEOMETRIES = [('hybrid', {'h_core': H_CORE, 'w_core': w, 'sin_width': sw, 'sin_height': SIN_HEIGHT,
                          'shell_eq': SINX_SHELL_EQ, 'shell_loss_eq': SINX_SHELL_LOSS_EQ})
              for w in W_CORE_VALUES for sw in SIN_WIDTH_VALUES if sw >= w + MIN_SHELL_MARGIN]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
