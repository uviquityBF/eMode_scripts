"""First loaded-family sweep (John Carlson deck slides 10-15). Same settings as survey_config.py.

Before the full sweep, run ONE geometry and check em.plot(component='Index') / the field plots:
the partial-etch and mask_offset conventions in geometry.Loaded are not yet verified.

TiO2: EMode's built-in 'TiO2' has k=0 everywhere (checked via em.refractive_index -- a
visible-range-only fit that silently drops the strong UV absorption at 215-235 nm). Replaced here
with materials/fit_tio2_sellmeier.py's damped-Sellmeier fit to Siefke et al. 2016 (ALD TiO2);
see materials/TiO2_Siefke2016_sellmeier_fit.json for the fit quality and the pump-band-residual
caveat (SH-band n,k are good to 1-3%; pump-band k has a small ~1-3e4 dB/cm artifact vs the real
near-zero value). Two separate equations are used:

- strip_eq: the REAL-only part (n), given to EMode as the strip's refractive_index_equation. A
  complex (lossy, 1j-containing) one crashes em.FDM() outright -- confirmed a genuine EMode bug
  (not version drift: re-tested on v1.0.0, v1.0.4, v1.0.5, same crash every time, full traceback
  points at numpy_shape_utils.add_scaled in EMode's own make_tensors).
- strip_loss_eq: the full complex n+ik equation, evaluated in Python only (never given to EMode).
  geometry.Loaded.apply_losses() reads k(lambda) from it and feeds the resulting bulk loss
  [dB/m] to EMode via shape(loss_dB_per_m=...) before every solve, recomputed per wavelength
  (pump band vs SH band need very different values) -- the only mechanism confirmed to actually
  produce EMode-computed, confinement-weighted modal loss for bulk material absorption in this
  EMode version (also re-verified add_material(loss=...) does NOT work for a plain FDM solve on
  v1.0.5: it's an EME-only mechanism per EMode's 1.0.5 release notes, not an FDM one).
"""

import json
import os

from survey_config import SETTINGS  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'TiO2_Siefke2016_sellmeier_fit.json')) as _f:
    _fit = json.load(_f)
TIO2_STRIP_EQ = _fit['emode_equation_real']
TIO2_STRIP_LOSS_EQ = _fit['emode_equation_complex']

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': 0.0, 'strip_eq': TIO2_STRIP_EQ,
                          'strip_loss_eq': TIO2_STRIP_LOSS_EQ, 'h_s': hs, 'w_s': ws})
              for t in (354.0, 600.0) for hs in (70.0, 150.0) for ws in (500.0, 1000.0)]

SMOKE = GEOMETRIES[:1]
