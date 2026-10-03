# SHG Mode Survey — Plan

Status (2026-10-03): Step 1 and Step 1b implemented for the `ridge` family and trial-run (see
README.md for how to run, and "Implementation status & findings" at the end). Step 2 pending
geometry parameterization. Builds on `loss_vs_dimensions/` and borrows from
`phase_matching_pipeline/`.

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

- [ ] Geometry parameterization (colleague's slides) — needed for Step 2 only.
- [ ] k(λ) for AlN near 215 nm, ScAlN (Bäumler 2019 — paywalled; user checking), AlGaN, TiO2.
- [ ] d15 values (assume Kleinman for now); d-tensor dispersion to 450 → 225 nm.
- [ ] Decide default N_pump, N_SH, λ_SH step, and SH n_eff window margins after a first trial.

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
interface, `ridge`), `cerenkov_fdfd.py` + `cerenkov_run.py` (Step 1b), `summarize_run.py`,
`plot_crossing.py`; tests `test_shg_physics.py`, `test_cerenkov_fdfd.py`. How to run: README.md.

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
