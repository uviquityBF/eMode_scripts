"""First loaded-family sweep (John Carlson deck slides 10-15). Same settings as survey_config.py.

Before the full sweep, run ONE geometry and check em.plot(component='Index') / the field plots:
the partial-etch and mask_offset conventions in geometry.Loaded are not yet verified.

strip_eq: EMode's built-in 'TiO2' has k=0 everywhere (checked via em.refractive_index -- a
visible-range-only fit that silently drops the strong UV absorption at 215-235 nm). Replaced here
with materials/fit_tio2_sellmeier.py's damped-Sellmeier fit to Siefke et al. 2016 (ALD TiO2);
see materials/TiO2_Siefke2016_sellmeier_fit.json for the fit quality and the pump-band-residual
caveat (SH-band n,k are good to 1-3%; pump-band k has a small ~1-3e4 dB/cm artifact vs the real
near-zero value).

IMPORTANT: this uses the REAL-only equation (n only, no loss), not emode_equation_complex --
a complex (lossy, 1j-containing) refractive_index_equation crashes em.FDM() outright
('Cannot cast ufunc add ... complex128 to float64'), confirmed independent of boundary
condition/shape/masking. EMode's actual working mechanism for bulk material loss in this build
is shape(loss_dB_per_m=...) (per-shape, deprecated in favor of material-level `loss`, but
`add_material(loss=...)` was verified NOT to reach the modal loss report -- only the deprecated
shape-level path does); wiring that in needs updating the lossy shape's loss_dB_per_m at every
solve wavelength (pump band vs SH band have very different k), which geometry.py/survey.py don't
do yet. Until that's built, SH loss through this strip is understated (n-only, no absorption).
"""

import json
import os

from survey_config import SETTINGS  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'TiO2_Siefke2016_sellmeier_fit.json')) as _f:
    TIO2_STRIP_EQ = json.load(_f)['emode_equation_real']

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': 0.0, 'strip_eq': TIO2_STRIP_EQ,
                          'h_s': hs, 'w_s': ws})
              for t in (354.0, 600.0) for hs in (70.0, 150.0) for ws in (500.0, 1000.0)]

SMOKE = GEOMETRIES[:1]
