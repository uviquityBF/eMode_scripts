"""Input Assumptions report: the materials and loss-model assumptions behind every shg_mode_survey
results report, in one place, so a reader doesn't have to dig through survey_config.py comments,
PLAN.md, and the loss_vs_dimensions notebook separately. Every future per-sweep PDF (see
build_subfigure_report.py) should reference this document rather than re-deriving any of it.

Requested 2026-10-12 after a real discrepancy was found between survey_config.py's pump-side
absorption-mechanism values and the ones documented in the "Loss Model Summary & Results" memo
(Google Drive, internal, 2026-09-22) -- see PLAN.md for the full writeup. Per-the-user's direction
(2026-10-12): not reconciling the two, just quantifying and logging how much they actually differ
(see compare_pump_loss_assumptions.py), and keeping survey_config.py's current values.

Status as of this version: AlN/SiNx/TiO2 dispersion fits are committed and wired into at least one
geometry family. ScAlN index data exists (Baumler 2019, 8 compositions) but its UV k and chi(2)
d-tensor are open/disputed (see PLAN.md's chi(2) table). GaAlN has no dispersion fit yet -- this
report documents that gap rather than filling it.

Usage: python build_assumptions_report.py [out.pdf]
"""
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

import geometry as geo
from compare_pump_loss_assumptions import (CODE_MECHANISMS, DOC_MECHANISMS,
                                            CODE_SIGMA_SIDEWALL_NM, DOC_SIGMA_SIDEWALL_NM, main as run_comparison)

INK, INK_MUTED, INK_FAINT = '#161a2e', '#5c6180', '#9094ad'
BORDER = '#dcdfeb'
ACCENT = '#5b3df0'
WARN = '#c9680e'

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9, 'text.color': INK, 'axes.edgecolor': BORDER,
    'axes.labelcolor': INK_MUTED, 'xtick.color': INK_MUTED, 'ytick.color': INK_MUTED,
    'axes.grid': True, 'grid.color': BORDER, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
    'figure.facecolor': 'white', 'savefig.facecolor': 'white',
})


def eval_n(eq, lam_nm):
    """Local stand-in for geo.eval_index_equation -- that function's restricted eval(eq,
    {'__builtins__': {}}, ...) was found to intermittently raise KeyError('__import__') when
    called many times in sequence within this script (reproducible, but root cause not pinned
    down -- doesn't reproduce in a minimal snippet, only here). Not worth risking a change to the
    shared geometry.py function used throughout the live EMode pipeline over a plotting script's
    quirk, so this local copy just uses real builtins instead of an empty restricted set."""
    x = lam_nm / 1000.0
    return float(np.real(eval(eq, {'__builtins__': __builtins__, 'np': np}, {'x': x})))


def eval_k(eq, lam_nm):
    x = lam_nm / 1000.0
    return float(np.imag(eval(eq, {'__builtins__': __builtins__, 'np': np}, {'x': x})))


def style_ax(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.spines['left'].set_color(BORDER)
    ax.spines['bottom'].set_color(BORDER)


def shade_bands(ax):
    ax.axvspan(215, 235, color='#eda100', alpha=0.10, lw=0)
    ax.axvspan(430, 470, color='#2a78d6', alpha=0.08, lw=0)


def text_block(fig, x, y, lines, fontsize=10, color=INK, linespacing=1.6, mono=False, weight='normal'):
    fig.text(x, y, '\n'.join(lines), fontsize=fontsize, color=color, va='top',
              linespacing=linespacing, family='monospace' if mono else None, weight=weight)


def page1_title(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.93
    fig.text(0.08, y, 'Input Assumptions', fontsize=24, weight='bold', color=INK)
    y -= 0.045
    fig.text(0.08, y, 'shg_mode_survey · loss model + material dispersion, referenced by every results report',
              fontsize=11, color=INK_MUTED)
    y -= 0.06
    body = [
        "Every per-sweep PDF this project produces should cite this document rather than re-stating",
        "or re-deriving any assumption. Two bands matter throughout: SH = 215–235 nm (deep UV),",
        "pump = 430–470 nm (true blue) — shaded orange and blue respectively in every chart below.",
    ]
    text_block(fig, 0.08, y, body, fontsize=10.5)
    y -= 0.14

    fig.text(0.08, y, 'CONTENTS', fontsize=9, weight='bold', color=INK_FAINT)
    y -= 0.03
    contents = [
        "0. Figures of merit — what NCE and peak efficiency mean, and why only one moves with loss",
        "1. Loss model — scattering + absorption mechanism assumptions, with citations",
        "2. Pump-loss assumption comparison (code vs. the Loss Model Summary memo)",
        "3. Core/cladding material dispersion — AlN, SiNx, TiO2",
        "3b. SH-loss calibration — why AlN's measured k isn't used, what is, and why",
        "4. ScAlN composition sweep — index ready, k/d33 open",
        "5. GaAlN — not yet sourced (status page)",
        "6. Nonlinear (chi(2)) tensor summary",
        "7. Notes & provenance",
    ]
    text_block(fig, 0.08, y, contents, fontsize=10)
    y -= 0.275

    fig.text(0.08, y, 'STATUS AT TIME OF WRITING', fontsize=9, weight='bold', color=WARN)
    y -= 0.03
    status = [
        "AlN, SiNx, TiO2 dispersion: committed, wired into at least one geometry family.",
        "AlN's own UV k(lambda): a real MOCVD-measured candidate was picked (AM187-LT6, section 3) --",
        "  k_e >> k_o, ~0.04-0.05 at SH, ~0.012 at pump. Wired as an opt-in mechanism (geom.params",
        "  ['aln_lossy']) and used to REPROCESS completed runs, but NOT adopted as the working",
        "  assumption at either band: its SH-band implication (~100,000 dB/cm) was checked against",
        "  real device output and found 3-4 orders of magnitude too high (section 3b). SH loss",
        "  instead uses a flat, empirically-calibrated 100 dB/cm placeholder; pump loss stays at its",
        "  prior native (scattering + interface-defect mechanism) value, unchanged.",
        "ScAlN: index fitted (8 compositions, Baumler 2019). UV k and chi(2) d33/d31 vs. Sc fraction",
        "  are disputed between sputtered and MBE literature — see section 6.",
        "GaAlN: no dispersion fit exists yet. Section 5 documents the gap, not a fix.",
    ]
    text_block(fig, 0.08, y, status, fontsize=9.5, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def page0_figures_of_merit(pdf):
    """NCE vs. loss-limited peak efficiency -- added 2026-10-12 after a reader of
    aln_loss_report.pdf had to ask what NCE actually means and why it doesn't move when loss
    does. A correct explanation already existed (aln_loss_report.pdf's own header text, a
    buried PLAN.md changelog line, scattered docstrings/captions, and the 2026-10-05 field-guide
    artifact) but nowhere in this report -- the one document whose own docstring says every
    other report should reference it instead of re-deriving this. Unnumbered ("0.") to avoid
    renumbering every other section's cross-references; it belongs conceptually first."""
    LH = 0.0305  # ~one text_block line at fontsize=9.5/linespacing=1.6, empirically fit to this page

    fig = plt.figure(figsize=(11, 8.5))
    y = 0.94
    fig.text(0.08, y, '0. Figures of merit: what NCE and peak efficiency mean', fontsize=16,
              weight='bold', color=INK)
    y -= 0.055

    fig.text(0.08, y, 'A phase-matched crossing', fontsize=11, weight='bold', color=INK)
    y -= 0.024
    lines = [
        "The pump mode's effective index n_eff,pump(2*lambda) equals the SH mode's",
        "n_eff,SH(lambda) -- pump and SH stay in step as they co-propagate, so generated SH",
        "keeps adding constructively instead of periodically cancelling. Every crossings.csv",
        "row is one such pump/SH mode pair.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    y -= len(lines) * LH + 0.018

    fig.text(0.08, y, 'NCE -- eta_pct_per_W_cm2 (normalized conversion efficiency)', fontsize=11,
              weight='bold', color=INK)
    y -= 0.024
    lines = [
        "A pure field-overlap quantity: how well the pump-driven nonlinear polarization",
        "(chi(2):E_pump^2) lines up with the SH mode's own field shape, for 1W-normalized",
        "modes (%/W/cm^2 -- shg_physics.eta_norm_per_W_m2/eta_to_pct_per_W_cm2). Computed",
        "from the two mode PROFILES at one cross-section -- propagation distance and device",
        "length never enter. overlap_shape (0-1) is the companion dimensionless version.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    y -= len(lines) * LH + 0.018

    fig.text(0.08, y, 'Loss-limited peak efficiency -- peak_efficiency_pct_per_W', fontsize=11,
              weight='bold', color=INK)
    y -= 0.024
    lines = ["What you'd actually measure from a real device of length L, pump/SH power-loss",
             "coefficients alpha_p/alpha_s (shg_physics.loss_limited_length):"]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    y -= len(lines) * LH + 0.012
    fig.text(0.12, y, "P_SH(L) = eta * P_pump^2 * L_eff(L)^2", fontsize=10.5, family='monospace',
              color=ACCENT)
    y -= 0.03
    fig.text(0.12, y, "L_eff(L) = [exp(-alpha_p*L) - exp(-alpha_s*L/2)] / (alpha_s/2 - alpha_p)",
              fontsize=10.5, family='monospace', color=ACCENT)
    y -= 0.045
    lines = [
        "L_eff -> L as loss -> 0 (plain quadratic P_SH ~ L^2); with real loss it rises, peaks",
        "at an optimum length L_opt (L_opt_mm), then DECLINES for longer devices -- not a",
        "plateau. peak_efficiency_pct_per_W = eta * L_eff(L_opt)^2: 'is this design any good'",
        "for a real device, as opposed to eta alone.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    y -= len(lines) * LH + 0.018

    fig.text(0.08, y, 'Why NCE never moves when the loss model changes', fontsize=11, weight='bold',
              color=WARN)
    y -= 0.024
    lines = [
        "eta and L_eff come from disjoint inputs -- eta from the transverse mode SHAPES alone",
        "(no z-dependence), L_eff from alpha_p/alpha_s alone (never looks at mode shape).",
        "Changing the loss model -- AlN's own absorption, sidewall roughness, a different",
        "cladding -- can only move L_eff (hence L_opt and peak efficiency); it has no path",
        "back to eta. Every loss-comparison report here (e.g. aln_loss_report.pdf) shows NCE",
        "exactly unchanged between scenarios, while peak efficiency moves -- by construction.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)

    pdf.savefig(fig)
    plt.close(fig)


def page2_loss_model(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.94
    fig.text(0.08, y, '1. Loss model: scattering + absorption', fontsize=16, weight='bold', color=INK)
    y -= 0.05

    fig.text(0.08, y, 'Scattering (native EMode, Volume Current Method)', fontsize=11, weight='bold', color=INK)
    y -= 0.03
    text_block(fig, 0.08, y, [
        f"Sidewall (vertical): {CODE_SIGMA_SIDEWALL_NM:g} nm RMS roughness, 50 nm correlation length.",
        "Top/bottom (horizontal): 0.3 nm RMS roughness, 10 nm correlation length.",
        "Values as currently used in survey_config.py. The \"Loss Model Summary\" memo (see section 2)",
        f"used {DOC_SIGMA_SIDEWALL_NM:g} nm sidewall RMS instead — everything else matches.",
    ], fontsize=9.5, color=INK_MUTED)
    y -= 0.14

    fig.text(0.08, y, 'Absorption (non-uniform, growth-interface defects)', fontsize=11, weight='bold', color=INK)
    y -= 0.03
    text_block(fig, 0.08, y, [
        "Each mechanism: a local power-absorption coefficient (alpha0, dB/m) at a physical boundary,",
        "decaying into the core (exponential or step) over a penetration depth L (nm). Modal loss is",
        "the Poynting-flux-weighted average of that profile over the mode. Currently active in",
        "survey_config.py's pump_absorption_mechanisms (4 of them; sh_absorption_mechanisms is empty",
        "— this interface-defect model contributes ZERO absorption at the SH wavelength). SH loss's",
        "own flat, confinement-weighted 100 dB/cm calibrated absorption is a SEPARATE mechanism, not",
        "part of this interface-defect list -- see section 3b:",
    ], fontsize=9.5, color=INK_MUTED)
    y -= 0.20

    rows = [
        ('Dislocations', '2000 dB/m, exp, 40nm', 'Chen et al., Opt. Express 27(12), 17262 (2019) — but',
         'literature treats this as SCATTERING with a TM>TE dependence, not modeled here as such.'),
        ('C impurities', '3500 dB/m, step, 50nm', 'Robinson et al., arXiv:2606.19615 (2026)', ''),
        ('Si impurities', '3500 dB/m, step, 50nm', 'No literature value found.', 'Engineering placeholder.'),
        ('O impurities', '5000 dB/m, step, 50nm', 'Bickermann et al., Appl. Phys. Lett. 95, 262104 (2009)', ''),
    ]
    for name, val, cite1, cite2 in rows:
        fig.text(0.08, y, name, fontsize=9.5, weight='bold', color=INK)
        fig.text(0.28, y, val, fontsize=9, color=INK_MUTED, family='monospace')
        fig.text(0.08, y - 0.022, cite1, fontsize=8.5, color=ACCENT)
        y -= 0.022
        if cite2:
            fig.text(0.08, y - 0.022, cite2, fontsize=8.5, color=INK_FAINT)
            y -= 0.022
        y -= 0.028

    y -= 0.01
    fig.text(0.08, y, 'Not currently modeled at all (zero sidewall mechanisms in survey_config.py):',
              fontsize=9, color=WARN, weight='bold')
    y -= 0.025
    text_block(fig, 0.08, y, [
        "Oxidation ingress, sidewall contamination, sidewall damage — all three have no literature",
        "support either; the Loss Model Summary memo carries two of them at nonzero values (see",
        "section 2's comparison). Dropped here, not evaluated as zero-impact — just never added.",
    ], fontsize=8.5, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def page3_comparison(pdf):
    df = run_comparison()
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.94
    fig.text(0.08, y, '2. Pump-loss assumption comparison', fontsize=16, weight='bold', color=INK)
    y -= 0.04
    text_block(fig, 0.08, y, [
        "code = survey_config.py's current 4-mechanism set (section 1). doc = the \"Loss Model Summary",
        "& Results\" memo's own \"Actual Inputs Used\" table (7 mechanisms, different roughness).",
        "Computed from trial_grid's already-exported TM00 pump fields (ridge, h_core=350 nm fixed,",
        "no new EMode calls). Scattering's roughness difference (2.5 vs 2.0 nm sidewall) is applied",
        "as an analytic (RMS)^2 scaling to the combined EMode-native value, not a fresh VCM solve —",
        "a rougher approximation than the absorption-side comparison; see the script's docstring.",
    ], fontsize=9, color=INK_MUTED)
    y -= 0.20  # clears the 6-line text block above (was wrongly dropped in an earlier edit)
    axes_bottom = 0.22
    ax = fig.add_axes((0.1, axes_bottom, 0.8, y - axes_bottom))
    ax.plot(df['w_core'], df['total_code_dB_per_cm'], 'o-', color=ACCENT, label='code (current)', lw=2)
    ax.plot(df['w_core'], df['total_doc_dB_per_cm'], 's--', color=WARN, label='doc (memo)', lw=2)
    ax.set_xlabel('ridge core width w_core [nm]  (h_core = 350 nm)')
    ax.set_ylabel('total pump loss [dB/cm]')
    ax.legend(frameon=False, fontsize=9)
    style_ax(ax)

    ratio_lo, ratio_hi = df['ratio_doc_over_code'].min(), df['ratio_doc_over_code'].max()
    text_block(fig, 0.08, 0.14, [
        f"doc/code ratio across this width range: {ratio_lo:.2f}–{ratio_hi:.2f}x — doc consistently",
        "LOWER than code, not higher, despite its extra sidewall terms (its exponential-decay,",
        "shorter-penetration-depth choices for C/Si/O more than offset that). Not an order-of-",
        "magnitude gap. Per 2026-10-12 direction: logged here, current code assumptions kept as-is.",
    ], fontsize=8.5, color=INK_MUTED, linespacing=1.5)
    pdf.savefig(fig)
    plt.close(fig)


def precompute_dispersion_data():
    """All equation evals happen here (using the local eval_n/eval_k helpers above, not
    geo.eval_index_equation -- see that function's note), before any plotting starts."""
    lam_core = np.linspace(200, 500, 400)
    n_o = [eval_n(geo.AlN_EQ_O, l) for l in lam_core]
    n_e = [eval_n(geo.AlN_EQ_E, l) for l in lam_core]
    sinx = json.load(open('materials/SiNx_Beliaev2022_sellmeier_fit.json'))
    tio2 = json.load(open('materials/TiO2_Siefke2016_sellmeier_fit.json'))
    sinx_n = [eval_n(sinx['emode_equation_real'], l) for l in lam_core]
    sinx_k = [eval_k(sinx['emode_equation_complex'], l) for l in lam_core]
    tio2_n = [eval_n(tio2['emode_equation_real'], l) for l in lam_core]
    tio2_k = [eval_k(tio2['emode_equation_complex'], l) for l in lam_core]

    sc = json.load(open('materials/ScAlN_Baumler2019_sellmeier_fits.json'))
    lam_sc = np.linspace(207, 500, 400)
    fractions = sorted(sc['fits'].keys(), key=float)
    sc_curves = []
    for frac in fractions:
        fit = sc['fits'][frac]
        n = [eval_n(fit['emode_equation_real'], l) for l in lam_sc]
        k = [eval_k(fit['emode_equation_complex'], l) for l in lam_sc]
        sc_curves.append((frac, n, k))

    aln_meas = pd.read_csv('materials/AlN_AM187_LT6_measured_nk.csv')

    # Equivalent k of geo.SH_ABSORPTION_CALIBRATED_DB_PER_CM (flat 100 dB/cm) -- what's ACTUALLY
    # used for SH-band loss when geom.params['sh_absorption_calibrated'] is set (see survey.py's
    # bulk_absorption_loss). Only meaningful/applied in the SH band (215-235nm) -- plotted only
    # there, not extrapolated across lam_core like the other curves.
    lam_sh_only = np.linspace(215.0, 235.0, 50)
    sh_cal_k = [geo.k_from_loss_dB_per_m(geo.sh_absorption_calibrated_dB_per_m(l), l) for l in lam_sh_only]

    return {
        'lam_core': lam_core, 'n_o': n_o, 'n_e': n_e, 'sinx_n': sinx_n, 'sinx_k': sinx_k,
        'tio2_n': tio2_n, 'tio2_k': tio2_k, 'lam_sc': lam_sc, 'sc_curves': sc_curves, 'sc_meta': sc,
        'aln_meas': aln_meas, 'lam_sh_only': lam_sh_only, 'sh_cal_k': sh_cal_k,
    }


def page4_core_cladding(pdf, data):
    lam = data['lam_core']
    n_o, n_e = data['n_o'], data['n_e']
    sinx_n, sinx_k = data['sinx_n'], data['sinx_k']
    tio2_n, tio2_k = data['tio2_n'], data['tio2_k']
    aln_m = data['aln_meas']
    lam_sh_only, sh_cal_k = data['lam_sh_only'], data['sh_cal_k']
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle('3. Core/cladding material dispersion', fontsize=14, weight='bold', x=0.08, ha='left')

    ax = axs[0]
    ax.plot(lam, n_o, color='#7570B3', ls=':', lw=1.3, alpha=0.6, label='AlN n_o (hardcoded, lossless)')
    ax.plot(lam, n_e, color='#7570B3', ls='--', lw=1.3, alpha=0.6, label='AlN n_e (hardcoded, lossless)')
    ax.plot(aln_m['wavelength_nm'], aln_m['n_o'], color='#C23A73', lw=1.8, label='AlN n_o (measured, AM187-LT6)')
    ax.plot(aln_m['wavelength_nm'], aln_m['n_e'], color='#C23A73', ls='--', lw=1.8, label='AlN n_e (measured, AM187-LT6)')
    ax.plot(lam, sinx_n, color='#009E73', label='SiNx (Beliaev 2022)')
    ax.plot(lam, tio2_n, color='#D55E00', label='TiO2 (Siefke 2016)')
    shade_bands(ax)
    ax.set_xlabel('wavelength [nm]'); ax.set_ylabel('n')
    # fitted Sellmeier forms have a resonance pole near the UV band edge (denominator -> 0) --
    # a real feature of the fit, not a plotting bug, but it dwarfs the device-relevant index
    # range if left unclipped; capped here to the range that's actually useful to read off.
    ax.set_ylim(1.0, 3.2)
    ax.legend(fontsize=6.5, frameon=False)
    style_ax(ax)

    ax = axs[1]
    ax.plot(aln_m['wavelength_nm'], aln_m['k_o'], color='#C23A73', lw=1.8, alpha=0.6, label='AlN k_o (measured, AM187-LT6)')
    ax.plot(aln_m['wavelength_nm'], aln_m['k_e'], color='#C23A73', ls='--', lw=1.8, alpha=0.6, label='AlN k_e (measured, AM187-LT6)')
    ax.plot(lam, sinx_k, color='#009E73', label='SiNx')
    ax.plot(lam, tio2_k, color='#D55E00', label='TiO2')
    ax.plot(lam_sh_only, sh_cal_k, color=INK, lw=2.6, solid_capstyle='round',
            label='SH absorption, calibrated — 100 dB/cm (USED in simulation)')
    ax.set_yscale('log')
    shade_bands(ax)
    ax.set_xlabel('wavelength [nm]'); ax.set_ylabel('k  (log scale)')
    ax.set_ylim(1e-5, 3.0)
    ax.set_title('AlN\'s measured k (AM187-LT6) is NOT used for SH loss — it implied ~100,000 dB/cm,\n'
                '3-4 orders of magnitude above what fabricated devices actually permit (section 3b)',
                fontsize=8, color=WARN)
    ax.legend(fontsize=6.5, frameon=False, loc='lower right')
    style_ax(ax)

    fig.tight_layout(rect=(0, 0.06, 1, 0.91))
    fig.text(0.08, 0.02,
              "AlN measured curves: sample AM187 (MOCVD, new model, 6.4.26), position LT(6) -- the lowest, "
              "non-negative k_e among all MOCVD-labeled positions in the team's own ellipsometry\n"
              "repo (github.com/uviquityBF/ellipsometry_data), selected 2026-10-12. Shown for reference only "
              "(right panel, log scale) -- NOT what the simulation actually uses for SH loss; see section 3b.",
              fontsize=7.5, color=INK_FAINT)
    pdf.savefig(fig)
    plt.close(fig)


def page3b_sh_loss_calibration(pdf, data):
    lam_sh_only, sh_cal_k = data['lam_sh_only'], data['sh_cal_k']
    aln_m = data['aln_meas']
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.94, '3b. What SH loss the simulation actually uses', fontsize=16, weight='bold', color=INK)
    y = 0.90

    body = [
        "AlN's own measured k_e (AM187-LT6, section 3) implies roughly 100,000 dB/cm of SH-band",
        "absorption for a representative crossing (ridge h=350 w=500nm, TM00->TM04 -- the closest",
        "match in this project's dataset to real fabricated/tested devices). That number is NOT",
        "used -- it was checked against real device measurements and found to be 3-4 orders of",
        "magnitude too high.",
    ]
    text_block(fig, 0.08, y, body, fontsize=10.5)
    y -= 0.16

    fig.text(0.08, y, 'How the empirical bound was derived (2026-10-12)', fontsize=10.5, weight='bold', color=INK)
    y -= 0.03
    body2 = [
        "A fabricated device (same geometry) measures ~200 nW SH output at best, ~10s of nW",
        "typically, under ~200 mW incident pump power (10-50% coupling efficiency into the",
        "waveguide, unmeasured) over a ~2 mm interaction length. Inverting this project's own",
        "loss-limited-efficiency model (shg_physics.loss_limited_length, evaluated at the real",
        "fixed 2mm length -- not an idealized optimum) for the SH loss consistent with that output",
        "bounds alpha_SH to roughly 15-680 dB/cm across the coupling-efficiency uncertainty --",
        "nowhere near the ~100,000 dB/cm the ellipsometry sample implies.",
    ]
    text_block(fig, 0.08, y, body2, fontsize=9.5, color=INK_MUTED)
    y -= 0.21

    fig.text(0.08, y, 'Working value: 100 dB/cm, confinement-weighted (2026-10-12 decision)', fontsize=10.5,
              weight='bold', color=INK)
    y -= 0.03
    body3 = [
        "100 dB/cm is a round number inside that empirically-bounded range -- not a measurement of",
        "any specific physical mechanism (absorption, under-modeled scattering, or something else",
        "is equally plausible as the real cause). Applied as geometry.sh_absorption_calibrated_dB_per_m,",
        "confinement-weighted by the mode's power fraction in the AlN core exactly like AlN's own",
        "absorption would be (geom.core_mask) -- see survey.py's bulk_absorption_loss. Flat across",
        "the SH band (215-235nm) by construction, since it's a single working value rather than a",
        "fitted spectral shape. Applies ONLY to SH loss, never to pump -- it was back-calculated",
        "purely from SH output. EMode-native sidewall-roughness scattering at SH (already in the",
        "model throughout, unaffected by any of this -- see section 1) is ADDED on top, not replaced.",
    ]
    text_block(fig, 0.08, y, body3, fontsize=9.5, color=INK_MUTED)
    y -= 0.29

    ax = fig.add_axes((0.1, 0.06, 0.8, y - 0.06))
    ax.plot(aln_m['wavelength_nm'], aln_m['k_e'], color='#C23A73', ls='--', lw=1.5, alpha=0.5,
            label='AlN k_e (measured, AM187-LT6) — NOT used')
    ax.plot(lam_sh_only, sh_cal_k, color=INK, lw=2.6, solid_capstyle='round',
            label='100 dB/cm calibrated — USED for SH loss')
    ax.set_yscale('log')
    ax.axvspan(215, 235, color='#eda100', alpha=0.12, lw=0)
    ax.set_xlim(195, 245)
    ax.set_xlabel('wavelength [nm]'); ax.set_ylabel('k  (log scale)')
    ax.set_title('~1000x gap between the measured sample and what\'s actually used', fontsize=9.5, color=INK)
    ax.legend(fontsize=8, frameon=False, loc='center right')
    style_ax(ax)
    pdf.savefig(fig)
    plt.close(fig)
    plt.close(fig)


def page5_scaln(pdf, data):
    sc = data['sc_meta']
    lam = data['lam_sc']
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle('4. ScAlN composition sweep (index ready, k/d33 open)', fontsize=14, weight='bold', x=0.08, ha='left')

    cmap = plt.get_cmap('viridis')
    for i, (frac, n, k) in enumerate(data['sc_curves']):
        color = cmap(i / max(1, len(data['sc_curves']) - 1))
        axs[0].plot(lam, n, color=color, label=f"{float(frac)*100:.0f}% Sc")
        axs[1].plot(lam, k, color=color, label=f"{float(frac)*100:.0f}% Sc")

    for ax, ylab in zip(axs, ('n', 'k')):
        shade_bands(ax)
        ax.set_xlabel('wavelength [nm]'); ax.set_ylabel(ylab)
        style_ax(ax)
    # same resonance-pole clipping as page 4 (see that comment) -- real feature of the fits,
    # clipped here purely so the device-relevant range is actually legible.
    axs[0].set_ylim(1.5, 3.5)
    axs[1].set_ylim(-0.02, 0.4)
    axs[0].legend(fontsize=6.5, frameon=False, ncol=2)
    fig.tight_layout(rect=(0, 0.1, 1, 0.91))

    fig.text(0.08, 0.05,
              f"Source: {sc['source'][:110]}\nk resolution ~0.008, fit to 0 beyond {sc.get('transparent_nm','?')} nm "
              "(digitization limit, not a physical statement) — UV k and the chi(2) d33/d31-vs-Sc\n"
              "relationship are NOT from this fit and remain disputed; see section 6.",
              fontsize=8, color=INK_FAINT)
    pdf.savefig(fig)
    plt.close(fig)


def page6_gaaln(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.90
    fig.text(0.08, y, '5. GaAlN: not yet sourced', fontsize=16, weight='bold', color=INK)
    y -= 0.06
    text_block(fig, 0.08, y, [
        "No n(lambda)/k(lambda) dispersion fit exists for GaAlN (Al_xGa_1-xN) in this repo. This page",
        "documents the gap and what's known from a first literature pass, not a resolution.",
        "",
        "Two independent motivations were identified for keeping GaAlN in the design matrix even with",
        "d33 enhancement deprioritized (user direction, 2026-10-12):",
        "  1. Index engineering for a Cerenkov cladding (composition tunes index, not nonlinearity).",
        "  2. As a loading strip that reshapes the AlN mode — pulling it from the substrate interface,",
        "     or improving the AlN region's own overlap — without needing the strip itself active.",
        "",
        "Composition-dependent d33 (NIST, Sanford et al.): decreases with increasing Al fraction x,",
        "with a SIGN CHANGE near x ~ 0.65. The favorable (higher-d33) direction is toward Ga-rich",
        "compositions — but GaN's bandgap (~3.4 eV) is well below the SH photon energy at 215-235 nm",
        "(~5.5 eV), so Ga-rich AlGaN is almost certainly strongly absorbing exactly where this project",
        "needs transparency. The useful composition window (enough Ga for index tuning, not so much",
        "that it absorbs the SH) is likely narrow and has not been checked quantitatively.",
        "",
        "Needed before GaAlN can enter any sweep: n(lambda)/k(lambda) across 215-470 nm for a composition",
        "range still TBD (narrow, Al-rich, pending the transparency check above).",
    ], fontsize=10, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def page7_tensor(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.90
    fig.text(0.08, y, '6. Nonlinear (chi(2)) tensor summary', fontsize=16, weight='bold', color=INK)
    y -= 0.05
    text_block(fig, 0.08, y, [
        "wurtzite 6mm, c || y. Nonzero: d33; d31 = d32; d15 = d24. Py = eps0[d31(Ex^2+Ez^2) + d33 Ey^2],",
        "Px = 2 eps0 d15 Ex Ey, Pz = 2 eps0 d15 Ez Ey. Kleinman symmetry (d15=d31) assumed unless data",
        "says otherwise -- questionable near the SH band edge, treat d15 as separate.",
    ], fontsize=9.5, color=INK_MUTED)
    y -= 0.12

    rows = [
        ('AlN, bulk', '4.3 +/- 0.3 (@1030nm)', '~0.1', 'Majkic 2017, pssb 201700077'),
        ('AlN (working value)', '4.7', '~0.1', "user's current value -- used throughout this project"),
        ('AlN, sputter film', '5.1 +/- 0.4', '0.07', 'Yoshioka 2021, APL Mater. 9, 101104'),
        ('ScAlN sputter, 10/20/28/36% Sc', '15.8/42.5/46.9/62.3', '0.84/2.4/3.4/4.5', 'Yoshioka 2021'),
        ('ScAlN MBE on sapphire, 10/15/20/25%', '-2.5/5.1/-3.1/3.2 (noisy)', '1.6/3.3/4.9/1.6', 'Lee et al., arXiv 2607.14590 (2026)'),
    ]
    for name, d33, d31, src in rows:
        fig.text(0.08, y, name, fontsize=9, weight='bold', color=INK)
        fig.text(0.42, y, f"d33={d33} pm/V", fontsize=8.5, color=INK_MUTED, family='monospace')
        fig.text(0.68, y, f"d31={d31}", fontsize=8.5, color=INK_MUTED, family='monospace')
        y -= 0.022
        fig.text(0.08, y, src, fontsize=8, color=ACCENT)
        y -= 0.035

    y -= 0.02
    fig.text(0.08, y, 'DISAGREEMENT', fontsize=9, weight='bold', color=WARN)
    y -= 0.025
    text_block(fig, 0.08, y, [
        "Sputtered films show strong, clean d33 enhancement with Sc content. MBE films (direct on",
        "sapphire, bypassing the AlN buffer) show d33 scattered/suppressed instead, with d31 showing",
        "the strong, clean enhancement there. Neither growth method has been measured anywhere near",
        "215-235nm/430-470nm (both cited studies: ~1030nm pump). Implication: if d33 doesn't actually",
        "enhance for your growth process, a ScAlN core's real lever may be d31 (TE-pump -> TM-SH",
        "coupling, Py = d31*Ex^2), not d33 -- a different mode/polarization design than naively",
        "assuming 'bigger d33'. overlap_terms() in shg_physics.py already separates d33/d31/d15",
        "contributions per crossing, so this is mechanically supported once real tensor values are",
        "chosen -- the open question is which values, not whether the code can use them.",
    ], fontsize=9, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def page8_notes(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.92, '7. Notes & provenance', fontsize=16, weight='bold', color=INK)
    text_block(fig, 0.08, 0.86, [
        "Loss model source: \"Loss Model Summary & Results\", internal memo, Google Drive, created",
        "2026-09-22 (shorthand used throughout this project: [Loss Model Summary, 2026-09-22]).",
        "Companion doc: \"AlN_Absorption_Literature_Review\" (same Drive folder).",
        "",
        "Material fits: materials/fit_sinx_sellmeier.py (Beliaev et al., Thin Solid Films 763,",
        "139568, 2022), materials/fit_tio2_sellmeier.py (Siefke et al., Adv. Opt. Mater. 4, 1780,",
        "2016), materials/fit_baumler_sellmeier.py (Baumler et al., J. Appl. Phys. 126, 045715,",
        "2019, digitized). AlN o/e equations hardcoded in geometry.py (AlN_EQ_O/AlN_EQ_E) --",
        "real-valued, lossless; deliberately kept unchanged for continuity with prior results",
        "(2026-10-12 decision) rather than switched to the measured n below -- see section 3b for",
        "where k (a separate, independent addition) is actually used instead.",
        "",
        "AlN measured n/k: materials/AlN_AM187_LT6_measured_nk.csv, exported 2026-10-12 from",
        "github.com/uviquityBF/ellipsometry_data (a sibling repo, cloned to ..\\ellipsometry_data,",
        "not inside this one) -- sample AM187 (MOCVD, new model, 6.4.26), wafer position LT(6),",
        "picked as the lowest non-negative k_e among all MOCVD-labeled positions in that repo's",
        "catalog (240 anisotropic positions checked). Raw WVASE ellipsometry export; k_e fit",
        "separately to a 3-Lorentzian form (materials/fit_aln_measured_k.py, decoupled from n) for",
        "simulation use -- geometry.AlN_K_E_EQ / aln_core_loss_dB_per_m.",
        "",
        "SH-loss calibration (section 3b): geometry.SH_ABSORPTION_CALIBRATED_DB_PER_CM = 100, chosen",
        "2026-10-12 against real fabricated-device measurements (user-supplied, not a literature or",
        "ellipsometry source) -- ~200nW best-case / ~10s of nW typical SH output, ~200mW incident",
        "pump power (10-50% coupling efficiency, unmeasured), ~2mm interaction length, ridge",
        "h=350 w=500nm geometry (closest dataset match). Derivation: inverting",
        "shg_physics.loss_limited_length at the real fixed device length for the SH loss consistent",
        "with that output. See PLAN.md's 2026-10-12 \"empirical SH-loss bound\" entries for the full",
        "numeric derivation (per-coupling-scenario table) this report's section 3b summarizes.",
        "",
        "Pump-loss comparison: compare_pump_loss_assumptions.py, computed from trial_grid's already-",
        "exported TM00 pump fields -- no new EMode calls. Re-run that script directly to regenerate",
        "runs/pump_loss_assumption_comparison.csv.",
        "",
        "This report: build_assumptions_report.py. Regenerate after any change to the loss model or",
        "material fits referenced above -- every per-sweep results PDF should cite this document's",
        "generation date rather than re-deriving any of this.",
    ], fontsize=10, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'runs/input_assumptions_report.pdf'
    data = precompute_dispersion_data()
    with PdfPages(out) as pdf:
        page1_title(pdf)
        page0_figures_of_merit(pdf)
        page2_loss_model(pdf)
        page3_comparison(pdf)
        page4_core_cladding(pdf, data)
        page3b_sh_loss_calibration(pdf, data)
        page5_scaln(pdf, data)
        page6_gaaln(pdf)
        page7_tensor(pdf)
        page8_notes(pdf)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
