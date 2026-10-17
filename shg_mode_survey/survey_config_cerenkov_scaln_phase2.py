"""Phase 2 of the embedded-Cerenkov study (row 8), per user direction 2026-10-17: proper
per-composition d33/d31 (so cerenkov_run.py's FDFD kappa calculation uses the right chi(2) per
point, not AlN's generic 4.7 -- phase 1's config left core_chi2 at its 'AlN' default since the
angle-only scan never needed it) plus a substrate-THICKNESS dimension, motivated directly by the
user's fabrication-reality comments (2026-10-16): MOCVD AlN only grows high-purity up to ~1um
before cracking, so "bulk/infinite AlN substrate" is an idealization -- cerenkov_regions() treats
it as bulk regardless of the simulated thickness for the ANALYTIC angle formula, but the actual
FDM-solved mode landscape (confinement, competing modes) is NOT idealized and can change with a
realistic finite thickness. Also directly relevant after finding (2026-10-16/17) that the
AlN-substrate structure can support spurious substrate/window-edge-pinned pump candidates (see
cerenkov_run.py's MIN_CORE_FRACTION filter, added in response) -- checking whether that behavior
is thickness-dependent is exactly what this dimension is for.

Ridge geometry held FIXED at h_core=350/w_core=400 (phase 1's baseline) -- per user direction
2026-10-13 (row 5 low/high/mid) and reiterated 2026-10-16 ("more important to cover
compositions... than many geometries"), geometric variation is deliberately minimal here; the one
geometric dimension added is the substrate thickness, directly motivated by the fab-reality
comments above, not a general h_core/w_core sweep.

SUBSTRATE_HEIGHT_VALUES = (500, 1000, 2000) nm: below/at/above the ~1um MOCVD practical ceiling.

d33/d31/d15 per composition: AT RISK compositions (23/32/41%) reuse the EXACT values already
established for rows 5.1/5.2/5.3 (consistency, not independently re-derived); the 4 NEW
compositions (0/6/14/17%) are interpolated the same way -- 0% uses AlN's own independently-
established d33=4.7/d31=0.1 (NOT part of the Yoshioka Sc-series, a different measurement
entirely -- flagged the same way the Baumler-vs-ellipsometry 0%-Sc index mismatch was flagged in
phase 1); 6/14/17% are linear interpolation (6% between the AlN anchor and Yoshioka's real 10%
point; 14/17% within Yoshioka's real 10-20% range). Only 41% is extrapolated past Yoshioka's real
range (36%) -- same AT RISK tier as row 5.2.

Run with `python survey.py <run> survey_config_cerenkov_scaln_phase2 --pumps-only`, then
`python cerenkov_run.py <run> --config=survey_config_cerenkov_scaln_phase2` for the FDFD kappa
calculation (reads the pump field exports directly, no EMode needed for that step at all).
"""

import json
import os

from survey_config import SETTINGS as _BASE_SETTINGS
import geometry as geo

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'ScAlN_Baumler2019_sellmeier_fits.json')) as _f:
    _FITS = json.load(_f)['fits']

# composition (Sc fraction) -> (d33, d31) pm/V; d15 = d31 (established convention, no independent
# measurement). 23/32/41% reuse rows 5.1-5.3's exact established values; 0/6/14/17% computed here.
D33_D31_BY_COMP = {
    0.00: (4.70, 0.100),    # AlN's own established value, not the Yoshioka Sc-series
    0.06: (11.36, 0.544),   # interpolated: AlN(0%) -> Yoshioka real 10% point
    0.09: (15.80, 0.840),   # = row 5.1 (uses Yoshioka's real 10% point directly)
    0.14: (26.48, 1.464),   # interpolated within Yoshioka's real 10-20% range
    0.17: (34.49, 1.932),   # interpolated within Yoshioka's real 10-20% range
    0.23: (44.20, 2.800),   # = row 5.3 (interpolated within real 20-28% range)
    0.32: (54.60, 3.950),   # = original project working value (interpolated real 28-36% range)
    0.41: (71.90, 5.200),   # = row 5.2 -- EXTRAPOLATED past Yoshioka's real range, AT RISK
}

SETTINGS = {**_BASE_SETTINGS, 'd_tensors_pm': {
    **_BASE_SETTINGS['d_tensors_pm'],
    **{f'ScAlN_{c:.2f}': {'d33': d33, 'd31': d31, 'd15': d31} for c, (d33, d31) in D33_D31_BY_COMP.items()},
}}

H_CORE, W_CORE = 350.0, 400.0
SUBSTRATE_HEIGHT_VALUES = (500.0, 1000.0, 2000.0)

GEOMETRIES = [('ridge', {'h_core': H_CORE, 'w_core': W_CORE,
                         'core_eq_o': fit['emode_equation_real'],
                         'core_eq_e': fit['emode_equation_real'],
                         'core_chi2': f'ScAlN_{float(comp):.2f}',
                         'substrate_eq_o': geo.AlN_EQ_O, 'substrate_eq_e': geo.AlN_EQ_E,
                         'substrate_height': sub_h})
              for comp, fit in _FITS.items() for sub_h in SUBSTRATE_HEIGHT_VALUES]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
