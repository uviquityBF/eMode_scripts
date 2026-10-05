# SHG Mode Survey — Plan

Status (2026-10-05): Step 1 and Step 1b implemented for the `ridge` family and trial-run; Step 2's
`loaded` family implemented, geometry-verified, and both its scattering loss (an EMode-version
bug on this machine, fixed by updating to v1.0.4) and bulk SH-absorption loss (TiO2 etc., wired as
a post-solve perturbation after EMode-side approaches proved to be dead ends) are now trustworthy.
First full `loaded` sweep (`loaded_sweep1`, TiO2 strip) ran overnight: much higher lossless NCE
than `ridge`, but loss-limited peak efficiency collapses ~40,000x below `ridge`'s best once real
TiO2 absorption is included -- TiO2 looks like the wrong strip material, not just a materials-data
gap (see "Implementation status & findings" at the end, 2026-10-04/05 entries). Builds on
`loss_vs_dimensions/` and borrows from `phase_matching_pipeline/`.

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
  way the design intends.
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
  %/W/cm^2 is the best NCE in this family" as final.

`cerenkov_run.py loaded_sweep1 --all` (all 40 pumps across the 8 geometries -- notably slower per
pump than ridge's ~40s, 4-7 min each here, worth a look if this module gets used routinely for
`loaded`): confirms the ridge family's conclusion holds here too -- kappa_C tops out at ~0.078
%/W/cm (TM10, t=600/h_s=150/w_s=1000), negligible next to the guided channel. 35/40 rows have
energy balance within ~3% of 1; the 5 that don't all have |kappa_C| <~1e-5 %/W/cm (near the
solver's noise floor at that signal size, same as the energy-balance caveat already noted for
ridge) -- not a new issue, just the existing caveat showing up for real on this family's first run
through Step 1b.
