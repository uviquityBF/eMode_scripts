# SHG Mode Survey — Plan

Status (2026-10-05): Step 1 and Step 1b implemented for the `ridge` family and trial-run; Step 2's
`loaded` family implemented, geometry-verified, and both its scattering loss (an EMode-version
bug on this machine, fixed by updating to v1.0.4) and bulk SH-absorption loss (TiO2 etc., wired as
a post-solve perturbation after EMode-side approaches proved to be dead ends) are now trustworthy.
First full `loaded` sweep (`loaded_sweep1`, TiO2 strip) ran overnight: much higher lossless NCE
than `ridge`, but loss-limited peak efficiency collapses ~40,000x below `ridge`'s best once real
TiO2 absorption is included -- TiO2 looks like the wrong strip material, not just a materials-data
gap. User review of the field plots then caught a second issue: most of that sweep's top-NCE
crossings (81% of refined, 100% in `loaded_smoke`) turned out to be simulation-window artifacts
(box modes mimicking confined ones), not real. Fixed both where it's reported
(`shg_physics.lateral_edge_ratio`, `summarize_run.py`) and at the source: `sh_scan()` now screens
for this before deciding what to refine, so `refine_top_n`'s budget goes to real candidates.
Re-ran the full sweep with the fix active: **98.2% of all screened crossings across the family
turn out window-limited**, not just the smoke-test geometry's ~99% -- but the corrected headline
NCE is unchanged at 159 %/W/cm^2 (TM00->TM05?, h_s=150/w_s=1000), confirming the fix improves
efficiency/coverage without changing the physics conclusion. `ridge`'s older committed results have
since been re-verified clean against this check (0 window-limited across `trial_grid` +
`wide_window`). A third family, `hybrid` (AlN core embedded in a SiNx shell, adapting Honda et al.
2025's TM00->TM20 mechanism to this project's UV band), is now implemented, geometry-verified, and
surveyed across 52 geometries total (three sweeps, 23546 crossings) -- **but a geometry-construction
bug (`em.shape()`'s default `position` auto-stacks a new shape on top of the last one; `Hybrid.build()`
never set it) meant the AlN core was never actually embedded in the SiNx shell in any of those 52
geometries, just stacked on top of it.** Found and fixed 2026-10-10 (see "Implementation status &
findings", same-day entry). Every `hybrid` number reported before that fix -- all three sweeps'
headlines, the "no TM00->TM20 anywhere" finding, the sub-metric breakdown artifact -- describes a
structure that was never the one intended, not the Honda et al. mechanism. Awaiting direction on
re-running the sweep campaign under the corrected geometry. Builds on `loss_vs_dimensions/` and
borrows from `phase_matching_pipeline/`.

## Goal

For a given waveguide geometry, survey **all** pump-mode / SH-mode combinations that could give
useful SHG with an SH wavelength in a user-set window (default 215–235 nm), and rank them.
Two families of outcome are of interest:

1. **Guided-to-guided phase matching**: e.g. TM00 → TM02/TM20 (hoped to overlap better than the
   current TM00 → TM04/TM40), or a higher pump mode (e.g. TM10) → some SH mode.
2. **Radiative SH (Cerenkov / leaky / slab-coupled)**: SH that leaves the waveguide rather than
   propagating in it ("Mechanism 2" in the Engineered Channel deck, slides 57–69). These are of
   value and must be flagged and quantified, not discarded.

## Conventions

- **TMmn / TEmn: m = lateral nodes, n = vertical nodes.**
- Coordinates as in EMode: x lateral, y vertical, z propagation. AlN c-axis is **y** (the
  anisotropic material is `[n_o, n_e, n_o]`), so d33 couples Ey·Ey → Py.
- Wavelengths: λ_SH in the survey window, λ_pump = 2·λ_SH.

## Project phases

### Step 1 — full per-geometry evaluation, existing ridge geometry only

For one geometry (the current trapezoidal AlN ridge on sapphire, SiO2 top clad):

- **(a) Pump modes.** Lowest N_pump modes (user-set, default 3) at λ_pump. TM by default; TE
  optional (needed for d31/d15 channels, see tensor table). Loss per mode as in
  `loss_vs_dimensions` (EMode-native `em.scattering()` + post-processed absorption), plus
  leakage loss from PML boundaries.
- **(b) SH modes.** N_SH modes (user-set, 5–10+) found by **n_eff window**, not by index:
  solve with `max_effective_index` set just above the pump n_eff so only SH modes that could
  phase-match are returned. Optionally extend the window below the highest cladding/substrate
  index to include **leaky** SH modes (PML on; filter out PML-box spurious modes by
  near-core field fraction).
- **(c) Phase-matching scan.** Sweep λ_SH across the window; track each SH mode step-to-step by
  overlap (reuse the `walk_mode_across_points` idea — raw indices reshuffle). Record a match if
  n_eff,pump(2λ) − Re n_eff,SH(λ) changes sign; refine the crossing. No match → logged as
  "no phase match in window".
- **(d) For every match:** full-tensor nonlinear overlap, effective areas of pump and SH mode,
  normalized conversion efficiency (NCE, %/W/cm²), SH-mode loss, pump loss, L_opt and peak
  achievable efficiency (see "Efficiency with loss"). SH mode labelled after the fact by
  lobe/node counting, with TE/TM fraction.
- **(e) Cerenkov / radiation flag per pump mode** (no extra solves): for **every material
  region** in the stack, check n_region(λ_SH) > n_eff,pump; report the Cerenkov angle
  θ = acos(n_eff,pump / n_region) and whether that region is **semi-infinite/bulk** (true
  radiation, e.g. thick AlN substrate) or a **finite layer** (SH couples into slab modes and
  spreads laterally — still off the waveguide, but extraction is a separate problem).
- **Symmetry pre-filter** (skip, but log as "symmetry-forbidden"): in an x-mirror-symmetric
  structure the SH mode must be x-even (even m), for **every** pump mode and every tensor
  component (pump⊗pump is always in the even class; wurtzite with c ∥ y is x-mirror
  symmetric). Numerical residue (~1e-6) from a symmetric structure is reported as forbidden,
  not as a value. No vertical selection rule (substrate breaks y-symmetry). The rule is
  **only valid for symmetric geometries** — asymmetric ones (offset loading strip, unequal
  sidewalls, tilted c-axis) must disable it.
- **TM-only filter is a setting**: on by default for guided→guided; off for radiative/leaky and
  whenever TE pumps are enabled.
- **Ranking**: by NCE and separately by loss-limited peak efficiency; always also report raw
  overlap and both effective areas.

### Step 1b — Cerenkov radiation module (driven 2D solve)

Pure post-processing of exported pump fields, no EMode calls:

1. Build P_NL(x, y) at 2ω from the pump field (Ex, Ey, Ez) and each region's d-tensor.
2. Solve the **driven** vector wave equation on the cross-section,
   ∇×∇×E − k0²ε(x,y)E = μ0ω²P_NL, with the axial wavevector fixed at k_z = 2β_pump
   (∂z → i·k_z), ε at λ_SH (complex, so SH absorption is included), and stretched-coordinate
   PML on all sides. Sparse FDFD (Yee grid) with scipy.
3. Radiated SH power per unit length = Poynting flux through a contour just inside the PML;
   cross-check with the source work −½ Re ∫ E*·J dA. Output: Cerenkov conversion rate
   κ_C = (dP_SH/dz)/P_pump² [%/W/cm]. Total over length with pump loss:
   P_SH(L) = κ_C·P_p0²·(1 − e^(−2α_p L))/(2α_p) — linear in L, unlike L² for guided.
4. Flux decomposition by direction (into substrate / into top clad / laterally into slab) so
   the bulk-vs-slab distinction is quantitative.
5. **Validation**: analytic Cerenkov SHG from a slab waveguide; then the Engineered Channel
   deck geometries (slides 63–68). Note: if a *guided* SH mode lies at k_z, the driven solve
   resonates — that is the guided phase-matched case and belongs to Step 1, so the module
   should warn when it detects it.

Rationale for driven solve over summing many leaky modes (deck slide 62, ~900 COMSOL modes):
leaky modes don't normalize cleanly and the sum converges slowly; the driven solve computes the
projection onto the whole radiation continuum directly.

### Step 2 — geometry families + sweep wrapper

Wrap Steps 1/1b in a sweep over geometry families. Candidate families:
- rib (partial etch), loaded strip, rib/loaded hybrid (etch depth 0 → loaded, no strip → rib)
- AlN / AlScN / AlN tri-layer on sapphire (deck slides 63–67)
- AlScN ridge on thick AlN, SiO2 top clad (deck slide 68)
Exact parameterization TBD — waiting on colleague's slides.

## Geometry interface (decided now so Step 2 doesn't rewrite Step 1)

- A geometry = `family` name + `params` dict. A family's **builder** function:
  - creates the EMode shapes/materials for a session;
  - returns metadata the physics needs: which regions are χ(2)-active and their d-tensors;
    region masks / boundary definitions for the absorption & scattering models; whether the
    structure is x-mirror-symmetric; bulk vs finite extent of each region (for the Cerenkov flag).
- Step 1 implements one family: `ridge` (current trapezoid: h_core, w_core, sidewall_angle,
  substrate/topclad materials & thicknesses).
- Results rows store `family`, `params` (JSON), and a **fingerprint** = hash of family + params +
  material dispersion strings + d-tensors + solver settings. On resume, rows whose fingerprint
  doesn't match current inputs are treated as not done (closes, for this pipeline, the
  "fresh-run versioning" gap noted in CLAUDE.md).
- Checkpoint/resume as in the existing pipelines: append-per-result CSV + per-mode field exports
  (.npz), so a transient EMode failure costs one point.

## Efficiency with loss

Power-loss coefficients α_p (pump), α_s (SH); phase-matched, undepleted pump:

  P_SH(L) = η_norm · P_p² · L_eff²,  L_eff = e^(−α_s L/2) · (e^(ΔL) − 1)/Δ,  Δ = α_s/2 − α_p

(L_eff → L when lossless.) Report η_norm (NCE), L_opt, and peak η_norm·L_eff,max².

## SH-wavelength loss model

1. **Bulk absorption**: complex index n + ik in EMode at λ_SH → modal absorption returned by
   the solver. Covers TiO2 strips (strongly absorbing — accepted, must enter efficiency), AlN's
   own Urbach tail near its ~6.0–6.1 eV edge, and ScAlN/AlGaN band tails.
2. **Defect/interface absorption**: reuse `absorption_model.py` machinery with UV α0 values
   (see `loss_vs_dimensions/docs/AlN_Absorption_Literature_Review.docx`).
3. **Roughness scattering**: EMode-native `em.scattering()` on the SH mode. The adapted
   Payne–Lacey model (calibrated only for TM00 at 450 nm) is a cross-check only.

## Materials

| Material | Role | Status |
|---|---|---|
| AlN (o/e Sellmeier, as in `loss_vs_dimensions`) | core / χ(2) | have n; k near 215 nm needed |
| Sapphire (Al2O3) | substrate | EMode built-in; cross-check: 1.871 @ 225 nm (deck sheet Sellmeier) |
| SiO2 | top clad | EMode built-in |
| ScAlN (various Sc) | core / strip / χ(2) | n from Bäumler 2019 (digitized in `2025_12_cerenkov` sheet); **k needed** |
| AlGaN | strip | **n, k needed** (user to supply) |
| TiO2 | loading strip | **n, k needed**; absorbs strongly at λ_SH (accepted) |

Caution: Bäumler 17% Sc index rises to ~2.96 at 225 nm vs ~2.52 for AlN — likely near the
absorption edge; k is essential for high-Sc designs even in the Cerenkov case (SH must cross
the core to escape).

## χ(2) tensor (wurtzite, 6mm; c ∥ y)

Nonzero: d33; d31 = d32; d15 = d24. P_y = ε0[d31(Ex²+Ez²) + d33 Ey²], P_x = 2ε0 d15 Ex Ey,
P_z = 2ε0 d15 Ez Ey (contracted-notation with c → y). Kleinman symmetry (d15 = d31) assumed
unless data says otherwise — questionable close to the band edge (λ_SH ≈ 215–235 nm), so
treat d15 as a separate input.

| Material | d33 (pm/V) | d31 (pm/V) | Source |
|---|---|---|---|
| AlN, bulk | 4.3 ± 0.3 (@1030 nm) | d33/(45 ± 5) ≈ 0.1 | Majkić 2017, pssb 201700077 |
| AlN (working value) | 4.7 | ~0.1 | user's current value |
| AlN, sputter film | 5.1 ± 0.4 | 0.07 | Yoshioka 2021 (APL Mater. 9, 101104) |
| ScAlN sputter, 10/20/28/36% Sc | 15.8 / 42.5 / 46.9 / 62.3 | 0.84 / 2.4 / 3.4 / 4.5 | Yoshioka 2021 |
| ScAlN MBE (ref. 22 in Lee), 10/20/30% | 1.3 / 0.0±3.5 / 0.3±1.3 | 0.84 / 1.81 / 2.59 | via Lee 2026 Table I |
| ScAlN MBE on sapphire, 10/15/20/25% | −2.45±1.9 / 5.1±1.9 / −3.1±4.6 / 3.2±1.2 | 1.61 / 3.27 / 4.93 / 1.60 | Lee et al., arXiv 2607.14590 (2026) |

Notes: literature **disagrees** on ScAlN d33 (sputtered: huge enhancement; MBE: none, but large
d31 enhancement). Lee et al. argue simplified analyses may overestimate d33 in high-index films.
Implication for the survey: d-tensors must be per-material inputs, and **TE-pump → TM-SH via
d31** (P_y = d31·Ex²) becomes interesting in ScAlN, where d31 ≈ 5 pm/V ≈ AlN's d33. In pure
AlN, d31 channels are ~(0.1/4.7)² ≈ 5e-4 of d33 — not competitive.

## Implementation notes / risks

- `emode_helpers.setup_waveguide` uses `boundary_condition='TM'` — needs PML (or a settable
  boundary) for TE pumps, leakage loss and leaky SH modes.
- Number of SH modes at 215–235 nm is large; the n_eff window is what keeps (b) tractable.
- Field exports for pump and SH must share a grid (same window/resolution) for the overlap; the
  driven solve needs ε(x, y) at λ_SH from the geometry builder (or EMode's permittivity export).
- Shared code: currently `loss_vs_dimensions` imports `emode_helpers` via a `sys.path` entry to
  `../phase_matching_pipeline/`; this pipeline will do the same for now. Consolidating into a
  `common/` folder is deferred until Step 1 shows which loss/export code is genuinely shared
  (the loss models need generalizing to arbitrary region masks anyway), to avoid touching the
  working notebooks twice.

## Open items

- [x] Geometry parameterization (colleague's slides) — `loaded` family implemented
  (`geometry.Loaded`, John Carlson deck slides 10-15) and mask/EMode-plot conventions verified
  2026-10-04 (see findings below). Other Step 2 families (rib, AlN/AlScN/AlN tri-layer, AlScN
  ridge on AlN) still TBD.
- [ ] k(λ) for AlN near 215 nm, AlGaN. ScAlN done (Bäumler 2019 digitized + damped-Sellmeier fit,
  `materials/fit_baumler_sellmeier.py`) but **not yet wired into any geometry/survey_config** --
  `d_tensors_pm`/material equations still only define AlN. TiO2 done the same way
  (`materials/fit_tio2_sellmeier.py`, Siefke et al. 2016) and **is** fully wired into
  `survey_config_loaded.py` (both n via `strip_eq` and loss via `strip_loss_eq`, see the
  bulk-absorption item below for how the loss actually reaches results).

  **AlN k candidates found 2026-10-04 (research only -- NOT wired in, needs a user decision, see
  "why" below):**
  | source | material quality | k near 215-235 nm | alpha near 225 nm |
  |---|---|---|---|
  | AlN boule/crystal patents (e.g. "Aluminum nitride crystals having low Urbach energy...") | ultra-pure bulk single crystal | ~1-5e-5 (from alpha < 10-30 cm^-1 claims) | ~15-30 cm^-1 |
  | Beliaev et al. 2021, J. Vac. Sci. Technol. A 39, 043408 -- refractiveindex.info `main/AlN/nk/Beliaev1.yml`, CC0, tabulated 211-1690 nm | 303 nm reactive-sputtered film | ~0.045-0.12 | ~25000-45000 cm^-1 |
  | (unverified -- found only as a search-engine summary, not an independently fetched citation) MOCVD epitaxial AlN on sapphire at 233 nm | epitaxial thin film | ~0.005-0.05 | ~2800-28000 cm^-1 |
  | Baumler et al. 2019 (J. Appl. Phys. 126, 045715) -- the same digitized source as `ScAlN_Baumler2019_sellmeier_fits.json`'s 0% Sc fit, i.e. *already in this repo* | thin film (growth method per that paper, not re-verified here) | 0.0058-0.019 (225/215 nm; fit from only 3 raw digitized UV samples -- sparse) | ~1.4-4.8 dB/um (~1.4-4.8e6 dB/m) |

  **2026-10-12**: found while checking an idea of the user's -- this falls *within* the existing
  range, close to the MOCVD-epitaxial estimate, not a new extreme. User also has (b) a repo of the
  team's own measured AlN ellipsometry data, not yet shared/pulled in -- likely the most directly
  relevant source once available, pending the pointer.

  These span ~4 orders of magnitude in k, entirely driven by material quality/growth method
  (single crystal vs epitaxial vs sputtered/amorphous) -- not a case where one literature value is
  simply "more accurate" than another. Picking wrong would scale pump-band bulk absorption by up
  to 10,000x. This pipeline's existing `pump_absorption_mechanisms` (interface-localized
  dislocation/impurity terms) implicitly assume a relatively clean *bulk* AlN with loss
  concentrated at growth interfaces, which points away from the sputtered/amorphous end -- but
  deciding between single-crystal-like and MOCVD-epitaxial-like values needs to know the actual
  AlN growth process this project's wafers use, which isn't in this repo. Left unresolved rather
  than guessed; the Beliaev dataset is the most concretely verified of the three (real tabulated
  data, CC0, same `fit_tio2_sellmeier.py`-style pipeline would apply) if a conservative
  (upper-bound) estimate is wanted meanwhile.
- [x] **`native_scattering()` NaN for every `loaded`-family mode was an EMode version bug, not a
  code/geometry bug.** This desktop's EMode.exe was v1.0.0.0 (`get_shape()` failed with 'NoneType'
  object is not subscriptable after `em.scattering()` succeeded -- reproduced even for `ridge`/
  `core` via the real `survey.py` code path, so it was never `loaded`-specific, just not noticed
  for `ridge` because that family's committed runs predate this machine / were run on the laptop,
  which already had v1.0.4). Updating this desktop to **v1.0.4 fixed it**: both `ridge`/`core` and
  `loaded`/`strip` scattering confirmed working 2026-10-04. A v1.0.5 is also available
  (emodephotonix.com/downloads) but not yet tried.
- [x] **Bulk-absorption loss (SH-wavelength loss model item 1) is now wired up, as a post-solve
  perturbation, not via EMode re-solve.** EMode-side options were dead ends, confirmed across
  v1.0.0/1.0.4/1.0.5: a complex `refractive_index_equation` crashes `em.FDM()` every time (full
  traceback points at a real defect in EMode's own `numpy_shape_utils.add_scaled`, called from
  `make_tensors` during meshing -- worth reporting to EMode Photonix); `add_material(loss=...)`
  never reaches a plain FDM solve's modal loss at all (confirmed EME-only per EMode's 1.0.5 release
  notes, not a bug for our use case). `shape(loss_dB_per_m=...)` (deprecated in EMode's own
  message) DOES work and is correctly confinement-weighted when read back via `report()` -- but
  feeding it TiO2's large SH-band bulk loss and re-solving was found to corrupt SH-mode
  re-identification at refine time (overlap_shape for a nominally-unchanged crossing dropped from
  0.051 to 0.0036, SH label changed TM165? -> TM183 -- a genuinely different candidate mode got
  matched, not just relabeled). Fixed by computing the loss as a pure first-order-perturbation
  post-solve step instead: `geometry.Loaded.lossy_mask()` (the strip region) +
  `lossy_bulk_loss_dB_per_m()` (the strip material's own bulk alpha(lambda) from `strip_loss_eq`,
  no EMode call at all) and `survey.bulk_absorption_loss()` (confinement Gamma from the
  already-solved lossless mode's own fields, via `shg_physics.power_fraction_in`, times the bulk
  value) -- no re-solve, so mode identification is untouched. Re-ran `loaded_smoke`: every label,
  NCE and overlap_shape now matches the pre-bulk-loss run exactly, confirming the fix.
  `shg_physics.bulk_loss_dB_per_m` (Im(n_eff) -> dB/m) is still unused dead code from the original
  (wrong) approach; keep it for a legitimate future Im(n_eff) source (e.g. PML leakage loss).
- [ ] d15 values (assume Kleinman for now); d-tensor dispersion to 450 → 225 nm.
- [x] Default N_pump, N_SH, λ_SH step, SH n_eff window margins -- set in `survey_config.py`
  (`num_pump_tm=3`, `num_pump_te=2`, `num_sh_modes=30`, `lambda_step=1.0 nm`,
  `sh_window_margin=0.10`) and validated by the `trial_grid`/`wide_window` runs below. **Except**:
  `num_sh_modes=30` is too narrow for the `loaded` family specifically -- every geometry in
  `loaded_sweep1` hit the "SH n_eff window too narrow" warning (21-63 group-steps affected, worst
  for h_s=150), so that family's results may be missing some crossings at the margins (see
  `loaded_sweep1` findings below).
- [ ] **TiO2 is likely the wrong `loaded`-strip material** -- `loaded_sweep1` (first full sweep
  with real TiO2 loss, see findings below) shows it absorbs too strongly at both pump and SH bands
  to be competitive with plain `ridge`, despite much higher lossless NCE. Next experiment: swap the
  strip for a nonlinear, lower-loss material (ScAlN -- Bäumler fit already done, needs
  `strip_chi2`/`d_tensors_pm` wiring and a `strip_eq`/`strip_loss_eq` built the same way as TiO2's)
  instead of (or combined with) iterating on TiO2 geometry parameters.
- [x] **Refine-selection was spending most of its budget on window/box-mode artifacts, not just
  reporting them** -- see "Window/box-mode artifacts" / "Screen-time window/box-mode filtering"
  findings below. User chose screen-time filtering (option 2) over widening the window (option 1).
  `sh_scan()` now computes `lateral_edge_ratio` at screening time (full resolution, same field
  `eta_screen` uses -- no fidelity gap to validate) and `run_geometry()` skips window-limited
  crossings when filling `refine_top_n`. Re-ran `loaded_smoke` clean: only 4 of 317 screened
  crossings were even eligible for refinement. `loaded_sweep1`'s full 8-geometry sweep still needs
  re-running with this active -- its "159 %/W/cm^2 real best" is from report-time filtering only,
  not yet benefiting from the better-targeted refine budget. **Done**: re-ran, headline unchanged
  (159 %/W/cm^2, same crossing, independently re-solved) -- see "`loaded_sweep1` re-run" finding.
  Across the whole family, 98.2% of screened crossings turn out window-limited, not just the
  smoke-test geometry's ~99%.
- [x] **`trial_grid` verified clean against the window/box-mode check** -- see "`ridge` family
  verified clean" finding below. Local `exports/` turned out to be gone (laptop-only, gitignored),
  so this needed a fresh re-run rather than `reprocess_run.py`; 0 of 1109 newly-verified crossings
  were window-limited. `ridge`'s committed "best" numbers need no correction.
- [x] **`wide_window` re-verified, also fully clean** -- 2 geometries, 36 min, 0 window-limited
  out of 123 newly-verified crossings (0 at screening, 0 refined). Both `ridge`-family runs now
  confirmed; the "ridge doesn't produce this artifact" explanation in the `trial_grid` finding
  holds across both.
- [ ] **New `hybrid` (AlN/SiNx) geometry family needs its em.plot(component='Index') geometry
  check and smoke survey** -- `geometry.Hybrid` is written and unit-tested (masks tile correctly,
  core embeds in shell, invalid dimensions rejected) but the actual EMode build (shape `priority`
  for the AlN-over-SiNx overlap, the rectangular-shell convention) is unverified, same status
  `loaded.Loaded` started at. `survey_config_hybrid_smoke.py` is ready to run once EMode is free.
  Goal: re-attempt TM00->TM20 phase matching (per Honda et al. 2025, adapted to this project's UV
  band) where plain `ridge` found none in 215-235 nm.

## References

- Engineered Channel concept deck (B. Fisher, 2025), slides 57–69 (Mechanism 2, leaky modes,
  Cerenkov): https://drive.google.com/open?id=13qvuAlLau_AkQfryeLN-KplnEaCyg8omGNrym3DXIMQ
- `2025_12_cerenkov` sheet (COMSOL mode indices for AlN/ScAlN/AlN on sapphire; Bäumler AlScN
  indices; sapphire Sellmeier):
  https://drive.google.com/open?id=1jQ602CaZzPCRrRnDJQgsaBiBmuDJc-GB9webnkYphxE
- Bäumler et al., J. Appl. Phys. 126, 045715 (2019) — AlScN optical constants, x ≤ 0.41.
- Majkić et al., Phys. Status Solidi B (2017), 201700077 — bulk AlN d33, d31.
- Yoshioka et al., APL Materials 9, 101104 (2021) — sputtered AlScN d33/d31 vs Sc.
- Lee et al., arXiv:2607.14590 (2026) — MBE AlScN on sapphire d31/d33 vs Sc.

## Implementation status & findings (2026-10-03)

Code: `survey.py` (Step 1 driver), `shg_physics.py` (figures of merit), `geometry.py` (family
interface, `ridge`, later `loaded`), `cerenkov_fdfd.py` + `cerenkov_run.py` (Step 1b),
`summarize_run.py`, `plot_crossing.py`, `plot_geometry.py`; tests `test_shg_physics.py`,
`test_cerenkov_fdfd.py`, `test_geometry.py`, `test_plot_crossing.py`. How to run: README.md,
`SHG_Survey_Runner.ipynb`, or the Field Guide artifact (theory + architecture + operating guide
in one place — ask Claude for the link).

EMode facts established while building it (EMode 1.0.4):
- `boundary_condition='0A'` (antisymmetric Ex on the west wall) returns exactly the x-even
  class (Ey even: TM00, TM01, TM20, TE10...); `'0S'` the x-odd class (TM10, TE00...). Fields come
  back on the FULL window (already unfolded). The old pipeline's `'TM'` setting therefore only
  ever saw one class. The SH scan uses `'0A'` only = the selection rule, for free.
- `max_effective_index` is a *target*: FDM returns the `num_modes` modes nearest it.
- Mode normalization: integral of Sz = 1 (nm^2 units) with Sz = Re(E x H*) (no 1/2). E [V/m] and
  H [A/m] are mutually SI-consistent; the survey renormalizes to 0.5 Re int(E x H*) = 1 W.
- No permittivity export via `get_fields` (only E/H/S). chi(2) / absorption masks come from the
  geometry builder.
- PML combined with a symmetry boundary crashed EMode's FDM (internal broadcast error) — leaky
  SH modes in EMode are therefore not used; radiation is handled by the driven FDFD instead.
- `em.scattering(shape, mode_list=[i])` keeps the native scattering call to ~a few s.
- Profile labels must not contain '.'.

Physics/validation:
- NCE formula reproduces the textbook plane-wave limit exactly; symmetry-forbidden pairs come
  out at ~1e-16 relative. FDFD radiation matches analytic line-source results to <1% for
  Ex/Ey/Ez sources; flux = source work to 0.1%.
- h=350/w=400 ridge: TM00 -> TM04 at 228.8 nm, NCE 6.2 %/W/cm², EMode linear overlap 0.0086
  (old pipeline: ~0.0095 at nearby widths), shape overlap 0.014, L_opt 3.2 mm, peak 0.08 %/W.
- SH "modes" below the max cladding index at lambda_SH are box modes of the metal-walled window
  (radiation continuum), not guided — excluded from guided matching (they belong to Step 1b).
- Cerenkov from a high-index AlN ridge core into sapphire is strongly suppressed even when
  allowed by the index condition: inside the core the SH transverse wavelength (~130 nm) is far
  shorter than the source size, so emission cancels (kappa ~1e-5 %/W/cm in a test). Efficient
  Cerenkov needs the nonlinear layer embedded in a cladding whose SH index is close to n_eff,pump
  (the deck's AlN/AlScN/AlN designs) — a Step 2 geometry.

### Trial grid results (ridge, h = 300/350/400, w = 300–800, run `trial_grid`, 2026-10-03)

- 18 geometries in 91 min (~5 min each), 0 failures; 1109 guided crossings, 140 refined.
  Pump-export pass 16 min; Cerenkov pass ~40 s per pump.
- Best loss-limited: TM00 -> TM04, h=350, w=500 (227.9 nm): NCE 4.8 %/W/cm², L_opt 4.3 mm,
  peak 0.11 %/W; TM00 -> TM04/TM64 at h=350 holds ~0.08–0.11 %/W for w = 400–700.
  At h=400 the best partner becomes TM01 pump -> TM06 SH.
- Highest lossless NCE: TM10 -> TM60 (h=350, w=400) 14.9 %/W/cm² — but its SH mode scatters
  ~1100 dB/cm (EMode-native, 2.5 nm sidewall rms), so its loss-limited peak is ~100x lower.
  All shape overlaps are ~0.01–0.025.
- **No TM02/TM20 SH partner phase-matches anywhere in 215–235 nm.** Wide-window run
  (`wide_window`, 215–275 nm, h=300/350, w=500): lowest-order TM00 partners are TM22
  (254–263 nm) and TM40 (263–267 nm); TM02/TM20 lie beyond 275 nm. AlN's index dispersion
  450 -> 225 nm is too large for a low-order SH mode to match the pump in a plain ridge;
  bringing TM02 into the window needs dispersion engineering (Step 2 geometries / materials).
- Cerenkov (Step 1b) for all 19 index-allowed pumps: kappa_C <= 0.0019 %/W/cm (best: TM01,
  h=350 w=300, 14 deg into sapphire); energy balance within 0.3% everywhere. Negligible vs the
  guided match, as expected from the core-cancellation argument above.
- Mode labels: node counting now uses the power-weighted most common count per row/column
  and marks hybrids with '?'; `relabel_run.py` re-labels refined rows from their exports.

### Loaded-family smoke test (2026-10-04)

Ran the PLAN's open item 1 (geometry parameterization check) end-to-end for `geometry.Loaded`
(strip_eq AlN film + TiO2 strip, John Carlson deck slides 10-15). Geometry/mask conventions
verified correct (partial-etch rib width and outside-slab thickness, `strip_offset` sign -- strip
at +300 nm gave a mode x-centroid at +299.9 nm -- all matched EMode's own index plot pixel-for-pixel,
`runs/geometry_check/`). The pipeline itself runs cleanly: `loaded_smoke` found 5 pump modes, 317
guided crossings, 8 refined (best TM00->TM165? at 225.4 nm, NCE 33.4 %/W/cm^2). No bugs in
`geometry.Loaded`'s masks/build.

But two independent loss gaps mean none of that run's loss numbers (scattering or absorption) can
be trusted yet -- see the three new "Open items" entries above for detail:

1. EMode's built-in `TiO2` has k=0 everywhere (checked via `em.refractive_index`) -- fixed with a
   damped-Sellmeier fit to Siefke et al. 2016 ALD TiO2 data (`materials/fit_tio2_sellmeier.py`,
   `materials/TiO2_Siefke2016_sellmeier_fit.json`; SH-band n,k good to 1-3%, pump-band k has a
   small ~1-3e4 dB/cm residual-tail artifact, documented in the JSON). But EMode's FDM solver
   cannot actually consume a complex (lossy) `refractive_index_equation` -- it crashes
   unconditionally (`Cannot cast ufunc 'add' output from dtype('complex128') to dtype('float64')`),
   confirmed independent of boundary condition, masking, or which shape. `survey_config_loaded.py`
   currently uses the fit's real-only equation (correct n, no loss) so the smoke test can run.
2. `native_scattering()` (roughness loss) returns NaN for every `loaded`-family shape, silently
   treated as zero loss downstream -- see the matching "Open items" entry.

The one bulk-loss mechanism confirmed to actually work in this EMode build is the deprecated
`shape(loss_dB_per_m=...)` parameter (verified: a 300 nm-wide lossy strip with bulk loss=1e6 dB/m
reports a correctly confinement-weighted ~9.4e5 dB/m modal loss via `em.report()`; a 0-loss
control reports exactly 0). `add_material(loss=...)`, the documented non-deprecated replacement,
was verified to NOT reach the modal loss report at all (`report()` showed 0.000 dB/m regardless of
the material's `loss` value). Wiring real SH-band TiO2 absorption into the survey therefore means
computing bulk alpha(lambda) in Python from the n,k fit and re-setting it via the deprecated
shape-level call at every solve wavelength -- not yet implemented.

### EMode version gap resolved the scattering NaN (2026-10-04, later same day)

This desktop's EMode.exe was v1.0.0.0 while the laptop (which built this whole codebase and
produced `trial_grid`) was on v1.0.4 -- the two machines' EMode installs had silently diverged;
nothing in the repo/CLAUDE.md tracks or syncs the EMode.exe version itself (only the git repo and
`requirements.txt`-managed Python packages). Re-tested all three EMode-API findings above after
updating this desktop to v1.0.4:

- `get_shape()` after `em.scattering()`: **fixed**. Re-ran `loaded_smoke` fresh with no code
  changes -- scattering now populates for every pump and SH mode, matching `ridge`'s long-working
  behavior. The "possibly related to etch_depth == height" theory above was a red herring; it was
  never geometry-specific, just unnoticed on `ridge` because this machine hadn't run that family
  since the version gap opened. The committed `loaded_smoke` run now reflects this: best match
  TM00->TM165? @ 225.4 nm, NCE 33.4 %/W/cm^2 unchanged (lossless), but loss-limited peak efficiency
  corrected from a bogus 47.4 %/W (artifact of scattering silently reading as zero, L_opt pinned at
  the 200 mm cap) down to a physically sane 6.3 %/W/cm^2 at L_opt = 12.1 mm.
- Complex `refractive_index_equation` crashing `em.FDM()`: **still broken on v1.0.4**, now with a
  full traceback confirming a genuine EMode-side bug (see Open items). A v1.0.5 exists; not tried.
- `add_material(loss=...)`: **still broken on v1.0.4**, loss never reaches `report()`.

Net: the loaded-family pipeline's roughness-scattering loss is now trustworthy without any code
change. Bulk SH-absorption loss (TiO2 etc.) still needs the `shape(loss_dB_per_m=...)` workaround
described above, independent of EMode version.

### Bulk SH-absorption wired up, and EMode 1.0.5 checked (2026-10-04, later same day)

Updated this desktop to EMode v1.0.5: did NOT fix the complex-equation `em.FDM()` crash (identical
error, traceback now at a shifted line number confirming the surrounding code did change) or
`add_material(loss=...)` (still 0.000 in `report()`). Checked EMode's 1.0.5 release notes directly:
the material-loss fix that version shipped was scoped to **EME** ("a lossy material amplified the
mode in EME... now has an effective index with a negative imaginary part") -- not FDM. Re-verified
`n_eff_tilde` directly (not just `report()`) stays exactly `0j` for `add_material(loss=...)`
regardless of the loss magnitude (tried up to 1e8 dB/m): the material `loss` parameter is an
EME-only mechanism, not a bug we were hitting for FDM mode-solving.

So `shape(loss_dB_per_m=...)` + re-solve was the only remaining option -- tried it first (geometry
builders setting bulk alpha(lambda) on the lossy shape via `shape()`, re-solving, reading
`report()`'s "Loss (dB/m)" column). It technically worked (correct confinement-weighted values,
confirmed against a toy single-slab structure), but re-running `loaded_smoke` with it showed the
refined crossings had DRIFTED from the pre-bulk-loss run: the ~225.38 nm TM00 crossing's SH label
changed TM165? -> TM183 and its `overlap_shape` dropped 0.051 -> 0.0036, even though nothing about
the crossing's identity should have changed. Root cause: TiO2's SH-band bulk loss is enormous
(alpha ~3.4e8 dB/m, 215-235 nm) -- large enough that re-solving with it set perturbs the solver's
eigenvalue search enough to return a different candidate mode set than the lossless screening
pass, so the argmax-similarity match locks onto a different physical mode. Switched to a pure
post-solve perturbation instead (no EMode re-solve): `geometry.Loaded.lossy_mask()` returns the
strip region, `lossy_bulk_loss_dB_per_m()` computes the material's own bulk alpha(lambda) in
Python from `strip_loss_eq` (no EMode call), and `survey.bulk_absorption_loss()` multiplies by
Gamma = the already-solved lossless mode's own power fraction in that mask
(`shg_physics.power_fraction_in`). Re-ran `loaded_smoke` again: every refined crossing's label,
NCE and overlap_shape now match the original pre-bulk-loss run exactly (mode ID is untouched,
since nothing is re-solved), while `sh_absorption_dB_per_m` / `pump_absorption_dB_per_m` are now
real, nonzero, physically-scaled values (e.g. the best crossing, TM00->TM165? at 225.38 nm, now
carries ~2.6e7 dB/m of SH-band bulk absorption -- about 7.7% modal confinement in the TiO2 strip
times TiO2's bulk value).

Finding (not a bug -- this is what including real TiO2 absorption for the first time reveals):
with TiO2's actual SH-band k, **any crossing whose SH mode has more than a percent or so of its
power in the strip is efficiency-killed** -- `L_opt` pins at the 1 um floor of
`loss_limited_length`'s search grid for several of the smoke run's best-NCE crossings, meaning the
true optimum is shorter still. A `loaded` design wanting usable SHG efficiency likely needs the
*phase-matched* SH mode's field kept largely out of the strip (using the strip mainly to perturb
dispersion for phase matching, not as part of the SH mode's core), which is a real geometry-design
constraint for Step 2, not just a materials-data gap.

### First full `loaded` sweep with real TiO2 loss (`loaded_sweep1`, 2026-10-04/05 overnight)

**Correction (2026-10-05, see the "Window/box-mode artifacts" entry below): the NCE=293 %/W/cm^2
"best crossing" cited in this section is a simulation-window artifact, not a real mode** -- the
real best is TM00->TM05? at 159 %/W/cm^2 (h_s=150/w_s=1000). The peak-efficiency numbers below are
only mildly affected (the peak-efficiency #1 row survives the filter essentially unchanged) --
it's specifically the NCE ranking and the "which crossing is best" headline that were wrong. Left
as originally written below for the history; `runs/loaded_sweep1/summary/` now reflects the
corrected numbers.

Ran the 8-geometry sweep in `survey_config_loaded.py` (unetched AlN film, TiO2 strip; t_film in
{354, 600}, h_s in {70, 150}, w_s in {500, 1000} nm) with the bulk-loss wiring above. 0 failures,
80 min total, 2399 guided crossings (64 refined, 8 per geometry). `summarize_run.py` updated to
surface `pump_absorption_dB_per_m` / `sh_absorption_dB_per_m` in the peak-efficiency table (it was
still saying "no UV absorption data yet" and hiding exactly the numbers that now explain the
results) and to describe scattering/absorption generically instead of hardcoding "native
scattering + interface absorption" for pump / "native scattering only" for SH.

- **Lossless NCE is dramatically higher than the ridge family**: 0.0005-293 %/W/cm^2 across all
  refined crossings, vs. ridge's best of ~15 %/W/cm^2 (`trial_grid`). The h_s=150 nm geometries in
  particular reach NCE > 100 %/W/cm^2 repeatedly (TM00->TM123? at h_s=150/w_s=500 hits 293
  %/W/cm^2) -- the strip genuinely does pull in strongly-overlapping, low-order-ish SH modes the
  way the design intends. **[corrected below: TM00->TM123? is a window artifact; the real ceiling
  from this sweep is ~159 %/W/cm^2, still dramatically above ridge]**
- **But loss-limited peak efficiency collapses once real TiO2 absorption is included**: 2.9e-11 to
  2.8e-6 %/W across all 64 refined crossings -- the best case in the whole sweep (TM10->TM26 at
  234.9 nm, t=600/h_s=150/w_s=500, NCE 43.6 %/W/cm^2) is ~40,000x worse than ridge's best committed
  peak efficiency (0.11 %/W, `trial_grid` TM00->TM04 h=350/w=500). `L_opt` pins at the 1 um grid
  floor for nearly every top-NCE row. Root cause confirmed in the data: it's not just SH-band loss
  (expected) -- **pump-band TiO2 absorption is also substantial** (confinement-weighted
  pump_absorption_dB_per_m commonly 1e5-1.7e6 dB/m across the sweep's best-NCE rows), because the
  fitted pump-band bulk value itself is ~1.5-2.9e6 dB/m (not negligible merely because k is "small"
  relative to the SH band -- 0.01-0.03 is still ~100x the existing AlN growth-interface absorption
  mechanisms already in `pump_absorption_mechanisms`), and a loaded design's pump mode has real
  confinement in the strip by construction.
- **Conclusion: TiO2 is likely the wrong strip material for this design**, not merely "needs real
  loss data" -- with real data in hand, it absorbs too strongly at BOTH bands to be competitive
  with the plain `ridge` family, let alone better. The natural next experiment is swapping the
  strip for a nonlinear, lower-loss material that can also contribute d33/d31 (ScAlN's Bäumler fit
  is already done, `materials/fit_baumler_sellmeier.py` -- just needs `strip_chi2` wired to a
  ScAlN entry in `d_tensors_pm` and a `strip_eq`/`strip_loss_eq` built the same way as TiO2's); see
  PLAN.md's chi2 tensor section on TE-pump -> TM-SH via d31 becoming competitive in ScAlN.
- **Caveat on completeness**: every one of the 8 geometries hit the "SH n_eff window too narrow"
  warning (21-63 group-steps affected, worst for h_s=150 cases) -- `num_sh_modes=30` may be
  undercounting the true crossing set for this family, especially the higher-NCE h_s=150
  geometries. Re-running with a larger `num_sh_modes` would be worth it before treating "293
  %/W/cm^2 is the best NCE in this family" as final. (Moot for that specific number now --
  see below -- but the undercounting concern itself stands.)

### Window/box-mode artifacts in `loaded`-family results (2026-10-05)

User review of `loaded_sweep1`'s field plots caught it: several high-NCE refined crossings (the
reported #1, TM00->TM123? at 293 %/W/cm^2, among them) showed a SH field with a regular, roughly
uniform-amplitude lattice of lobes spanning the *entire* simulation window at constant spacing,
not decaying toward the walls -- a real local field enhancement near the strip riding on top of
an undecayed background, rather than a genuinely bound mode. Confirmed by contrast against a
clean case (TM00->TM05, NCE 154, smooth envelope decaying to ~0 well inside the window) -- see
`runs/loaded_sweep1/plots/`.

Root cause: `sh_scan()`'s window has reflecting (non-PML) walls for the guided-mode search (PML
is reserved for the driven Cerenkov solve, see "Implementation notes/risks"). In addition to real
bound modes, this quantizes a quasi-continuum of **box modes** of the surrounding cladding/
substrate -- states that exist only because the hard walls force a standing wave, not because
anything in the actual (physically much wider, or infinite) device would confine them there. Nowhere
in the pipeline previously checked for this; NCE and overlap_shape are computed from the field as
given and don't care whether that field is physically confined or an artifact of the box.

Fix: `shg_physics.lateral_edge_ratio(f, x)` -- the lateral intensity profile's value at the
window's outermost ~2.5%, relative to its own peak. Near 0 for a real bound mode (quasi-exponential
decay before reaching the wall); stays well above 0 for a box mode (undecaying oscillation all the
way out). Validated against the sweep's own data: a clean cluster (TM03/04/05 family) sits at
0.0005-0.016, a contaminated cluster at 0.04-0.83, with the visually-confirmed TM123? case (0.038)
right at that boundary. Computed per refined crossing (needs the full field export, so **not
decidable for screened-only crossings**) and stored as `sh_edge_ratio` / `pump_edge_ratio` (pump
is uniformly clean, ~1e-6 to 1e-14, across every crossing checked -- expected, since pump
candidates are the lowest-order real modes by construction, not a broad SH-style index-targeted
search). `survey.refine_crossing()` now computes both for every future run;
`reprocess_run.py` backfills them into existing runs from already-saved exports (no EMode needed)
-- ran for `loaded_smoke` and `loaded_sweep1`.

`summarize_run.py` now excludes refined crossings with `sh_edge_ratio` > `MAX_SH_EDGE_RATIO`
(0.02, tunable at the top of the file) from every ranking table, and states the exclusion count
plus how many screened-only crossings in that run couldn't be checked. Corrected headline numbers:
`loaded_sweep1`'s real best NCE is **159 %/W/cm^2** (TM00->TM05? at h_s=150/w_s=1000), not 293;
peak efficiency's #1 row is unaffected (TM00->TM05, 8.5e-7 %/W/cm^2, already physically clean).

**Bigger finding: refinement is spending most of its budget on these artifacts, not just reporting
them.** `refine_top_n` picks the top-N crossings *by screened NCE* for full refinement -- exactly
the number box modes inflate. Of `loaded_sweep1`'s 64 refined crossings, **52 (81%) turned out to
be window-limited**; for `loaded_smoke` specifically, **all 8 of 8** were -- that single-geometry
smoke run currently has zero verified-real refined crossings, only an unverified screened one
(NCE 0.68) as the best trustworthy entry. This means real candidates are plausibly being crowded
out of the refine budget entirely, not just outranked in the final report. Two non-exclusive
fixes, not yet implemented, needing a decision on which to pursue first:
1. **Widen the simulation window.** Box modes are an artifact of a finite box; a wider window
   pushes the spurious quasi-continuum's index spacing tighter and reduces how often one
   coincidentally sits right at a pump's crossing index with a locally-enhanced overlap. Simplest,
   but costs more per solve (bigger mesh) and doesn't eliminate the issue, just thins it out.
2. **Screen-time filtering.** `lateral_edge_ratio` only needs a field + its x grid -- in principle
   computable on `sh_scan()`'s already-in-memory downsampled (`small()`) tracking fields, before
   deciding what to refine, so `refine_top_n` could skip (or deprioritize) obviously box-mode
   candidates and spend the budget on real ones instead. Not yet tried; `small()` only keeps
   `Ex`/`Ey` (drops `Ez`) at half resolution, so the ratio would need validating at that reduced
   fidelity before trusting it to drive selection.

`cerenkov_run.py loaded_sweep1 --all` (all 40 pumps across the 8 geometries -- notably slower per
pump than ridge's ~40s, 4-7 min each here, worth a look if this module gets used routinely for
`loaded`): confirms the ridge family's conclusion holds here too -- kappa_C tops out at ~0.078
%/W/cm (TM10, t=600/h_s=150/w_s=1000), negligible next to the guided channel. 35/40 rows have
energy balance within ~3% of 1; the 5 that don't all have |kappa_C| <~1e-5 %/W/cm (near the
solver's noise floor at that signal size, same as the energy-balance caveat already noted for
ridge) -- not a new issue, just the existing caveat showing up for real on this family's first run
through Step 1b.

### Screen-time window/box-mode filtering (2026-10-05, same day, user chose option 2 of the two
candidate fixes above)

`Es`, the field `sh_scan()` already holds for a crossing at screening time, turns out to be the
*full-resolution* solve (Ex/Ey/Ez on the actual simulation grid, same field `eta_screen` itself is
computed from) -- not the downsampled Ex/Ey-only `small()` field used for step-to-step tracking,
which the previous entry's option 2 worried would need a fidelity check first. So
`shg_physics.lateral_edge_ratio(Es, x)` is computed directly, no proxy, no validation gap:
`sh_scan()` now stores it per crossing (`edge_ratio_screen`), and `run_geometry()`'s refine
selection skips any crossing above `cfg['max_sh_edge_ratio']` (0.02, new `SETTINGS` key --
deliberately part of the fingerprint, since it changes which crossings get refined) when filling
`refine_top_n`, rather than spending the budget confirming what screening already knows.
`screened_row()` now also carries `sh_edge_ratio_screen`, so **every** crossing -- not just
refined ones -- gets a verdict; `summarize_run.py` updated to use it as a fallback wherever the
full `sh_edge_ratio` isn't available (refined rows still prefer that one).

Re-ran `loaded_smoke` clean: of 317 screened crossings, only **4 were eligible** for refinement at
all (edge_ratio_screen <= 0.02) -- confirming the earlier finding that ~99% of this specific
geometry's crossings are window artifacts, not an 81%-vs-100% difference between two runs. Only 1
of those 4 got refined (the rest fell below `refine_min_nce_pct`); its screen-time and full-refine
edge ratios agree to within ~1% (0.00643 vs 0.00635), validating that the screening-stage check is
exactly as reliable as the refined one, as expected since it's the same-resolution field. That one
verified-real crossing (TM20->TM04 @ 230.99 nm) has NCE only 0.045 %/W/cm^2 -- this specific
geometry (h_s=70/w_s=500) genuinely doesn't support a good phase match once artifacts are removed;
the sweep's better geometries (h_s=150, w_s=1000) are where the real ~150 %/W/cm^2 result lives.

**Second bug found and fixed while implementing this**: `CROSS_FIELDS` (the fixed column list
`append_rows()`'s `csv.DictWriter(..., extrasaction='ignore')` uses) was never updated when
`pump_edge_ratio`/`sh_edge_ratio` were added for the post-solve-perturbation loss work, and
`sh_edge_ratio_screen` was never added either -- both silently dropped from newly-appended rows.
Worse, `append_rows()` itself had a latent bug: when it detects an older file's header needs new
columns, it rewrites the header to the union but was still *appending* new rows with the
narrower original fieldnames list, so new rows ended up with fewer CSV cells than the (correctly
upgraded) header -- not content-misaligned (pandas pads short rows at the end with NaN), but the
new fields' real data was gone for exactly the rows that should have had it. Fixed both: added the
three field names to `CROSS_FIELDS`, and `append_rows()` now uses the same unioned fieldname list
for the upgrade pass and the append pass. Added `test_survey.py` to cover the append_rows fix
directly (a synthetic two-write scenario exercising the exact bug). `loaded_smoke`'s crossings.csv
had already been corrupted this way by the first (pre-fix) re-run attempt -- deleted and re-run
clean rather than patched.

Not yet done: re-running `loaded_sweep1`'s full 8-geometry sweep with this fix active, to get a
properly-filtered-at-the-source "real best NCE" for the whole family (today's 159 %/W/cm^2 number
is from the report-time filter only -- still correct, just not benefiting from the better-targeted
refine budget this unlocks).

### `loaded_sweep1` re-run with screen-time filtering active (2026-10-05, same day)

Re-ran the full 8-geometry sweep (old fingerprints kept alongside, per the usual checkpoint
convention -- `summarize_run.py` now reports "16 geometries", 8 old + 8 new). 75 min, 0 failures.
Across the new run's 2399 screened crossings, only **44 (1.8%) were eligible for refinement**
(2355, 98.2%, window-limited at screening) -- generalizing the single-geometry smoke-test finding
(~99% artifacts) to the whole family, not an outlier. 32 of the 44 eligible ones got refined
(fewer than the old run's 64, since several geometries simply don't have 8 eligible candidates --
budget no longer being forced to fill).

**Headline NCE is unchanged: 159 %/W/cm^2 (TM00->TM05?, h_s=150/w_s=1000)** -- reassuring
cross-check that the earlier report-time-only filter had already found the correct answer; this
run's value is the same crossing, re-solved independently, confirming the fix improves efficiency
and verification coverage without changing the physics conclusion. TiO2-strip-as-wrong-material
conclusion stands unchanged.

**Open follow-up, not yet done**: the `ridge` family's committed results (`trial_grid`,
`wide_window`) predate this entire window/box-mode check and have never been verified against it
-- worth a pass before trusting their "best" rows at face value, the same way `loaded`'s needed
correcting. Likely lower risk there (ridge's window is sized differently and its best crossings
were lower-order, less suspicious node counts) but not actually checked.

### `ridge` family verified clean: `trial_grid` re-run (2026-10-05, same day)

`ridge`'s local `exports/`/`traces/` turned out to be gone -- only ever existed on the laptop
(gitignored, never committed), so `reprocess_run.py` couldn't backfill from local files the way it
did for `loaded`. Re-ran `trial_grid` fresh instead (same `max_sh_edge_ratio` fingerprint-change
mechanism as `loaded_sweep1`'s re-run triggers this automatically). 18 geometries, 131 min, 0
failures, old fingerprints kept alongside (36 geometries total now).

**Zero window-limited crossings, out of 1109 newly-verified** (0 at screening time, 0 at full
refine resolution) -- not even the oddest-looking result: the final geometry's best crossing
(TM20->TM120 @ 221.38 nm) has `sh_edge_ratio` ~3e-11, about as clean as a mode gets, despite the
suspiciously-high-sounding label. `ridge`'s committed "best" numbers across both `trial_grid` and
(by the same reasoning, though not independently re-run) `wide_window` need no correction. This is
a real structural difference from `loaded`, not a coincidence worth re-litigating every time: the
plain ridge is a simple, strongly-guiding core directly on the substrate with nothing to create a
shallow, weakly-confining background region for a box mode to hide near -- `loaded`'s unetched AlN
film (and now `hybrid`'s SiNx shell) both have exactly that kind of shallow surrounding region,
which is where every `loaded`-family window artifact was found living.

`wide_window` (2 geometries, wider 215-275 nm SH scan) re-run the same way: also fully clean, 0 of
123 newly-verified crossings window-limited. Both `ridge`-family runs are now confirmed; "ridge
doesn't produce this artifact" isn't a one-run coincidence.

### New `hybrid` (AlN/SiNx) geometry family added, `etch_depth` bug found and fixed (2026-10-05, same day)

Added a third geometry family, `geometry.Hybrid`, adapting Honda et al. 2025 (Appl. Phys. Express
18, 122001 -- AlN core embedded in a SiNx "shell" sized so SiNx occupies the region where TM20's
transverse field reverses sign, enabling TM00->TM20 phase matching that a plain ridge can't reach)
directly to this project's UV target (215-235 nm SH, 430-470 nm pump) rather than replicating the
paper's telecom demo (1550/775 nm) -- user's explicit choice between the two options. Needed a new
SiNx n+ik fit (`materials/fit_sinx_sellmeier.py`, Beliaev et al. 2022 PECVD data via
refractiveindex.info, rms n=0.0009/k=0.0012; SiNx is genuinely ~lossless in the pump band, k~0 by
450 nm in the raw data, not just a fit artifact). `'SiN'` is EMode's database name (`'SiNx'`,
`'Si3N4'` don't exist there).

Live `em.plot(component='Index')` check on the smoke geometry caught a real bug before any survey
ran: both the shell and core `em.shape()` calls were missing `etch_depth`, so `mask` alone did
nothing -- EMode rendered a flat full-window-width layer stack instead of the intended embedded
trapezoid. Root cause and fix: `etch_depth` must equal the shape's own height (same convention
`Loaded`'s `'strip'` already used) for `mask` to actually restrict a shape to finite width; without
it, a shape silently fills the whole window regardless of `mask`. Fixed in `Hybrid.build()`
(`geometry.py`); re-ran the check after the fix and confirmed the render now matches `_masks()`
exactly -- AlN trapezoid correctly embedded in the SiNx rectangle, substrate/topclad otherwise
clean. No-EMode test suite (`test_geometry.py`) re-run clean, all passing (these tests only cover
the pure-Python mask logic, which was already correct -- the bug was specifically in the EMode-side
`build()`, not something they'd have caught).

### `hybrid_smoke` + first 6-geometry `hybrid` sweep (2026-10-05, same day)

Ran `hybrid_smoke` (1 geometry, pipeline validation) then the full `hybrid1` sweep
(`survey_config_hybrid.py`'s 6 geometries: h_core in (300,350,400), w_core in (400,500), with
`sin_width = w_core+400`, `sin_height = h_core+300`). All 6 `ok`, no failures, ~46 min total.
**Zero window-limited crossings across all 2290 screened + 48 refined results** (max `sh_edge_ratio`
among refined: ~3e-15) -- `hybrid`'s shallow SiNx shell region was flagged as a plausible artifact
risk (similar in spirit to `loaded`'s unetched film, where every prior artifact was found), but
didn't produce one here, at least not at this sample size/these geometries.

Headline: **21.1 %/W/cm^2** (TM01->TM101 @ 227.41 nm, h=400/w=400/sin_w=800/sin_h=700) --
well below `ridge`'s 159 %/W/cm^2 and `loaded`'s best. More importantly: **no TM00->TM20 (or
TM00->TM02) match anywhere in the full 2290-crossing dataset** -- every top result pairs TM01 or
TM10 (not TM00) with a high-order, often uncertainly-identified SH mode (TM101, TM103?, TM411?,
TM122?, etc.), not the paper's specific TM00->TM20 mechanism.

This isn't evidence the hybrid mechanism doesn't work in the UV band -- it's evidence this specific
set of 6 geometries wasn't *designed* to trigger it. The paper gets TM00->TM20 phase matching by
choosing the SiNx shell's extent specifically so AlN sits where TM20's transverse field keeps one
sign (between its two interior nodes); `sin_width`/`sin_height` here were picked as arbitrary
margins (core size + fixed offset), not tuned to that condition. Finding the real UV-band hybrid
result (if it exists) needs a `sin_width` (and/or `sin_height`) sweep at fixed `h_core`/`w_core`,
explicitly searching for the shell extent where TM20 appears in the pump-mode list AND the AlN
core's position avoids cancelling against TM20's sign flip -- not more guesses at the margin size.
Deferred pending user direction on whether to pursue that targeted sweep.

### Targeted `hybrid` sweep: `sin_width` decoupled from `w_core`, still no TM00->TM20 (2026-10-05/06)

User asked to proceed with an extensive sweep. Built `survey_config_hybrid_sweep.py`: fixed
h_core=400/sin_height=700 (the first pass's best NCE combo), independently scanned `w_core` in
{200,300,400,500,600} nm x `sin_width` in {700,900,1100,1300,1500} nm (24 geometries, kept where
`sin_width >= w_core + 200`) -- the whole point being to actually vary the core-to-shell width
ratio, which the first pass's `sin_width = w_core + fixed_margin` construction never did. Also
raised `num_sh_modes` 30->45 (every geometry in the first pass logged "SH n_eff window too narrow",
worse for wider shells -- a real risk of the scan's per-step mode window missing whichever SH mode
actually matters). Ran clean: all 24 `ok`, 0 failures, **0 window-limited among 12442 crossings**
(max refined `sh_edge_ratio` ~4e-15) over ~4.9 hours (wall time climbs steeply with `sin_width`: a
700 nm shell takes ~8-9 min/geometry, 1500 nm climbs to ~14 min -- more lateral modes to track).

Headline across both `hybrid` sweeps combined (30 geometries, 14732 crossings total): **25.2
%/W/cm^2**, TM01->TM81 @ 232.38 nm (h=400/w=400/sin_w=700/sin_h=700 -- the narrowest shell tried in
the targeted sweep, notably *not* the widest). Still well below `ridge`'s 159 and `loaded`'s best.

**The paper's TM00->TM20 mechanism was not found.** Checked directly: zero crossings anywhere in
either sweep's combined dataset carry an exact `TM20` or `TM02` SH-mode label (confirmed via exact
regex match, not substring -- an earlier pass of this check falsely "found" TM00->TM20 hits that
turned out to be TM200/TM201/etc., i.e. m=20 not m=2, a much higher lateral order that just happens
to share a text prefix). The shells here are wide enough to guide many lateral orders (labels up to
~TM220 appear), so TM20 as a *mode* almost certainly exists at the SH wavelength in most of these
geometries -- what's missing is a *phase-matching crossing* between TM20's n_eff(lambda) curve and
any pump mode's, landing inside the narrow 215-235 nm window. That's a much more specific condition
than mode existence, and PLAN.md already has precedent for it being hard to hit: `ridge`'s own
trial_grid found "No TM02/TM20 SH partner phase-matches anywhere in 215-235 nm" despite a denser
18-geometry grid. 30 hybrid geometries, spanning only the lateral dimensions (`w_core`/`sin_width`)
at one fixed `h_core`/`sin_height`, may simply be too coarse/narrow a slice of the real design space
to land that one specific crossing -- vertical dimensions were never varied at all this round, and
they shift every mode's dispersion too.

Not yet done, deferred pending user direction: a vertical-dimension sweep (`h_core`/`sin_height`)
crossed with the lateral one would be the natural next step if the TM00->TM20 result specifically
still matters; alternatively, treating `hybrid`'s current best (TM01->TM81, 25.2 %/W/cm^2, clean)
as this family's answer and moving on is also defensible given 30 geometries of consistently modest,
sub-`ridge` NCE regardless of which modes end up matching.

### Sub-metric breakdown artifact (2026-10-06): loss is confinement-driven, overlap_shape isn't predictive

Before committing to a vertical sweep, built an exploratory artifact ("Hybrid Loss Atlas") from
`extract_subfigure_data.py` pulling apart the fields `refine_crossing()` already computes but
`summarize_run.py` only ever collapses into `eta_pct_per_W_cm2`: `overlap_shape` (dimensionless
0-1, integrated over the AlN region only, independent of loss or the d-tensor's absolute scale),
and the SH-side/pump-side scattering and absorption split. Across all 240 refined crossings
(hybrid1 + hybrid_sweep1):

- **SH-side (UV, 215-235 nm) absorption beats scattering by ~1000x median** -- and since AlN is
  modeled as lossless here (its own UV k is the still-open deferred item), 100% of that absorption
  is SiNx shell bulk loss, confirmed via `bulk_absorption_loss()`'s literal `Gamma_shell *
  alpha_SiNx(lambda)` (first-order perturbation: modal loss = the mode's own power fraction in the
  lossy region times that region's bulk material loss -- see [survey.py:167-182](survey.py#L167-L182)). Narrow
  AlN cores (w_core=200) have 2-3x *worse* SH absorption than wide ones (w_core=600) because less
  of the SH mode's power ever reaches the (lossless) AlN and more stays in the (lossy) SiNx.
- **Pump-side (true blue, 430-470 nm) loss is ~8300x smaller** than SH-side loss at the same
  crossing, and absorption only beats scattering by ~8x there (not ~1000x) -- SiNx's own measured k
  rounds to 0 in the raw literature data at these wavelengths, so pump absorption is mostly the
  fixed AlN growth-interface baseline (dislocations/impurities), not shell confinement, though the
  same weak "more power in core helps" trend still shows up via a small residual SiNx tail (likely
  a fit artifact, same caveat already flagged for TiO2's pump-band tail).
- **`overlap_shape` barely predicts final `eta`** (r ~ 0.09 across all 240 crossings): the
  narrowest cores reach the *highest* shape overlap (up to 0.81, vs ~0.05-0.10 for wide cores)
  despite having some of the *lowest* final NCE, because overlap_shape only measures field
  proportionality inside AlN, blind to how much power actually gets there or the overlap's
  absolute magnitude. None of the four w_core x sin_width geometry maps (best overlap_shape, mean
  SH power in core, lowest SH loss, best eta) peaks in the same place -- no single sub-metric picks
  the eventual NCE winner.

### Vertical-dimension sweep (`hybrid_vertical1`, 2026-10-09/10): new headline, still no TM00->TM20

User confirmed: proceed with the vertical sweep (not a re-run of the lateral grid at one new
thickness). Built `survey_config_hybrid_vertical.py`: lateral dims fixed at the lateral sweep's
best combo (w_core=400, sin_width=700), `h_core` in {250,300,350,400,450} x `sin_height` in
{500,650,800,950,1100}, kept where `sin_height >= h_core + 200` -- 22 geometries, same
`num_sh_modes=45` as the lateral sweep. Ran clean: all 22 `ok` (one transient `PermissionError`,
auto-retried per the known EMode-instability gotcha), **0 window-limited across 8814 crossings**
(max refined `sh_edge_ratio` ~7e-14).

**New headline: 35.2 %/W/cm^2** (TM01->TM81 @ 233.60 nm, h_core=300/sin_height=500 -- the
*shortest* shell tried, sitting right at this sweep's own minimum-margin floor), beating the
lateral sweep's 25.2. The top of the ranking is dominated by the smallest `sin_height` values
(500, 650) almost regardless of `h_core`, suggesting the true optimum may sit at or below 500 nm --
not explored yet, since 500 was this sweep's floor (`sin_height >= h_core + 200`), not a
physically-motivated lower bound. **Still zero exact TM20/TM02 SH-mode labels** across the
sweep's 8814 crossings (checked the same way as the lateral sweep, exact regex not substring).
Combined across all three `hybrid` runs so far (52 geometries, 23546 crossings total): headline
remains 35.2 %/W/cm^2, still clean, still no TM00->TM20 anywhere.

Not yet done: a narrower `sin_height` sweep (e.g. below 500 nm) following up on the "smaller shell
margin keeps winning" trend; re-running the sub-metric artifact against this run's data to see
whether the same loss/overlap decoupling holds vertically.

### CRITICAL: `hybrid`'s core was never actually embedded in the shell -- invalidates all 52 prior geometries (2026-10-10)

Before starting the narrower-`sin_height` follow-up, re-examined the committed geometry-check
render ([runs/geometry_check/hybrid_smoke_index.png](runs/geometry_check/hybrid_smoke_index.png))
more carefully and found the AlN core was **not actually embedded inside the SiNx shell** in any
of the three `hybrid` sweeps run so far (`hybrid1`, `hybrid_sweep1`, `hybrid_vertical1` -- 52
geometries, 23546 crossings total). The render showed the core trapezoid sitting *on top of* the
shell block (two tiers stacked vertically, a plain ridge-on-pedestal), not surrounded by shell on
the sides and above as `_masks()` computes and the Honda et al. mechanism requires.

Root cause: `em.shape()`'s `position` defaults to `(0, 'auto')`, where `'auto'` auto-stacks a new
shape on top of whatever already occupies its mask footprint (real-fab-style sequential
deposition) -- `Hybrid.build()`'s `core` shape() call never set `position` at all, so EMode
silently stacked it on top of the already-drawn `shell` instead of placing it at the substrate
baseline alongside/within the shell's footprint. Confirmed by comparing `em.plot(component=
'Index')` against the Python-side `_masks()` (which was always correct -- the bug was purely in
`build()`, same class of issue as the `etch_depth` bug found 2026-10-05, different parameter).

Fix required a second round: setting `position=(0, substrate_height)` (assuming bottom-referenced,
like the implicit stacking default) instead centered the core *on* `substrate_height`, straddling
down into the substrate -- `position`'s y-value turns out to be **center-referenced**, not
bottom-referenced. `position=(0, substrate_height + h_core/2)` is what actually lands the core's
bottom edge at the substrate line, matching `_masks()` exactly (confirmed via the geometry-check
render: core now sits bottom-flush with the shell's bottom, flanked on both sides and wrapped
above by shell, up to `sin_height`). Fixed in `geometry.py`'s `Hybrid.build()`; no-EMode test
suite re-run clean (these tests only cover `_masks()`, which was never wrong).

**This means every `hybrid` result reported so far -- the 25.2 %/W/cm^2 and 35.2 %/W/cm^2
headlines, the "no TM00->TM20 anywhere" finding across all three sweeps, and the sub-metric
breakdown artifact's loss/overlap/confinement story -- was computed for a structure that was never
the one intended.** The stacked (wrong) and embedded (correct) geometries are different
waveguides with different dispersion; nothing above should be treated as a finding about the
Honda et al. mechanism itself. Whether the *stacked* structure's own numbers are independently
interesting is a separate, unasked question -- not pursued.

One encouraging, NOT YET CONFIRMED signal: re-running the live mode check on the smoke geometry
(h=300/w=400/sin_w=800/sin_h=600) with the corrected geometry shows **TM20 appearing among the
first four computed modes** at the check's default wavelength (450 nm) -- it didn't appear at all
in the equivalent check against the old, stacked geometry. This is just a mode existing at one
wavelength, not a phase-matching crossing in the 215-235 nm SH window -- far short of confirming
the mechanism -- but it's the first time TM20 has shown up at all in this family's results, which
the stacked geometry apparently could never produce. Worth a fresh, full campaign to check
properly rather than reading into one data point.

Pending user direction on how to proceed: likely a full re-run of both the lateral and vertical
sweeps (and the narrower-`sin_height` follow-up) under the corrected geometry, effectively
restarting the `hybrid` family's sweep history from here. The three invalidated runs are left
committed (as `hybrid1`, `hybrid_sweep1`, `hybrid_vertical1`) for the record, not deleted.

### Renamed the stacked (non-embedded) structure to its own family, `pedestal` (2026-10-12)

User: keep the 52 geometries already computed under the broken geometry (real, valid results --
just for a different structure than intended), filed under an honest name rather than left
confusingly labeled `hybrid` next to the now-corrected family of the same name.

Added `geometry.Pedestal` (subclasses `Hybrid`, overriding only the geometry-placement methods --
`build`, `_masks`, `bbox`, `describe` -- since every other method, loss/chi(2)/Cerenkov/export,
already keys off `_masks()`/`bbox()` polymorphically): an AlN ridge stacked on top of an SiNx
rib/pedestal, matching exactly what every pre-fix `hybrid` run actually built (`build()` omits the
`position` override; `_masks()` places the core's trapezoid base at the shell's top instead of the
substrate line). Hit one new bug writing `_masks()`: shell's top (`yy <= y_sub+sin_height`) and
core's bottom (`yy >= y_sub+sin_height`) are both inclusive at that exact shared line, double-
counting it in `region_masks()`'s tiling check -- fixed with the same `& ~core` defensive pattern
`Hybrid`'s `_masks` already uses (even though the two "shouldn't" overlap by construction there
either). `test_geometry.py` gained a `pedestal` case in the tiling test plus
`test_pedestal_core_stacked_on_shell` (confirms core sits strictly above shell, not beside/within
it); full suite passes.

Renamed in place (`git mv`) and relabeled: `runs/hybrid1` -> `runs/pedestal1`,
`runs/hybrid_sweep1` -> `runs/pedestal_sweep1`, `runs/hybrid_vertical1` -> `runs/pedestal_vertical1`
(+ their `_smoke` counterparts), with every CSV's `family` column rewritten `hybrid` -> `pedestal`
(always the 2nd column, confirmed before the rewrite -- safe, unambiguous sed). The original
`survey_config_hybrid*.py` files are left untouched and will be reused as-is for the corrected
re-run (same parameter grids, now building the actually-embedded structure); parallel
`survey_config_pedestal*.py` copies were made purely for archival/reproducibility of the `pedestal`
runs, `family` string swapped and each docstring prefixed with a note pointing back to this entry
-- not meant to be run again, the data's already there.

### Next up

1. Housekeeping continues: review everything in `runs/` so far (ridge, loaded, pedestal) and decide
   what new report/figure outputs are useful -- user wants, concretely, a PDF version of the
   sub-metric breakdown artifact ("Hybrid Loss Atlas").
2. Plan a broader campaign (beyond `hybrid`/`pedestal`) -- candidate directions and materials-data
   gaps to be scoped with the user before anything runs.
3. Once 1-2 are settled: re-run `hybrid1`/`hybrid_sweep1` (lateral) and `hybrid_vertical1`
   (vertical, extended thinner per the "smaller sin_height keeps winning" trend) under the
   corrected geometry, then fold in whatever the broader campaign adds.

### Report-output agreement + Input Assumptions PDF (2026-10-12)

User direction on every future per-sweep results report: (1) pump/blue (430-470 nm) loss reported
with the same headline prominence as NCE, not buried as a sub-panel -- `loaded`'s TiO2 and now
`pedestal`'s SiNx both already showed lossless NCE can be badly misleading on its own; (2) a fixed
"Input Assumptions" page/reference in every report, including a cross-section diagram pulled from
EMode's own Index-component render; (3) keep the scatter-plot panel types already established
(`build_subfigure_report.py`'s loss/overlap breakdown); (4) a dB-additive stacked bar chart, one
bar per geometry, decomposing log(peak efficiency) into overlap/size/pump-loss/SH-loss
contributions -- agreed as illustrative (not exact), not yet built, pending real data to sketch it
against.

Found the authoritative source for the pump-loss absorption-mechanism assumptions: a Google Drive
memo, "Loss Model Summary & Results" (created 2026-09-22; shorthand used from here on:
`[Loss Model Summary, 2026-09-22]`), with real per-mechanism literature citations where they
exist (dislocations: Chen et al., Opt. Express 27(12), 17262, 2019 -- though literature treats
this as scattering with a TM>TE dependence, not modeled as such here; C impurities: Robinson et
al., arXiv:2606.19615, 2026; O impurities: Bickermann et al., Appl. Phys. Lett. 95, 262104, 2009;
Si impurities and all 3 sidewall mechanisms: explicitly flagged in the memo as unsupported
engineering placeholders).

That memo's own "Actual Inputs Used" table does NOT match `survey_config.py`'s actual current
values (different shapes, penetration depths, and two nonzero sidewall mechanisms the code omits
entirely) -- see `compare_pump_loss_assumptions.py`. Per user direction: rather than reconcile the
two, quantified the gap directly (ridge, h_core=350 nm, w_core=300-800 nm, reusing `trial_grid`'s
already-exported TM00 pump fields, no new EMode calls) and logged it. Result: the memo's values
give **consistently LOWER** total pump loss than the current code (ratio 0.49-0.75x across that
width range) -- not higher despite the extra sidewall terms, because the memo's exponential-decay/
shorter-penetration-depth choices for C/Si/O impurities more than offset them. Not an order-of-
magnitude gap, matching the user's own expectation -- **current `survey_config.py` assumptions
kept as-is**, no code change.

Built `build_assumptions_report.py`: an "Input Assumptions" PDF (`runs/input_assumptions_report.pdf`,
8 pages) every future results report should cite rather than re-deriving -- loss model + citations,
the pump-loss comparison above, AlN/SiNx/TiO2 dispersion overlay, ScAlN's 8-composition dispersion
sweep (index ready; UV k and chi(2) d33/d31 vs. Sc fraction still disputed, see below), a GaAlN
status page (no fit exists; documents the gap, not a fix), and the chi(2) tensor table (already in
this file, just not previously rendered into a report). Hit and worked around one odd, unexplained
bug while building it: `geo.eval_index_equation`'s restricted `eval(eq, {'__builtins__': {}}, ...)`
intermittently raised `KeyError: '__import__'` when called many times in sequence inside this
script specifically (reproducible given the exact page sequence, but not in a minimal snippet --
root cause not found); worked around with a local real-builtins eval helper in the report script
rather than risk changing the shared function used throughout the live EMode pipeline. Also found
(while building the dispersion charts) that the fitted Sellmeier forms for SiNx/TiO2/ScAlN all have
a real resonance pole near the UV band edge that dwarfs the device-relevant index range if plotted
unclipped -- y-axis limits added to keep the charts legible; the pole itself is a real feature of
the fits, not a bug.

On ScAlN/GaAlN's role in the matrix (user clarification, 2026-10-12): not only core-replacement
for d33 -- also (a) index engineering for a Cerenkov cladding (composition tunes index, not
nonlinearity) and (b) as a loading strip that reshapes the AlN mode (pulling it from the substrate
interface, or improving the AlN region's own overlap) without the strip itself needing to be
active. GaAlN specifically: NIST (Sanford et al.) gives composition-dependent d33 with a sign
change near Al fraction x~0.65, favorable (higher-d33) direction toward Ga-rich -- but GaN's
bandgap (~3.4 eV) sits well below the SH photon energy (~5.5 eV at 215-235 nm), so Ga-rich AlGaN is
almost certainly strongly absorbing exactly where this project needs transparency. Useful
composition window likely narrow, not yet checked quantitatively -- documented as an open item on
the GaAlN status page, not resolved.

### dB-additive NCE waterfall chart, built and verified (2026-10-12)

`nce_decomposition.py`: exact decomposition of loss-corrected peak efficiency into 5 dB-additive
terms (overlap shape, mode-size/field scale, SH loss, pump loss, + device length -- a 5th term
found to be mathematically necessary, not originally requested, once each geometry is evaluated at
its own optimal propagation length; see the module's docstring). Two earlier derivations were
tried and rejected after each failed its own reconstruction check against real data (~35 dB error
both times) -- comparing `L_eff` across separate `loss_limited_length()` calls that each
independently re-optimize L, then a single shared fixed length that numerically underflowed for
the dataset's higher-loss geometries. Final version: ~1e-14 dB reconstruction error (machine
precision) across all 416 `pedestal` crossings -- segments sum exactly to the total, not
approximately.

Added as a new page (`waterfall_page`) in `build_subfigure_report.py`: one stacked bar per
geometry (best crossing by eta, top 14 by peak efficiency), positive segments up / negative down
from 0, a marker confirming each bar's segments sum to its total. `runs/pedestal_subfigure_report.pdf`
regenerated with it.

### Simulation Study Plan PDF (2026-10-12)

`build_study_plan_report.py` -> `runs/simulation_study_plan.pdf` (7 pages): documents the 10-row
geometry x material design matrix before any of it runs -- the matrix table (with the `h_A` column
added per user request, and an honest `0 -> TBD*` for the embedded topologies since `h_A` is only
wired up in `loaded` today), then one page per underlying cross-section topology (Ridge,
Rib-loaded, Embedded-guided, Embedded-Cerenkov) with a diagram and which matrix rows use it, then
a proposed sequencing page. Real cross-section diagrams for the three topologies that already
exist, pulled straight from `geometry.py`'s own mask functions via `plot_geometry.py` (same
families already built/verified, not re-drawn by hand); a hand-built schematic for the one that
doesn't (embedded-Cerenkov, recreating the user's own sketch in this report's visual language).

Explicitly states the matrix is not a green light to run all ten rows unsupervised -- user
direction, 2026-10-12: each batch gets its own check-in.
