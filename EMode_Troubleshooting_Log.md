# EMode Troubleshooting Log

Running log of questions and issues from this debugging session, newest first.

**RESOLVED (2026-07-17): the entire TM40 vs. COMSOL discrepancy was mode mislabeling -- mode 21 is
TM13, mode 23 is the real TM40.** Direct `n_eff` readout at the confirmed-correct indices (no
tracking/overlap involved) gives:
```
dn/dwidth  (mode 23, confirmed) = 2.407e-3 /nm   COMSOL: ~1.4-2e-3/nm   (old, wrong mode 21: 4.113e-4/nm)
dn/dheight (mode 23, confirmed) = 3.398e-5 /nm   COMSOL: ~3.0e-5/nm     (old, wrong mode 21: 2.168e-3/nm)
```
dn/dheight is now a near-perfect match to COMSOL; dn/dwidth is the right order of magnitude and
direction (previously 6x too small, now in the same family as COMSOL's range). **The sidewall-angle
and mesh-resolution hypotheses are dropped** -- not needed, the mislabeling explains everything.
This also means `crossing_TM40` (243.986nm) itself is suspect -- it was found via
`find_crossing(..., target_mode_idx=21, ...)`, i.e. searching for where the fundamental crosses
TM13, not TM40. The fact that it happened to land close to COMSOL's real TM40 crossing (~247.8nm at
h=335) is presumably because TM13 and TM40 are close in n_eff near this operating point (consistent
with the whole mislabeling story) -- but the *true* TM40 crossing wavelength, and therefore
`fund_grad_TM40` (evaluated at 2x the crossing wavelength) and the final `wl_grad_TM40`
(dWL/dwidth, dWL/dheight), all need to be redone with `target_mode_idx=23`.

**Next steps:** (1) redo `find_crossing` with `target_mode_idx=23` to get the true TM40 crossing
wavelength; (2) if it shifts meaningfully from 243.986nm, recompute `fund_grad_TM40` at the new
2x-wavelength operating point (cheap, num_modes=6); (3) build `target_grad_TM40_correct` directly
from the already-collected `dn_dwidth`/`dn_dheight` above (no new EMode calls needed -- already
have the numbers); (4) recompute `wl_grad_TM40` via `implicit_wavelength_gradient` and update the
final phase-matching table row.

**CLOSED (2026-07-17): final, corrected TM40 numbers -- matches COMSOL.** Corrected crossing
(`target_mode_idx=23`): **241.672nm** (n_eff=2.03125), vs. the old wrong-mode 243.986nm -- close
enough that `fund_grad_TM40` was reused as-is (evaluated at 2x243.986=487.972nm vs. the corrected
2x241.672=483.344nm, a ~4.6nm difference in the fundamental's operating wavelength, presumed
negligible given the fundamental's smooth/slow wavelength dependence -- not independently verified,
noted as a minor residual approximation). Final result:
```
                    dn/dwidth      dn/dheight
fund (TM00)         2.765e-4/nm    3.731e-4/nm
TM40 (mode 23)      2.407e-3/nm    3.398e-5/nm

d(PM wavelength)/d(width):   0.240897 nm/nm   (COMSOL: ~0.24 nm/nm)   -- near-exact match
d(PM wavelength)/d(height): -0.038346 nm/nm   (old wrong-mode: 0.2305) -- now small vs. width, as expected
```
**The whole TM40 vs. COMSOL discrepancy is resolved: it was mode mislabeling (mode 21 = TM13) from
the very start, not a resolution, sidewall-angle, or solver-accuracy problem.** TM40 is confirmed
width-dominant (`dWL_dwidth` ~6.3x larger in magnitude than `dWL_dheight`), matching both COMSOL and
basic physical intuition (4 lobes across width, 0 across height). Residual open item, low priority:
independently verify the small `fund_grad_TM40` wavelength-mismatch approximation above if this
number needs to be fully rigorous later.

**NEW (2026-07-17): general, repeatable pipeline built -- `General_PhaseMatching_Pipeline.ipynb`.**
Rolls up everything learned this session into a reusable workflow: (1) one upfront visual mode
survey at an anchor geometry (human-in-the-loop, done once), (2) optional auto-scan for other
modes' crossings (`scan_for_crossings` -- 2 sweep calls total, not one per mode index), (3) a
nearest-neighbor mode-index "walk" across an arbitrary target grid (`walk_mode_across_points` --
chains through neighboring points instead of jumping straight from the anchor, since index has been
shown to swing by 7+ over a single 50nm step), (4) `phase_matching_row` at every grid point using
the walked index directly (no further tracking uncertainty). New functions added to
`emode_helpers.py`: `visual_mode_survey`, `walk_mode_across_points`, `scan_for_crossings`. Designed
for a long (hours-OK) unattended run after the one-time visual step. Not yet test-run end-to-end --
next session should do a small-grid smoke test before trusting a big overnight/remote run.
Also wrote `TM04_TM40_Summary.md` -- a standalone summary of final EMode-vs-COMSOL numbers for both
modes, independent of this pipeline notebook.

## Roadmap

**NEW FAILURE MODE FOUND (2026-07-17): editing the .ipynb file on disk while a cell is actively
running can kill EMode.exe.** Claude edited `PhaseMatching_Table.ipynb` directly (raw JSON
read/rewrite, not through the Jupyter UI) while the user had just started running the
`crossing_TM40 = eh.find_crossing(...)` cell -- EMode.exe was killed shortly after. Likely
mechanism: VS Code watches the notebook file for external changes and may reload the in-memory
notebook document when it detects one; if that reload lands mid-execution, it can sever/disrupt the
live kernel<->EMode connection. **Going forward: never write/edit the notebook file while any cell
is actively executing** -- check or ask first. This may retroactively explain some of the earlier
"EMode just crashed" incidents this session, if a notebook edit happened to land during a run.

**CRITICAL CORRECTION (2026-07-17): mode 21 is NOT TM40 -- it's TM13. Mode 23 is TM40.** User's
instinct to visually re-check mode identity (rather than trust overlap()) paid off immediately: at
the exact anchor point used for every TM40 gradient/crossing calculation so far (h=350, w=400,
wl=243.986nm), a quick plot-only re-check (no overlap/track_mode, just `em.plot(mode=X,
component='Ey')` for modes 20/21/22 at each stencil point) showed **mode 21 is visually TM13, and
mode 23 is the true TM40**. This retroactively explains the entire TM40 vs. COMSOL discrepancy
(both the ~14x width-sensitivity underestimate and the ~72x height-sensitivity overestimate) as a
straightforward consequence of tracking the wrong physical mode the whole time -- not a resolution,
sidewall-angle, or solver-accuracy issue. It's also consistent with (and now explains) the earlier
"visual double-check surprise" from 2026-07-16: mode 22 at h=345 scored 98.47% overlap against our
(mistaken) mode-21 TM40 reference while visually being TM13 -- because the reference WAS TM13 all
along, so a high overlap between two things both actually TM13 is exactly what should happen, no
overlap-computation reliability problem after all.

**Invalidates**: `crossing_TM40`, `fund_grad_TM40`, `target_grad_TM40` (both the original and the
clean `d_height=1.0` version), `wl_grad_TM40` (both versions), and every conclusion drawn from them
-- all built on mode 21. The entire TM40 row needs to be redone from scratch with
`target_mode_idx=23`.

**Confirmed indices, all 5 stencil points, at WL=243.986nm (visual, per-point re-check).** Note:
the `h_plus` cell had a labeling bug (header said "h=355" but the code actually computed
`h0 + 15` = 365, not `h0 + 5` = 355 -- COMSOL's 335-355 range isn't symmetric around h0=350, and
the cell wrongly assumed a symmetric +/-15 would land on it). Fixed the cell for future reruns; the
data already collected is still valid, just at h=365 not 355.
```
point     h      w      TM40 mode   TM04 mode
anchor    350    400    23          30
w_minus   350    350    26          25
w_plus    350    450    19          34
h_minus   335    400    22          n/a (not found in scanned range)
h_plus    365    400    23          29
```
TM40's index swings by 7 across the width axis alone (19-26) but is nearly flat across the height
axis checked here (22-23) -- consistent with (and a good independent confirmation of) COMSOL's own
finding that TM40 is width-sensitive and essentially height-flat. TM04's index also moves a lot
(25-34), confirming index instability isn't unique to TM40.

**Big upside: since every index is now visually confirmed (ground truth), the large-step
dn/dwidth/dn/dheight for TM40 can be computed directly** -- solve at each point using its *known*
mode index and read `n_eff` straight off, no `track_mode`/`overlap()` tracking or window-size
guessing needed at all:
- `dn/dwidth = (n_eff(w=450, mode=19) - n_eff(w=350, mode=26)) / 100`
- `dn/dheight = (n_eff(h=365, mode=23) - n_eff(h=335, mode=22)) / 30`

This sidesteps the sidewall-angle and mesh-resolution hypotheses entirely for now -- they're only
relevant if the *correct-mode* numbers still disagree with COMSOL after this recompute.

**Next steps:** (1) run the 4 perturbation-point solves (already effectively done during the visual
check -- just need to read off `n_eff` at the confirmed index instead of/in addition to plotting)
plus the anchor, compute the direct secant slopes above; (2) compare against COMSOL's ~1.4-2e-3/nm
(width) and ~3e-5/nm (height); (3) if they now line up, the whole TM40 mystery was simply mode
mislabeling (mode 21 = TM13) from the start; (4) once confirmed, redo `find_crossing`/
`mode_gradient_width_height`/`phase_matching_row` properly with `target_mode_idx=23` at the anchor.

**FINDING (2026-07-17): decisive, COMSOL-native crossing calculation confirms TM_40's phase-matching
wavelength is ~14x more width-sensitive in COMSOL than in EMode -- TM_04 validates the method by
matching almost exactly.** User provided a cleaner file, `WL_and_width_dependence.csv`, with
n_eff(width) grids for TM_00 (at 2x wavelength), TM_20, TM_40, TM_04 all on the same SHG-wavelength
axis. Computed the phase-matching crossing wavelength directly from this COMSOL data (root of
n_fund(2*wl) - n_target(wl) over the wl grid, per width) -- **no EMode involved at all** -- then
took d(crossing)/d(width):
- **TM_04**: COMSOL gives -0.012 to -0.014 nm/nm (w=300-450) vs. EMode's -0.0119 -- near-perfect
  match. Validates the comparison method and that "TM_04" means the same mode in both tools.
- **TM_40**: COMSOL gives **+0.24 nm/nm**, essentially flat across w=300-600nm (0.239-0.258), vs.
  EMode's **+0.0173** -- same sign, ~14x smaller in EMode. Because COMSOL's own slope barely
  changes across that width range, this can't be explained by curvature/step-size sensitivity --
  it's a real, reproducible disagreement in magnitude, isolated specifically to TM_40.
- Bonus: absolute crossing wavelengths also line up (COMSOL: 247.8nm at w=400,h=335; EMode:
  243.986nm at w=400,h=350) -- residual is consistent with the small h difference, confirming both
  tools' "TM_40" is the same physical mode (resolves open question (c) from the 2026-07-16 entry).
- TM_20 has no crossing in this WL window except at very small widths (150/200nm, outside our
  region of interest) -- consistent with the earlier EMode finding of no TM_20/TM_02 crossing in
  210-250nm.

**Open lead raised by user, not yet tested:** the COMSOL sidewall angle for this dataset may
actually have been **89deg (from horizontal)**, not the 85deg assumed to match our
`sidewall_angle=5` (measured from vertical) default -- i.e. COMSOL's walls may be nearly vertical
(1deg taper) rather than the 5deg taper we've been using. This is an attractive candidate
explanation for why TM_04 (uniform across width, less sensitive to exact wall profile) matches so
well while TM_40 (4 lobes across width, plausibly far more sensitive to the exact sidewall shape)
doesn't. Added a `sidewall_angle` passthrough parameter to `solve_and_identify()` (forwarded to
`setup_waveguide`/`set_core_width`, default unchanged at 5) so this can be tested directly.

**Next (queued, cheap):** re-derive TM_40's `dn/dwidth` with a **larger width step** (w=350 vs 450,
instead of the existing +/-5nm stencil) at h=350, both at `sidewall_angle=5` (current default) and
`sidewall_angle=1` (~89deg-from-horizontal hypothesis) to see whether (a) a bigger step alone
shifts EMode's value meaningfully -- expected not to, since COMSOL's own slope is flat over this
range -- and (b) whether the sidewall angle mismatch can account for some/all of the 14x gap. 4
total `solve_and_identify` calls from the existing h=350,w=400,mode=21 anchor -- cheap, no full
sweep needed.

**FINDING (2026-07-17): COMSOL sheet (h=335nm, dozens of modes, w=300-700, WL=200-300) confirms
TM_40 is strongly width-sensitive in COMSOL, ~3-5x more than EMode currently shows -- and the
comparison method is validated by TM_04/TM_00 landing close to EMode.** User provided a Google
Sheets export (`2025_12___Modal_Index_for_h=335nm...csv`) of COMSOL-computed n_eff. Parsing was
non-trivial: it's laid out as one column-block per width (period of 21 columns, 9 blocks for
w=300-700), and -- crucially -- **mode labels shift row position across blocks** (same rank-by-
n_eff-descending problem we've been fighting in EMode's raw mode index), so extraction has to match
each block's label text directly rather than assume a fixed row per mode. Also found: the w=300
block's data row is shifted one column left of every other block (an export quirk, not physics --
it has an extra WL=200 point the others lack), and the **w=700 column is corrupted for every mode**
(TM_00 shows n_eff~29498, TM_40 shows ~956 -- nonphysical, a real solver/export failure at that
width, not usable).

Computed local dn/dwidth from finite differences on the (usable) data:
- **TM_04** @ WL=210nm, h=335: dn/dwidth decays from 1.14e-4/nm (w=300-350) down to 1.2e-5/nm
  (w=650-700) -- tiny, matches EMode's own TM04 dn/dwidth (1.087e-4/nm at h=350,w=400) well.
- **TM_00 (fund)** @ WL=220nm, h=335: 7.2e-5/nm (w=350-400) down to 1.6e-5/nm -- also small, same
  ballpark as EMode's fund dn/dwidth (2.765e-4/nm).
- **TM_40** @ WL=220nm, h=335: **1.986e-3/nm (w=350-400)**, decaying nonlinearly to 4.3e-4/nm by
  w=600-650 -- an order of magnitude larger near the w=350-450 region than everywhere else, and
  ~3-5x larger than EMode's own TM40 dn/dwidth (4.113e-4/nm, at h=350,w=400,wl=244 -- a different
  h/wl operating point, so not a perfect match, but the TM_04/TM_00 cross-checks landing close makes
  this comparison method trustworthy).

**Reframes the whole discrepancy**: since TM_04 and TM_00 both check out close to EMode, this isn't
a general calibration mismatch between the tools. The specific, real gap is that COMSOL's TM_40
width-sensitivity (~1.4-2e-3/nm near w=400) is roughly the *same order of magnitude* as EMode's own
TM_40 height-sensitivity (2.168e-3/nm) -- suggesting **EMode may be under-estimating TM_40's width-
sensitivity specifically**, not necessarily over-estimating height-sensitivity. Also notable: TM_40's
width-sensitivity is itself strongly nonlinear (drops >4x from w=350 to w=650), so a single-point
linear derivative may be a poor local model here regardless of which tool computes it.

**Decisive next step (not yet run):** compute EMode's own TM_40 dn/dwidth at the SAME operating
point as this COMSOL sheet (h=335nm, wl~220nm, width span e.g. 350-450) to remove the "different
h/wl" confound. If EMode's value jumps toward COMSOL's ~1.5-2e-3/nm there, the discrepancy is
mostly an operating-point/nonlinearity artifact. If it stays near 4e-4/nm, that's a confirmed real
quantitative gap needing deeper investigation. Requires re-identifying TM40's mode index at
h=335,w=400 first (mode index isn't stable across the h=350->335 change) via `solve_and_identify`
from the known h=350,w=400,mode=21 anchor.

**FINDING (2026-07-17): wider search window (`num_modes=50, window=20`) does NOT reliably recover
TM04 tracking at width extremes -- and costs far too much to scale to the full grid.** Retried
h=350, w=300/700 (jumping directly from the w=400 anchor, same anchor wavelength as the overnight
batch) with `sweep_crossing()`. Result after **229 minutes for just these 2 points**:
- w=300: overlap improved from the overnight batch's 0.03 to **0.58/0.64** -- better, but still
  below the 0.8 trust threshold (`trusted=False`).
- w=700: **overlap=0.0033/0.0035**, essentially unchanged from the overnight batch's collapse, and
  the tracked mode index landed at **49 -- the very top of the `num_modes=50` range**. That's a
  ceiling artifact, not a real identification: the true continuation of TM04 is apparently being
  pushed out past index 49 by w=700, so this run couldn't have found it even in principle.
Conclusion: brute-forcing with bigger `num_modes`/`window` doesn't scale -- pushing `num_modes`
higher to chase w=700 would cost even more per point (already ~1.9hr/point here, up from the
overnight batch's much cheaper per-point cost at `num_modes=35`), and w=300's case suggests the
issue isn't just "not enough modes in the search" but real tracking ambiguity (partial overlap,
not near-zero) that a bigger window doesn't resolve either. **Recommendation: switch to the
previously-discussed walking/incremental sweep** (chain through intermediate width steps from the
w=400 anchor, e.g. 400->350->300 and 400->500->600->700, re-tracking at each small step) so mode
index drift per step stays small enough for high-confidence overlap without needing an oversized
search window. Not yet implemented -- awaiting decision.

**FINDING (2026-07-17): TM40 vs. COMSOL discrepancy confirmed real, not a numerical artifact.**
Recomputed `wl_grad_TM40` with the clean `d_height=1.0` derivative (pure arithmetic): `dWL_dwidth`
unchanged at 0.017325, `dWL_dheight` went slightly **up** to 0.230543 (was 0.210233 with the
crossing-contaminated 5nm step) -- moved *away* from, not toward, the COMSOL width-dominant
expectation. TM40's phase-matching wavelength is ~13x more height-sensitive than width-sensitive in
this EMode calculation, cleanly and reproducibly. This is now a real open question (same geometry?
same mode definition? genuine solver difference?), not something explained away by the crossing
issue. Revisit once there's a chance to compare exact COMSOL parameters.

Added `sweep_crossing()` to `emode_helpers.py` -- generalizes the width-only overnight batch to
arbitrary (h,w) target points and any mode, with the same two-overlap-check resilience pattern.
Testing whether `num_modes=50, window=20` (vs the overnight batch's 35/10) recovers tracking at
widths that collapsed to near-zero overlap (250/500/700nm) before committing to the full
h=330-360/w=300-700 grid for TM04 and TM40 that's planned for today.

**PAUSED (2026-07-16 night) -- TM40 mystery deepened, not resolved. Resume here.**
Visually confirmed at h=345 (the `h_minus` point): mode 21 = TM40 (unchanged), mode 22 = **TM13**
(genuinely different mode family, not a close sibling) -- yet `solve_and_identify` gave 98.47%
overlap between them, which is surprising for two visually-distinct mode families. Two explanations
proposed, not yet distinguished: (1) strong hybridization near a real crossing, where the dominant
visual pattern and the overlap integral's verdict can legitimately diverge; (2) something off in the
overlap computation itself in this regime -- more concerning since it's the core mechanism the whole
pipeline relies on.

Re-ran with `d_height=1.0` (was 5.0) to test the "straddling a crossing" theory directly: **this time
both `h_plus` and `h_minus` cleanly tracked mode 21** (overlap 0.9918/0.9999, no more index swap) --
so the crossing-straddling explanation for the *anomaly* is ruled out. But `dn/dheight` did NOT
shrink toward the COMSOL expectation -- it went slightly *up* (2.1675e-3 vs 2.0094e-3 at d_height=5),
still ~5.3x larger than `dn/dwidth` (4.113e-4). **A clean, unambiguous local derivative still shows
TM40 as height-dominant, contradicting independent COMSOL work that says it should be width-dominant.**

**Important clarification from user (don't lose this):** the quantity that actually matters for
comparison is **d(phase-matching wavelength)/d(width) and d(...)/d(height)** -- i.e. `wl_grad`'s
`dWL_dwidth`/`dWL_dheight` -- NOT the raw per-mode `dn/dwidth`/`dn/dheight` we've been debugging.
**First step on resume:** recompute `wl_grad_TM40` using the new clean `dn_dheight=2.1675e-3` (pure
arithmetic via `implicit_wavelength_gradient`, no EMode calls, instant) to get the properly updated
`dWL_dheight` for TM40 before drawing any conclusion against COMSOL -- the old `wl_grad_TM40`
(0.210233) was built from the crossing-contaminated 5nm-step value and is now stale.

**Next steps to consider (not yet decided):** (a) recompute wl_grad_TM40 as above; (b) verify the
COMSOL comparison used the exact same geometry (h=350, w=400) and wavelength (~244nm) -- a different
COMSOL operating point wouldn't actually contradict this result; (c) consider whether "TM40" is
unambiguously the same physical entity in both tools' labeling conventions; (d) investigate whether
overlap() can be fooled between visually-distinct mode families (explanation #2 above), which would
be a more fundamental reliability concern for the whole pipeline.

**FINDING (2026-07-16): TM40's anomalous large `dn/dheight` explained -- straddling a mode
crossing, not a tracking bug.** Independent COMSOL work said TM40 should be width-sensitive, not
height-sensitive, contradicting our measured `dn/dheight=2.009e-3` (~4.9x its own `dn/dwidth`).
Added overlap return values to `mode_gradient_width_height`'s 4 internal perturbation points and
re-ran TM40's gradient: `w_plus`/`w_minus` both cleanly tracked mode 21 (overlap 0.98/0.99), but
`h_plus` tracked mode 21 (overlap 0.96) while **`h_minus` tracked mode 22** (overlap 0.98) -- a real
mode-index swap within just the ±5nm height stencil, i.e. a genuine near-degeneracy/avoided crossing
between TM40 and a neighbor somewhere in h=345-350. The tracking itself worked correctly (found the
true high-overlap continuation at each point); the problem is a central difference computed *across*
that crossing inflates the derivative regardless of correct tracking -- a numerical-differentiation
pitfall distinct from mode-tracking failure. Width axis was clean throughout (both width evaluations
tracked mode 21 consistently). Re-running with `d_height=1.0` (was 5.0) to stay on one side of the
crossing. **Action item:** consider having `mode_gradient_width_height` automatically detect and
warn when `h_plus`/`h_minus` (or `w_plus`/`w_minus`) disagree on mode index, since that's a reliable
signal the derivative is unreliable regardless of overlap values individually.

**MILESTONE (2026-07-16): all four target mode indices identified at h=350, w=400 (real target
geometry).** Full visual survey via `em.plot(mode=X, component='Ey')`, triaged first by
`TE_fraction`/`TM_indices` from a single `solve_modes()` call (avoids the earlier second-`FDM()`
kernel crash). Also incidentally identified: TM00=0, TM10=1, TM01=2, TM11=3, TM12=10, TM30=12,
TM31=16, TM03=17, TM21=9, TM13=20.
```
TM04 = mode 30   (already used for the completed table row)
TM40 = mode 21
TM02 = mode 6
TM20 = mode 4
```
**Next:** build the remaining three table rows (TM00 vs TM40/TM02/TM20) via `phase_matching_row()`.
Since TM40/TM02/TM20 sit at much lower indices than TM04's 30, `num_modes` can likely be reduced
per-mode (e.g. ~10-12 for TM20/TM02, ~27 for TM40, vs. 35 for TM04) to cut runtime on the expensive
gradient step, since solve cost scales with mode count — worth trying before committing to full runs.

**MILESTONE (2026-07-16): moved to h=350 (real target height); height-axis spot-check reveals more
curvature than width.** Tracked TM04 from the h=335 anchor to h=350 via `solve_and_identify` — mode
index happened to stay at 30 (unlike the width=350 test, which shifted 30->28), overlap 0.9097
(confident but more mode evolution than the width test's 0.9385). Ran `find_crossing` cleanly at
h=350: **228.244nm** — exactly matching the original (retroactively-diagnosed-as-h=350) crossing
value from earlier, a good reproducibility confirmation. Linear model predicted 228.555nm (using
`dWL_dheight=0.231648` from the h=335 anchor) — **0.311nm error out of a 3.164nm actual shift
(~9.8% relative error)**, notably worse than the width spot-check's ~1.1% despite a smaller absolute
change (15nm vs 50nm). Concrete, quantified evidence that height has more curvature in its n_eff
dependence than width — supports prioritizing the quadratic (Hessian) extension for the height axis
specifically, if/when built. Both height-axis steps ran clean, no crashes (~5 min + ~5 min).
**Next:** run the fundamental + TM04 gradients at h=350 to complete the real (non-h=335-standin)
first table row, now that h=350 has a clean, correctly-anchored crossing point.

**MILESTONE (2026-07-16): real h=350 table row complete, TM00 vs TM04 (h=350, w=400):**
```
Phase-matching wavelength (SHG side): 228.244 nm
n_eff at crossing: 2.05082
dn/dWL   -- fund: -1.544411e-03/nm   TM04: -1.359859e-02/nm
dn/dwidth -- fund: 2.524087e-04/nm   TM04: 1.086564e-04/nm
dn/dheight-- fund: 3.398009e-04/nm   TM04: 2.892175e-03/nm
d(PM wavelength)/d(width):  -0.011926 nm per nm
d(PM wavelength)/d(height):  0.211742 nm per nm
```
Every crossing-related number exactly matches the original "accidental h=350" run (228.244nm,
n_eff, both dn/dWL) despite an independent session + slightly different wavelength window — strong
confirmation EMode's solver is fully deterministic and the earlier "3.16nm mismatch" really was
just the h=335/350 mixup, nothing else. `d(PM)/d(width)` barely changed between h=335 (-0.011914)
and h=350 (-0.011926, <0.1% shift), but `d(PM)/d(height)` shifted meaningfully (0.231648 -> 0.211742,
~8.6% lower) — since these are the same slope at two nearby heights, this directly gives a **measured
second derivative**: `d²(PM)/d(height)² ≈ (0.2117-0.2316)/15 ≈ -0.0013 per nm²`. Real, quantified
curvature evidence for the quadratic extension, not just a suspicion.

**MILESTONE (2026-07-16): first spot-check of the linear model, at width=350nm (50nm from the
h=335/w=400 anchor) — validated remarkably well.** TM04 tracked from index 30 (at w=400) to index
28 at w=350 via `solve_and_identify` (overlap 0.9385 — lower than the 5nm-step tests' ~0.999+, as
expected for a bigger geometry jump, but still clearly the same continuous mode). Brute-force
crossing search (210-250nm window) at w=350 found **225.704nm**; the linear model (built purely
from the w=400 anchor's gradient, `dWL_dwidth=-0.011914`) predicted **225.676nm** — only **0.029nm
error** (~1.1% of the actual 2.54nm shift from the anchor). Notably, the mode *index* shifted (and
overlap dropped) while the *physical* dispersion curve stayed smooth enough that linear-only still
extrapolated well over this range — a good sign the linear model may hold up further than initially
feared, at least in this direction/range. Both steps ran clean, no crashes (~5 min + ~13 min).
Remaining planned spot-checks per the original plan: width = 250, 500, 700nm.

**MILESTONE (2026-07-16): first complete phase-matching table row, TM00 vs TM04 at (h=335, w=400):**
```
Phase-matching wavelength (SHG side): 228.244 nm
n_eff at crossing: 2.05082
dn/dWL   -- fund: -1.544411e-03/nm   TM04: -1.359859e-02/nm
dn/dwidth -- fund: 2.503775e-04/nm   TM04: 1.067646e-04/nm
dn/dheight-- fund: 3.804437e-04/nm   TM04: 3.172773e-03/nm
d(PM wavelength)/d(width):  -0.011914 nm per nm
d(PM wavelength)/d(height):  0.231648 nm per nm
```
Height is ~20x more sensitive as a phase-match tuning knob than width near this point (TM04's
dn/dheight is ~8x steeper than the fundamental's, while its dn/dwidth is actually *less* steep than
the fundamental's) — a real design insight, not just a pipeline validation. TM04 gradient run took
26.7 min (matched the ~25-30 min estimate), zero crashes — crash-avoidance approach (fresh session
per evaluation + narrow overlap window) continues to hold up reliably at this scale.

**Status (2026-07-16): mode-tracking blocker cleared, unblocked.** Factored the validated
mode-tracking approach into a reusable module (`emode_helpers.py`: `launch_session`, `em_save`,
`setup_waveguide`, `set_core_width`, `solve_modes`, `track_mode`) plus a new driver notebook
(`PhaseMatching_Table.ipynb`). Cross-validated twice against the module functions (widths 395/400,
different runs) — both completed in ~13.5 min with zero crashes, mode correctly tracked via overlap
each time (0.9997-1.0000) despite the raw index landing on 29 or 30 depending on the run (confirms
index instability is real and the overlap-tracker correctly works around it). Also reported the
underlying EMode.exe crash pattern to EMode Photonix support. Added `find_crossing`,
`solve_and_identify`, `mode_gradient_width_height`, `implicit_wavelength_gradient` to
`emode_helpers.py`; `find_crossing` smoke-test added to `PhaseMatching_Table.ipynb`, not yet run.

**Note for later:** the real target height has moved to h_core=350nm; all mode-index confirmation
so far (mode 30 = TM04) was done at h_core=335nm. Given index instability is already proven even
at a *fixed* geometry between separate runs, do NOT assume index 30 is still TM04 at h=350 --
re-confirm via `em.plot()` or `solve_and_identify` against the h=335 anchor before trusting it.
Currently still developing/validating at h=335; move to h=350 once the h=335 pipeline is solid.

**`find_crossing` smoke test passed (2026-07-16):** TM00 vs TM04 at (h=335, w=400), 4.3 min, no
crash. Phase-matching wavelength (SHG side) = 228.244nm, n_eff = 2.05082, dn/dWL fund =
-1.544e-3/nm, dn/dWL TM04 = -1.360e-2/nm (~9x steeper, physically reasonable for a higher-order
mode). Matches the range the original brute-force notebook sweep found. Next: run
`mode_gradient_width_height` for both modes (~45-60 min estimated) + `implicit_wavelength_gradient`
to complete one full table row. Fundamental-only sanity check queued (`PhaseMatching_Table.ipynb`
cell `30634475`) before committing to the full run.

**EMode support responded (2026-07-16), confirms our own finding: likely a memory limitation.**
Suggested: (1) `verbose=True` + env var `EMODE_LOG_SECRET` (value in the support email, not
reproduced here — see git note below) for extra debug output, to send back to them for
confirmation; (2) `priority='pH'` (they don't expect much effect); (3) increase virtual memory —
checked this machine: 31.5GB RAM, page file currently **auto-managed** at a 4.75GB base size,
757GB free disk. Recommended switching to a larger **fixed** page file size (auto-managed can
under-provision against a sudden spike). Not yet applied — pending user confirmation of exact
size. Threaded a `verbose` parameter through `emode_helpers.py` (`launch_session`,
`solve_and_identify`, `find_crossing`, `mode_gradient_width_height`) so the debug flag can be used
on the next expensive run.
**Note:** don't hardcode the `EMODE_LOG_SECRET` value into any file in this repo (it's a debug
secret from a vendor support email) — set it via `os.environ[...]` in a notebook cell at runtime
instead, so it isn't committed to git history.

**Parked:** setting up VS Code + Claude Code on a second dedicated simulation computer (accessed
via AnyDesk) — someone else is currently using that machine. Plan when resumed: install VS Code +
Node.js + `npm install -g @anthropic-ai/claude-code` there (first-time CLI install), clone this
repo onto it so a fresh session there has the accumulated context via these log files, and
replicate the `UVPY_venv` Python environment (offered to generate a `requirements.txt` from this
machine's venv, not yet done).

**Goal:** a script that takes only material index data + geometry as input and produces, for each
mode pair (TM00 vs. each of TM04, TM40, TM02, TM20): the phase-matching point (n_eff, wavelength),
the slope of n_eff vs. wavelength/width/height for both modes at that point, and the dependence of
the phase-matching wavelength itself on width and height — tabulated across all pairs. Wavelengths of
interest are constrained to 210-250nm. Width is the primary axis of interest (wide range), height
secondary.

**Math approach (agreed):** the phase-matching wavelength `WL*(w,h)` is defined implicitly by
`F(WL,w,h) = n_A(WL,w,h) - n_B(WL,w,h) = 0`. First-order sensitivities come from the standard
implicit-function-theorem gradient (`g_w = -F_w/F_WL`, etc.) — no brute-force re-sweeping needed.
**Two levels of model, by design:**
1. **Linear-only** (fast): just the gradient terms above. Intended as the primary tool for exploring
   the wide width range quickly.
2. **Quadratic** (slower): adds the full Hessian of `F` (all 2nd partials incl. WL-w/WL-h cross terms)
   via a ~19-point finite-difference stencil (~38 FDM solves per mode pair), combined into
   `g_ww, g_wh, g_hh` via the implicit-function 2nd-order formulas. More accurate locally, still not
   valid for large excursions.

**Validation strategy (agreed):** neither model extrapolates reliably over large width changes (this
system already shows mode hybridization/near-degeneracy around width 395-400nm — see the resolved
overlap-indexing issue below). Plan: use the fast linear model as the primary exploration tool, and
**spot-check it against direct brute-force crossing searches at width = 250, 350, 500, 700nm** to see
how far it can be trusted before needing a new anchor point (piecewise approach).

**Deferred further ("dream world", explicitly not now):** a separate tool that computes and stores
the full surface `n = f(WL, width, height)` per mode over a large domain, then reports intersections
on demand anywhere in that domain — a different, denser-sampling tool, not an extension of the
implicit-differentiation approach above.

**Blocker:** this is paused until the mode-tracking reliability + EMode.exe stability-under-repeated-calls
issue (open issue directly below) is resolved, since every derivative evaluation above depends on
correctly re-identifying the same physical mode as parameters shift.

## Open issues

- **EMode.exe appears to die/crash under sustained repeated computation, independent of sleep.**
  2026-07-16: ran a trimmed-down version of the width-loop mode-tracking test (2 widths, single FDM
  solve + 35 `overlap()` calls each, no wavelength sweeps) specifically to avoid the sleep issue.
  Machine was NOT closed this time (user stayed at it), though screen may have locked/dimmed at some
  point. Crashed anyway after ~27 min, ~7 min into the second width's batch of 35 `overlap()` calls —
  `ConnectionError: connection interrupted? expected 4 bytes, but only got 0` (clean EOF, not a reset),
  `EMode.exe` process gone afterward, no new output log written. Screen lock/dim alone normally
  doesn't kill background processes on Windows, so this looks like a **real EMode.exe stability
  issue under sustained repeated calls** (possibly a memory leak across many `overlap()` calls),
  separate from the confirmed sleep-kill issue below — though not 100% certain since the exact
  screen/power state during the run wasn't confirmed.
  - **Mitigation plan (in progress):** (1) narrow the overlap search to a small window around the
    previous width's matched index (e.g. ±5) instead of scanning all 35 candidates every time —
    cuts `overlap()` call volume ~7x; (2) relaunch `em` fresh (`clear='all'`) between widths so a
    crash only costs one width's worth of work instead of the whole loop.
  - Also still open/unfixed: `em.save(...)` shadowing bug and `mode_order` sweep crash haven't been
    proliferated to other scripts yet (`AlN_2D_3_sweep.ipynb`, `3b/3c_sweep_wTrack` notebooks,
    `AlN_Uviquity.py`) — see Resolved issues below for the fixes to replicate.

- **Recurring: "Connecting to kernel: UVPY_venv (...)" hangs on kernel startup.** Happened at least
  twice now (opening `AlN_2D_3_overlap.ipynb` on 2026-07-14, then `AlN_2D_4_sweep.ipynb` on
  2026-07-15) — not specific to one notebook. Occurs *before* any code (or EMode) runs, so it's a
  VS Code Jupyter extension issue, not an EMode/emodeconnection issue.
  - **Workaround (works every time so far):** Command Palette (`Ctrl+Shift+P`) -> "Developer: Reload Window".
  - **Suspected trigger:** happens when multiple notebook kernels are already alive at once — both
    times, 1-2 other kernels (~1.5-3 min old) were still running when the new one got stuck
    connecting. Each kernel spawns 2 `python.exe` processes (`ipykernel_launcher`), so kernel count
    doubles in the process list quickly if old notebooks aren't shut down.
  - **Mitigation to try:** close/shut down kernels for notebooks you're not actively using —
    Command Palette -> "Jupyter: Shut Down Kernel" (or just close the notebook tab) — before opening
    a new one, to see if that reduces how often this happens.
  - Not yet root-caused (nothing conclusive found in Application/System event logs); logging
    frequency here to look for a pattern.

## Resolved issues

- **Confirmed `overlap()`'s `mode_a`/`mode_b` indexing is self-consistent with `plot()`'s `mode=`
  indexing** (0-indexed, same convention throughout). Direct diagnostic: labeled width=400 and
  width=395 profiles explicitly and compared `overlap(mode_a=30, mode_b=30)` = **0.9998** (near-
  perfect, confirms mode 30 = TM04 unchanged at both widths) vs `overlap(mode_a=30, mode_b=31)` =
  **0.0000** (orthogonal, confirms TM04 and TE40/TM50 are genuinely distinct mode families, not
  near-degenerate). This proves the original width-loop's anomalous result (matching width=395's
  mode 31 to width=400's mode 30 at only ~0.7355 overlap) was **not** an indexing bug and not a
  logic bug in the tracking code — the approach and code are sound. Most likely explanation: the
  original 71-minute run had already accumulated a huge amount of computation by that point and was
  probably already degrading toward the crash that ended it (see the sustained-computation
  instability issue above, still open).

- **`EModeError('EMode failed to launch.')` / `ConnectionResetError` returned after a machine sleep
  killed a running EMode.exe mid-session** (during the 71-minute width-sweep run in
  `AlN_2D_4_sweep.ipynb` — the machine went to sleep, which killed `EMode.exe` without a clean
  `close()`). Relaunching afterward (even via `Developer: Reload Window` + fresh kernel) kept failing
  with "No licenses are available." even though no `EMode.exe` process was running — the license
  manager still considered the crashed session(s) active since they never checked in cleanly.
  **Root cause confirmed via CLI repro: 15 stale/orphaned sessions had piled up** (accumulated from
  this and earlier restarts across the whole troubleshooting session). **Fix: launch with
  `clear='all'`** (`emc.EMode(..., clear='all')`) once to clear the backlog — do NOT make this a
  permanent default, since it kills *any* other live EMode session on the machine, including ones in
  other notebooks you might have open.
  - **Prevention:** disabled Windows sleep on AC power (`powercfg /change standby-timeout-ac 0`) so
    long unattended runs don't get killed this way again. Note this only covers AC power, not battery.

- **`em.save(...)` raised `TypeError: 'bool' object is not callable`** (`AlN_2D_4_sweep.ipynb`, cells
  `cb343d89`/`57ad2d0e`). Root cause: `EMode.__init__` has a `save: bool` constructor param (default
  `True`) stored as `self.save` (emodeconnection.py:131) — a real instance attribute. Since
  `emodeconnection`'s `EMode.__getattr__` (the mechanism that forwards `em.<name>(...)` calls to the
  backend as `EM_<name>`) only fires when normal attribute lookup *fails*, `em.save` resolves to that
  bool instead of falling through to `__getattr__`, so `em.save(...)` tries to call `True(...)`. This
  is a naming collision in the library itself (between the constructor's save-on-close flag and the
  documented remote `save()` function) — will break `em.save(...)` in *any* notebook on this package
  version, not just this one. **Fix: call `em.call("EM_save", simulation_name=..., ...)` directly** —
  `call()` is a real bound method, not intercepted, so it bypasses the shadowing. Same applies to
  `AlN_2D_3_sweep.ipynb`, `AlN_2D_3b/3c_sweep_wTrack.ipynb`, `AlN_Uviquity.py`, and any other script
  calling `em.save(...)` — not yet fixed in those, planned for later.

- **`em.sweep(..., result=['effective_index','mode_order'])` raised `EModeError('unexpectected exception')`**
  (`AlN_2D_4_sweep.ipynb`, cells `cb343d89`/`57ad2d0e`). Bisected via direct reproduction: sweep
  works fine with `result=['effective_index']` alone; adding `'mode_order'` crashes the EMode
  backend on this sweep regardless of `num_modes` (tested both 2 and 10 — both fail identically).
  `mode_order` isn't actually used downstream (the phase-matching cell only reads
  `data['effective_index']`), and even in the working `AlN_2D_3_sweep.ipynb` it only ever returned
  `None`. **Fix: dropped `'mode_order'` from the `result` list in both sweep calls** — this appears
  to be a backend-side bug/limitation with `mode_order`, not something fixable from the Python side.
  If mode tracking across a sweep is ever needed, use the standalone `em.mode_order()` function
  (see [EMode_Function_Reference.md](EMode_Function_Reference.md)) instead of `sweep()`'s bundled
  result option.

- **"Set Up Simulation" cell appeared to hang** (`AlN_2D_3_overlap.ipynb`, cell `c7e84ab1`): not a
  real hang — `em.plot()` opens a native "EMode Plot" GUI window that was hidden behind VS Code /
  off-screen, waiting for interaction. Alt-Tab (or check the taskbar) to find it.

- **Kernel stuck on "Connecting to kernel"** when opening a second notebook (`AlN_2D_3_overlap.ipynb`)
  while `test.ipynb`'s kernel was alive. Fixed by Command Palette (`Ctrl+Shift+P`) -> "Developer: Reload Window".
- **`em = emc.EMode` missing parentheses** in cell `2bb54c8c` of `AlN_2D_3_overlap.ipynb` — assigned
  the class itself instead of an instance, causing downstream `AttributeError`/`TypeError`. Fixed to
  `em = emc.EMode()`.
- **`EMode() failed to launch` / `ConnectionResetError`** on first attempts in `test.ipynb`. Root cause
  was a transient failure — a direct command-line reproduction with the same venv/save_path succeeded
  immediately, confirming the EMode install and license were fine. Fixed by restarting the kernel.
- **Cell "just loops" / stays busy forever with no output**: caused by `emodeconnection`'s socket client
  blocking on `sock.recv()` with no timeout (`emodeclient.py`) combined with a leftover custom
  `SIGINT`/`SIGTERM` handler registered by a previously-failed `EMode()` call — interrupting doesn't
  help because the handler itself can block. Fix: restart the kernel (not just interrupt).

## Q&A

- **"What is the Command Palette?"** — VS Code's searchable command menu, opened with `Ctrl+Shift+P`.
  Type a command name (e.g. "Jupyter: Restart Kernel", "Developer: Reload Window") and press Enter.
- **"Do you have EMode's full documentation?"** — Not built in, and the installed `emodeconnection`
  package has no docstrings for simulation functions (they're dynamically forwarded to `EMode.exe`
  via `__getattr__`). Pulled the real reference from https://docs.emodephotonix.com/ instead — see
  [EMode_Function_Reference.md](EMode_Function_Reference.md).
