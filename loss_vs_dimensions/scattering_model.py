"""Independent, EMode-free estimate of sidewall-scattering loss, adapted from the Payne-Lacey
perturbation-theory framework, computed from the real exported TM00 mode profile (no further
EMode calls needed once a point's fields are exported by sweep_loss_vs_dimensions.py).

THIS IS AN ADAPTATION, NOT A LITERAL TRANSCRIPTION of Payne & Lacey's 1994 closed-form result
-- worth understanding before trusting absolute numbers from it. Background (see conversation
history / commit message for the literature dig that produced this):

  - Lacey, J.P.R. & Payne, F.P., "Radiation loss from planar waveguides with random wall
    imperfections," IEE Proc. J 137(4), 282-288 (1990).
  - Payne, F.P. & Lacey, J.P.R., "A theoretical analysis of scattering loss from planar optical
    waveguides," Opt. Quantum Electron. 26, 977-986 (1994).

The confirmed PHYSICAL STRUCTURE (independently corroborated by a paper citing the compact
practical form, and a 2024 thesis re-deriving the full perturbation theory from the original
papers): radiated power per unit length is proportional to the roughness variance, the guided
mode's field intensity evaluated AT the rough boundary, and an integral of the roughness's power
spectral density (PSD -- the Fourier transform of its autocorrelation function) evaluated at the
phase-matching condition between the guided mode (propagation constant beta) and radiation modes
in the cladding (wavevector n_clad*k0 at each angle theta), normalized by the guided power:

    P_rad/L  ~  sigma^2 * |E_boundary|^2 * Integral_0^pi[ PSD(beta - n_clad*k0*cos(theta)) ] dtheta
    alpha [1/m] = (P_rad/L) / P_guided

For the assumed EXPONENTIAL autocorrelation (matching sidewall roughness in this pipeline), the
PSD has a standard closed form independent of any Payne-Lacey-specific derivation (this part is
plain Fourier-transform math, not something to doubt):

    PSD(k) = 2 * sigma^2 * Lc / (1 + (k*Lc)^2)

WHAT'S ADAPTED (not from the original papers): Payne & Lacey solved this for an IDEALIZED 1D
slab waveguide, deriving |E_boundary|^2 and P_guided analytically from slab-mode theory (using
the mode's transverse wavenumber/decay-constant parameters). That analytic derivation involves
several intermediate quantities (effective mode depth, a mode-shape-dependent geometry factor,
possible TE/TM-specific prefactors) that could not be reliably transcribed from available
sources (garbled OCR on the original equations -- see conversation history). Rather than risk
wrong constants there, this module evaluates |E_boundary|^2 and P_guided DIRECTLY from your real
2D EMode mode profile (exported by sweep_loss_vs_dimensions.py) instead of the idealized
1D-slab analytic substitutes -- arguably a better fit for an actual ridge geometry anyway, and
exactly reuses the "keep the TM00 mode profile stored... run variations in python alone"
workflow this was built for.

WHAT'S UNCALIBRATED: the overall leading numeric prefactor (the 1/(8*pi*eta0) below) is a
physically-motivated but NOT independently paper-verified constant. Use `calibration_factor` to
fix the absolute scale: pick one (h, w) point, take its EMode-native `scattering_loss_dB_per_m`
from loss_vs_dimensions_results.csv (which records the roughness_rms/correlation_length that
produced it), run this model at the SAME point/roughness with calibration_factor=1.0, and set
calibration_factor = (EMode's value) / (this model's uncalibrated value). Trends vs. width/height/
sigma/Lc are meaningful even before calibrating; the absolute scale is not, until you do.
"""

import numpy as np

FREE_SPACE_IMPEDANCE = 376.730313668  # [Ohm]
NM_TO_M = 1e-9


def sellmeier_n(eq_str, wavelength_nm):
    """Evaluate an EMode-style Sellmeier equation string (as passed to add_material's
    refractive_index_equation, e.g. sweep_loss_vs_dimensions.EQ_O) at wavelength_nm [nm] --
    add_material expects wavelength in microns (wavelength_unit='um'), hence the /1000.
    """
    return eval(eq_str, {}, {'x': wavelength_nm / 1000.0})


def sidewall_boundary_intensity(core_mask, Ex, Ey, Ez):
    """|E|^2 at every point along BOTH sidewalls (left and right edge of the core in each row
    that has core), plus how many boundary points were found -- for the line-integral in
    payne_lacey_sidewall_scattering_loss_dB_per_m. Uses total field intensity
    |Ex|^2+|Ey|^2+|Ez|^2 (a simplification -- see module docstring; not decomposed into a
    TE/TM-specific tangential-only projection).
    """
    ny, nx = core_mask.shape
    cols = np.arange(nx)
    intensities = []
    for row in range(ny):
        in_core = core_mask[row]
        if not in_core.any():
            continue
        core_cols = cols[in_core]
        for col in (core_cols.min(), core_cols.max()):
            e2 = (np.abs(Ex[row, col]) ** 2 + np.abs(Ey[row, col]) ** 2
                  + np.abs(Ez[row, col]) ** 2)
            intensities.append(e2)
    return np.array(intensities)


def top_bottom_boundary_intensity(core_mask, Ex, Ey, Ez):
    """|E|^2 at the TOP and BOTTOM edges of the core (max/min row with core in each column),
    returned SEPARATELY since they interface different surrounding materials -- the top surface
    sees the TopClad material, the bottom sees the substrate -- with generally different
    refractive indices. Same total-intensity simplification as sidewall_boundary_intensity.

    Grid convention: row index increases with y (confirmed in emode_export.py), and the core
    sits directly on the substrate (SUBSTRATE_HEIGHT), so the SMALLEST-row core pixel in a
    column is the bottom (substrate) edge and the LARGEST-row one is the top (TopClad) edge.

    Returns (top_e2, bottom_e2), each a 1D array of |E|^2 values, one per core-containing column.
    """
    ny, nx = core_mask.shape
    rows = np.arange(ny)
    top_vals, bottom_vals = [], []
    for col in range(nx):
        in_core = core_mask[:, col]
        if not in_core.any():
            continue
        core_rows = rows[in_core]
        bottom_row, top_row = core_rows.min(), core_rows.max()
        bottom_vals.append(np.abs(Ex[bottom_row, col]) ** 2 + np.abs(Ey[bottom_row, col]) ** 2
                            + np.abs(Ez[bottom_row, col]) ** 2)
        top_vals.append(np.abs(Ex[top_row, col]) ** 2 + np.abs(Ey[top_row, col]) ** 2
                         + np.abs(Ez[top_row, col]) ** 2)
    return np.array(top_vals), np.array(bottom_vals)


def guided_power(Sz, dx_nm, dy_nm):
    """Total guided power, integrating the (clipped non-negative) z-Poynting flux over the
    grid. Same convention as absorption_model.modal_absorption_loss's Sz handling.
    """
    Sz_pos = np.clip(np.real(Sz), 0, None)
    return float(Sz_pos.sum() * dx_nm * NM_TO_M * dy_nm * NM_TO_M)


def exponential_psd(k, sigma_nm, correlation_length_nm):
    """Power spectral density (Fourier transform of an exponential autocorrelation function
    R(tau) = sigma^2 * exp(-|tau|/Lc)) at spatial frequency k [1/m]. Standard closed-form
    Fourier transform of a one-sided exponential -- not itself a Payne-Lacey-specific result.
    """
    sigma_m = sigma_nm * NM_TO_M
    Lc_m = correlation_length_nm * NM_TO_M
    return 2 * sigma_m ** 2 * Lc_m / (1 + (k * Lc_m) ** 2)


def angular_scattering_integral(beta, n_clad, k0, sigma_nm, correlation_length_nm, n_theta=200):
    """Integral_0^pi PSD(beta - n_clad*k0*cos(theta)) dtheta -- how much roughness spectral
    content exists at the spatial frequency needed to scatter the guided mode (wavevector beta)
    into a radiation mode leaving the cladding at angle theta (wavevector n_clad*k0*cos(theta)).
    `beta`, `k0` in [1/m]; n_theta is the number of trapezoidal-integration points.
    """
    theta = np.linspace(0, np.pi, n_theta)
    k = beta - n_clad * k0 * np.cos(theta)
    return float(np.trapezoid(exponential_psd(k, sigma_nm, correlation_length_nm), theta))


def payne_lacey_sidewall_scattering_loss_dB_per_m(
        x, y, core_mask, Ex, Ey, Ez, Sz, n_eff, wavelength_nm, n_core, n_clad,
        sigma_rms_nm, correlation_length_nm, calibration_factor=1.0, n_theta=200):
    """Sidewall-scattering loss [dB/m] for this mode under the given roughness assumptions --
    see module docstring for what's confirmed physics vs. adaptation vs. uncalibrated.

    `n_core`/`n_clad` are plain scalar inputs (not looked up from EMode) -- pass your core and
    sidewall-cladding refractive indices at wavelength_nm directly. `sigma_rms_nm`/
    `correlation_length_nm` are scalars too; if comparing against a sweep row's roughness_rms/
    correlation_length (2-element lists), pick the element that corresponds to the sidewall
    (vertical) edges for your EMode version -- not resolved here, since this module doesn't
    depend on EMode's own list-ordering convention.
    """
    dx_nm = float(x[1] - x[0])
    dy_nm = float(y[1] - y[0])
    k0 = 2 * np.pi / (wavelength_nm * NM_TO_M)
    beta = k0 * n_eff

    boundary_e2 = sidewall_boundary_intensity(core_mask, Ex, Ey, Ez)
    if boundary_e2.size == 0:
        raise ValueError("no sidewall boundary points found -- check core_mask")
    boundary_integral = boundary_e2.sum() * dy_nm * NM_TO_M  # line integral ds ~ dy per point

    S_W = angular_scattering_integral(beta, n_clad, k0, sigma_rms_nm, correlation_length_nm,
                                       n_theta=n_theta)
    P_g = guided_power(Sz, dx_nm, dy_nm)

    P_rad_per_L = (calibration_factor * (k0 ** 3) / (8 * np.pi * FREE_SPACE_IMPEDANCE)
                   * (n_core ** 2 - n_clad ** 2) ** 2 * boundary_integral * S_W)
    alpha_per_m = P_rad_per_L / P_g  # power attenuation coefficient [1/m]
    return 10 * np.log10(np.e) * alpha_per_m  # -> dB/m (10*log10(e) = 4.343, matches the
    # "4.34" constant quoted in the literature's compact form)


def compute_scattering_loss(export_data, n_core, n_clad, sigma_rms_nm, correlation_length_nm,
                             calibration_factor=1.0, n_theta=200):
    """One-call convenience: pull everything this needs out of an npz export (as loaded by
    np.load -- an NpzFile or an already-materialized dict both work) and compute the SIDEWALL
    (vertical-edge) loss only. See compute_total_scattering_loss for vertical + horizontal.
    """
    return payne_lacey_sidewall_scattering_loss_dB_per_m(
        export_data['x'], export_data['y'], export_data['core_mask'],
        export_data['Ex'], export_data['Ey'], export_data['Ez'], export_data['Sz'],
        float(export_data['n_eff']), float(export_data['wavelength_pump']),
        n_core, n_clad, sigma_rms_nm, correlation_length_nm,
        calibration_factor=calibration_factor, n_theta=n_theta)


N_SUBSTRATE_DEFAULT = 1.776  # sapphire (Al2O3) ordinary index near 450 nm -- approximate
# literature constant, not derived from a Sellmeier fit like n_core; override if you have a
# better value for your actual substrate material/wavelength.


def payne_lacey_top_bottom_scattering_loss_dB_per_m(
        x, y, core_mask, Ex, Ey, Ez, Sz, n_eff, wavelength_nm, n_core, n_top_clad, n_substrate,
        sigma_rms_nm, correlation_length_nm, calibration_factor=1.0, n_theta=200):
    """Top+bottom (horizontal-edge) scattering loss [dB/m] -- same physical framework as
    payne_lacey_sidewall_scattering_loss_dB_per_m (see module docstring), applied to the core's
    top surface (interfacing n_top_clad) and bottom surface (interfacing n_substrate)
    SEPARATELY -- generally different materials (e.g. SiO2 top cladding vs. sapphire substrate)
    with different index contrast against the core -- then summed. Uses the SAME
    sigma_rms_nm/correlation_length_nm for both top and bottom, matching EMode's own
    roughness_rms/correlation_length convention (one 'horizontal' value covers both, not a
    separate top/bottom pair).
    """
    dx_nm = float(x[1] - x[0])
    dy_nm = float(y[1] - y[0])
    k0 = 2 * np.pi / (wavelength_nm * NM_TO_M)
    beta = k0 * n_eff

    top_e2, bottom_e2 = top_bottom_boundary_intensity(core_mask, Ex, Ey, Ez)
    if top_e2.size == 0 or bottom_e2.size == 0:
        raise ValueError("no top/bottom boundary points found -- check core_mask")
    top_integral = top_e2.sum() * dx_nm * NM_TO_M  # line integral ds ~ dx per point
    bottom_integral = bottom_e2.sum() * dx_nm * NM_TO_M
    P_g = guided_power(Sz, dx_nm, dy_nm)

    def radiated_power(n_clad_side, boundary_integral):
        S_W = angular_scattering_integral(beta, n_clad_side, k0, sigma_rms_nm,
                                           correlation_length_nm, n_theta=n_theta)
        return (calibration_factor * (k0 ** 3) / (8 * np.pi * FREE_SPACE_IMPEDANCE)
                * (n_core ** 2 - n_clad_side ** 2) ** 2 * boundary_integral * S_W)

    P_rad_per_L = radiated_power(n_top_clad, top_integral) + radiated_power(n_substrate, bottom_integral)
    alpha_per_m = P_rad_per_L / P_g
    return 10 * np.log10(np.e) * alpha_per_m


def payne_lacey_total_scattering_loss_dB_per_m(
        x, y, core_mask, Ex, Ey, Ez, Sz, n_eff, wavelength_nm, n_core, n_clad, n_substrate,
        sigma_vertical_nm, Lc_vertical_nm, sigma_horizontal_nm, Lc_horizontal_nm,
        calibration_factor_vertical=1.0, calibration_factor_horizontal=1.0, n_theta=200):
    """Sidewall (vertical) + top/bottom (horizontal) scattering, summed -- "total scatter."
    Two independent calibration factors since EMode's own vertical/horizontal edge calculations
    are fit against separately (see calibrate_scattering.py) and needn't share one constant.
    """
    vertical = payne_lacey_sidewall_scattering_loss_dB_per_m(
        x, y, core_mask, Ex, Ey, Ez, Sz, n_eff, wavelength_nm, n_core, n_clad,
        sigma_vertical_nm, Lc_vertical_nm, calibration_factor=calibration_factor_vertical,
        n_theta=n_theta)
    horizontal = payne_lacey_top_bottom_scattering_loss_dB_per_m(
        x, y, core_mask, Ex, Ey, Ez, Sz, n_eff, wavelength_nm, n_core, n_clad, n_substrate,
        sigma_horizontal_nm, Lc_horizontal_nm, calibration_factor=calibration_factor_horizontal,
        n_theta=n_theta)
    return vertical + horizontal


def compute_total_scattering_loss(export_data, n_core, n_clad, n_substrate,
                                   sigma_vertical_nm, Lc_vertical_nm,
                                   sigma_horizontal_nm, Lc_horizontal_nm,
                                   calibration_factor_vertical=1.0,
                                   calibration_factor_horizontal=1.0, n_theta=200):
    """One-call convenience: total (vertical + horizontal) scattering loss from an npz export."""
    return payne_lacey_total_scattering_loss_dB_per_m(
        export_data['x'], export_data['y'], export_data['core_mask'],
        export_data['Ex'], export_data['Ey'], export_data['Ez'], export_data['Sz'],
        float(export_data['n_eff']), float(export_data['wavelength_pump']),
        n_core, n_clad, n_substrate, sigma_vertical_nm, Lc_vertical_nm,
        sigma_horizontal_nm, Lc_horizontal_nm,
        calibration_factor_vertical=calibration_factor_vertical,
        calibration_factor_horizontal=calibration_factor_horizontal, n_theta=n_theta)
