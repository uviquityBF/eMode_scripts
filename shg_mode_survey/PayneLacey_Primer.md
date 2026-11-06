# Sidewall scattering and its wavelength scaling — a primer on the Payne–Lacey framework

Written for: someone who wants to see the math that drives "how does scattering scale with wavelength" and know exactly where it lives in the repo.

## 1. Three different things in this repo are called "scattering"

| What | Where | Used for | Status |
|---|---|---|---|
| EMode-native `em.scattering()` | `survey.native_scattering`, `loss_vs_dimensions/sweep_loss_vs_dimensions.py` | **Every number in the SHG survey** | EMode's own implementation; closed box, we cannot see its math |
| Payne–Lacey *adapted* to the real 2D mode | `loss_vs_dimensions/scattering_model.py` (265 lines) | Cross-check on the exported field profile | Physics structure confirmed; overall prefactor uncalibrated (`calibrate_scattering.py` fits it) |
| Payne–Lacey 1D slab, closed form I derived | `shg_mode_survey/payne_lacey_explorer.ipynb` | Learning the λ, Lc, width dependence | EMode-free; not checked against Payne & Lacey's printed equations (paywalled / garbled OCR) |

The notebook is the one to read and edit. Reference paper (in `literature/`, untracked): Melati, Melloni, Morichetti, *Real photonic waveguides: guiding light through imperfections*, Adv. Opt. Photon. 6, 15 (2014).

## 2. The physics in one paragraph

A rough wall is a thin sheet of polarization current. A guided mode (propagation constant β = n_eff·k₀) can only radiate into a cladding plane wave (wavevector n₂k₀·cosθ along z) if the roughness supplies the difference in spatial frequency, k = β − n₂k₀cosθ. So the loss is proportional to: (roughness variance) × (field intensity *at the wall*, normalised to guided power) × (the roughness power spectrum sampled over the k-window the mode can scatter with).

## 3. The formula (notebook cell 2; `scattering_model.py:172-175` is the same expression with Ψ ≡ 2)

    α = [k₀⁴ (n₁²−n₂²)² / (4π β)] · [|E(wall)|² / ∫|E|²dx] · ∫₀^π PSD(β − n₂k₀cosθ) Ψ(θ) dθ

- **PSD(k)** for an exponential autocorrelation R(τ)=σ²e^(−|τ|/Lc): PSD = 2σ²Lc / (1+(k·Lc)²). Flat below the knee k ≈ 1/Lc, falls as 1/k² above it (`scattering_model.exponential_psd`).
- **k-window:** from β−n₂k₀ (θ=0) to β+n₂k₀ (θ=π). It moves to higher k at shorter wavelength.
- **Ψ(θ):** standing-wave factor of the radiated wave (=2 in a uniform medium). It makes the slab curves ripple with a ~100 nm period; the repo formula drops it.
- α ∝ σ². σ cancels from every wavelength *ratio*; only Lc and the geometry matter for the exponent.
- dB/cm = 4.343 · α[1/cm].

## 4. Why the wavelength scaling is not simply λ⁻⁴

Each factor scales differently, and some push opposite ways:

| Factor | Wavelength dependence |
|---|---|
| k₀⁴ / β | λ⁻⁴ · λ = **λ⁻³** (at fixed n_eff) |
| (n₁²−n₂²)² | grows toward the UV (material dispersion) |
| \|E(wall)\|² / ∫\|E\|² | at fixed width the mode confines more tightly at short λ, so the wall intensity *falls* |
| PSD integral S | depends on where the window sits relative to the knee 1/Lc. For Lc small (knee beyond the window) S is roughly flat; for Lc large the window sits on the 1/k² tail and S drops as the window moves up in k, offsetting k₀⁴ |

Result in the notebook (slab, AlN/SiO₂, d = 400 nm): the effective exponent p (α ∝ λ⁻ᵖ between 225 and 450 nm) is about **1.9** for Lc = 2 nm, stays near 2 for Lc ≲ 10 nm, and collapses toward 0 or negative for Lc ≳ 30 nm. EMode's native calculation on the real ridge gave about **1.1**. That disagreement between the two methods is unresolved (notebook caveats).

## 5. What this says about our measured data

The GL04 450 nm vs 635 nm cutback gives a loss ratio of 3.95 (exponent ≈ 4), but the 635 nm slope is poorly determined (R² = 0.24; rough 95% exponent range 1–10). Within this framework sidewall scattering gives p ≈ 2 at most for the roughness spectra explored; **p ≈ 4 would have to come from something else**: absorption with a rapidly rising k(λ) (band-tail or defect absorption), or Rayleigh-like volume scattering in the film. The width series does not contradict that: GL04's width-dependent (sidewall) term is only ~4 dB/cm between 250 and 700 nm, while the width-independent part is the bulk of the loss at 450 nm.

The one roughness parameter that decides the scattering exponent is **Lc** (where the knee sits relative to the k-window). It has not been measured on our devices; AFM or SEM-derived sidewall roughness spectra would constrain it directly.

## 6. How to use the notebook

Edit the parameter cell (cell 1): `SIGMA_NM`, `D_NM` (width), `LC_LIST`, `LAMS`, `PSD_KIND` ('exp' or 'gauss'), and `N1_FIXED` / `N2_FIXED` to freeze the indices. Then run all. The sections, in order: PSD and k-window; scattering vs λ with exponent p(λ); factor-by-factor decomposition (the plot that shows which piece drives the trend); the (λ, Lc) map and α(225)/α(450) vs Lc; and five suggested experiments at the end (hold the mode fixed, freeze dispersion, lower contrast, Gaussian PSD, search for any parameters giving p ≈ 3–4).

## 7. Known limits

- The slab is TE with the tangential field only. The real TM00 ridge mode also has a field component normal to the sidewall, plus corner, top and bottom contributions.
- Bulk-index contrast overstates absolute loss versus the real ridge. Compare ratios and exponents, not absolute dB/cm, with EMode.
- None of this includes absorption. See `absorption_model.py` and the survey's interface-absorption mechanisms for that side.
