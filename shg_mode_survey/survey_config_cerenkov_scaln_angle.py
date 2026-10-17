"""Phase 1 of the embedded-Cerenkov study (row 8), per user direction 2026-10-16: a cheap,
composition-only scan of the Cerenkov angle, before any geometry exploration or d33/kappa work.

Structure: a plain AlN-system RIDGE waveguide (geometry.Ridge, no new geometry class -- see
PLAN.md's 2026-10-16 entry for why the originally-floated "channel embedded in blanket AlN"
geometry turned out to be unnecessary) with a ScAlN core (composition swept) sitting on a REAL
AlN substrate (not Al2O3) -- the out-coupling direction the user specifically wants to study,
since real-device Cerenkov radiation has to go somewhere, and "blanket on all sides" isn't
buildable. AlN substrate uses geometry.Ridge's new substrate_eq_o/substrate_eq_e (added
2026-10-16), ANISOTROPIC per the existing row 10 decision (user direction 2026-10-12), reusing
the project's own AlN_EQ_O/AlN_EQ_E fit -- no new materials data needed.

Why this is cheap: the Cerenkov angle (shg_physics.cerenkov_flags: angle_deg =
arccos(n_eff_pump/n_region)) is pure linear optics -- needs only the pump mode's n_eff and the
substrate's bulk index at the SH wavelength, neither of which needs chi(2)/d33 or a full SH
phase-matching search. Run with `python survey.py <run> survey_config_cerenkov_scaln_angle
--pumps-only`: skips the SH scan entirely (survey.py's existing --pumps-only mode), reusing
characterize_pump()'s already-built cerenkov_regions()/cerenkov_flags() call -- no new analysis
code, just the right geometry. cerenkov_regions() already treats the substrate as bulk/infinite
regardless of the simulated substrate_height, so there's no thickness-convergence sweep needed
either (unlike the originally-floated embedded-shell idea, which would have needed one).

Composition sweep: all 8 Baumler-fitted ScAlN compositions (0/6/9/14/17/23/32/41% Sc), reusing the
already pole-fixed real equations (materials/fix_baumler_real_equation.py, 2026-10-14) -- no new
materials work. d33 is irrelevant here (pumps-only, no overlap integral computed), so
d_tensors_pm isn't populated per-composition; this config is NOT meant to be re-run with the SH
scan enabled as-is.

ScAlN core treated ISOTROPICALLY (core_eq_o = core_eq_e = Baumler's single fitted curve): Baumler
2019 doesn't resolve ordinary/extraordinary separately, so this is the most honest reading of the
available data, not an approximation of known anisotropy -- same treatment implicitly already used
throughout the row 5 Loaded-family strip configs (isotropic by construction there, no o/e split
exists in that code path at all). The substrate stays properly anisotropic since it's plain AlN,
using this project's own already-resolved AlN_EQ_O/AlN_EQ_E.

Geometry fixed at h_core=350/w_core=400 (the project's established good range, rows 1/2) for this
first pass -- phase 2 adds geometric variants informed by what phase 1 shows and by the user's
fabrication-reality comments (2026-10-16): HexaTech-grade AlN substrate purity for UV
transmission is the real constraint on the "real AlN substrate" option working at all; MOCVD AlN
can be grown high-purity up to ~1um before cracking, relevant if a thin top-side AlN cap (grown
layer) turns out to matter more than the bulk substrate; and a speculative surface-structuring
idea to suppress UV guided modes entirely, not designed yet.
"""

import json
import os

from survey_config import SETTINGS as _BASE_SETTINGS
import geometry as geo

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'materials', 'ScAlN_Baumler2019_sellmeier_fits.json')) as _f:
    _FITS = json.load(_f)['fits']

SETTINGS = _BASE_SETTINGS

H_CORE, W_CORE = 350.0, 400.0

GEOMETRIES = [('ridge', {'h_core': H_CORE, 'w_core': W_CORE,
                         'core_eq_o': fit['emode_equation_real'],
                         'core_eq_e': fit['emode_equation_real'],
                         'substrate_eq_o': geo.AlN_EQ_O, 'substrate_eq_e': geo.AlN_EQ_E})
              for comp, fit in _FITS.items()]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
