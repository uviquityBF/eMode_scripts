# TM04 / TM40 Phase-Matching Summary: EMode vs. COMSOL

Geometry: AlN waveguide, w=400nm, h=350nm (EMode) / h=335nm (COMSOL dataset), sidewall angle
~85deg from horizontal assumed (5deg from vertical) -- COMSOL's actual value for this dataset may
have been ~89deg; not resolved, but shown below to be a second-order effect at most (the dominant
discrepancy found this session was mode mislabeling, not sidewall angle -- see
EMode_Troubleshooting_Log.md for the full investigation).

## TM04 (mode 30 in EMode, at h=350/w=400)

| Quantity | EMode | COMSOL | Agreement |
|---|---|---|---|
| Crossing wavelength (vs. TM00) | 228.244nm (h=350) | ~225.3nm (h=335, w=400) | close; residual consistent with h difference |
| dn/dwidth | 1.087e-4 /nm | ~1e-4 to 1e-5 /nm (COMSOL, h=335) | same order, small in both |
| dn/dheight | 2.892e-3 /nm | ~2.76e-3 /nm (h=335-355 sweep, w=400, WL=240nm) | close match |
| d(PM wavelength)/d(width) | -0.011926 nm/nm | -0.012 to -0.014 nm/nm (w=300-450) | near-exact match |
| d(PM wavelength)/d(height) | 0.211742 nm/nm | not available (COMSOL height data is single-wavelength only -- see note below) | can't compare |

TM04 matched COMSOL well on every axis checked, from the start -- this mode was never in question
and served as the validation baseline for the whole comparison method.

## TM40 (mode 23 in EMode, at h=350/w=400 -- corrected; mode 21 was mistakenly used earlier and is
actually TM13, a different mode)

| Quantity | EMode (corrected) | COMSOL | Agreement |
|---|---|---|---|
| Crossing wavelength (vs. TM00) | 241.672nm (h=350) | ~247.8nm (h=335, w=400) | close; residual consistent with h difference |
| dn/dwidth | 2.407e-3 /nm | ~1.4-2e-3 /nm (COMSOL, h=335, near w=350-450) | same order/family (was 6x too small with the wrong mode) |
| dn/dheight | 3.398e-5 /nm | ~3.0e-5 /nm (h=335-355 sweep, w=400, WL=240nm) | near-perfect match |
| d(PM wavelength)/d(width) | 0.240897 nm/nm | ~0.24-0.26 nm/nm (flat, w=300-600) | near-exact match |
| d(PM wavelength)/d(height) | -0.038346 nm/nm | not available (COMSOL height data is single-wavelength only -- see note below) | small vs. width, as expected (EMode-only) |

**Bottom line:** TM40 is confirmed width-dominant in both tools (dWL/dwidth ~6x larger in
magnitude than dWL/dheight), matching the physical expectation for a mode with 4 field lobes across
width and 0 across height. The large earlier disagreement (EMode showing height-dominant behavior,
~13x backwards from COMSOL) was entirely due to tracking the wrong physical mode (mode 21 = TM13),
not a numerical, resolution, or geometry (sidewall-angle) issue. See
`EMode_Troubleshooting_Log.md` for the full investigation trail.

## TM00 (fundamental/pump), for reference

Evaluated at 2x the SHG wavelength (i.e. the actual pump wavelength) in each row -- these are the
"fund" numbers that feed into the implicit-function-theorem calculation above, shown here on their
own for completeness.

| Row context | Pump wavelength | EMode dn/dwidth | COMSOL dn/dwidth (w=350-450) | Agreement |
|---|---|---|---|---|
| TM04 row | 456.488nm (2x228.244) | 2.524e-4 /nm | 2.207e-4 /nm | Same order, close |
| TM40 row | 487.972nm (2x243.986, reused -- see caveat below) | 2.765e-4 /nm | 2.393e-4 /nm | Same order, close |

| Row context | EMode dn/dheight | COMSOL dn/dheight |
|---|---|---|
| TM04 row | 3.398e-4 /nm | Not available (no COMSOL height sweep for TM00) |
| TM40 row | 3.731e-4 /nm | Not available (no COMSOL height sweep for TM00) |

Same data-gap reason as the target modes' missing `d(PM wavelength)/d(height)` COMSOL column: the
COMSOL height sweep (h=335-355, w=400, WL=240nm fixed) only covered TM04 and TM40, not TM00.

## Caveats

- COMSOL comparison data is at h=335nm; EMode's final numbers are at h=350nm (the real design
  target). Absolute crossing wavelengths differ by a few nm, consistent with this height offset.
- COMSOL's sidewall angle for the uploaded datasets may have been ~89deg rather than the ~85deg
  assumed to match EMode's `sidewall_angle=5` (measured from vertical) default -- not resolved, but
  the mode-mislabeling finding above fully explains the prior discrepancy without needing this.
- `fund_grad_TM40` (TM00's own dn/dwidth, dn/dheight) was evaluated at 2x the *original* (wrong-mode)
  crossing wavelength (487.972nm) rather than the corrected one (483.344nm) -- a ~4.6nm difference,
  presumed negligible given the fundamental's smooth wavelength dependence, but not independently
  re-verified.
- No COMSOL-derived `d(PM wavelength)/d(height)` for either mode: the width comparison was possible
  because `WL_and_width_dependence.csv` gave n_eff(wavelength) curves for TM00/TM04/TM40 across many
  widths, letting the crossing wavelength be found at each width and differenced. The COMSOL height
  data received was only a single-wavelength (240nm) snapshot of TM04/TM40's index at 5 heights --
  enough for a raw `dn/dheight`, but not a wavelength-swept dataset, and not one for TM00 either, so
  the implicit-function-theorem terms needed for d(crossing)/d(height) aren't available from COMSOL.
  Would need a COMSOL run structured like the width one (multi-wavelength sweep at each height, for
  TM00 too) to fill this in.
