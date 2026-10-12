"""PDF twin of the "SHG Mode Survey Field Guide" artifact (claude.ai), for the offline/git-tracked
record every other report in this project gets. Covers the parts of the guide that make sense as
a durable, point-in-time printed record -- overview, status, loss model (including the AlN
rejection/calibration story), geometry families (real cross-sections), and the most consequential
gotchas. Deliberately drops the artifact's "Running a survey" / "Notebook vs. hands-off" sections
(live operational instructions, terminal commands, PowerShell snippets -- useful on a page you can
click through, not on a static PDF) and the "Phase matching & figures of merit" theory (the
canonical, maintained version of that now lives in build_assumptions_report.py's own "0. Figures
of merit" section; this report just points to it rather than duplicating it a third time).

Usage: python build_field_guide_report.py [out.pdf]
"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

import geometry as geo
from plot_geometry import REGION_COLOR

INK, INK_MUTED, INK_FAINT = '#161a2e', '#5c6180', '#9094ad'
BORDER = '#dcdfeb'
ACCENT = '#5b3df0'
WARN = '#c9680e'
GOOD = '#0e9488'

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9, 'text.color': INK, 'axes.edgecolor': BORDER,
    'axes.labelcolor': INK_MUTED, 'xtick.color': INK_MUTED, 'ytick.color': INK_MUTED,
    'axes.grid': True, 'grid.color': BORDER, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
    'figure.facecolor': 'white', 'savefig.facecolor': 'white',
})


def style_ax(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.spines['left'].set_color(BORDER)
    ax.spines['bottom'].set_color(BORDER)


def text_block(fig, x, y, lines, fontsize=10, color=INK, linespacing=1.6, weight='normal'):
    fig.text(x, y, '\n'.join(lines), fontsize=fontsize, color=color, va='top',
              linespacing=linespacing, weight=weight)


def page1_overview(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.92
    fig.text(0.08, y, 'SHG Mode Survey: Field Guide', fontsize=22, weight='bold', color=INK)
    y -= 0.04
    fig.text(0.08, y, 'shg_mode_survey · PDF record of the claude.ai field-guide artifact, 2026-10-12',
              fontsize=10.5, color=INK_MUTED)
    y -= 0.055
    lines = [
        "Surveys every pump->SH mode pair for a given waveguide cross-section: finds every",
        "phase-matched pair in the SH window, then ranks by efficiency and loss. Two outcome",
        "families: guided->guided (the SH mode is itself bound, scored by NCE) and radiative",
        "(Cerenkov/leaky -- flagged and quantified, not discarded).",
    ]
    text_block(fig, 0.08, y, lines, fontsize=10.5)
    y -= len(lines) * 0.0305 + 0.025

    fig.text(0.08, y, 'Wavelength convention', fontsize=11, weight='bold', color=INK)
    y -= 0.026
    lines = [
        "SH wavelength sweeps the target window (default 215-235nm); pump = 2x SH wavelength",
        "(430-470nm). Mode labels TMmn/TEmn (m=lateral nodes, n=vertical). AlN's c-axis is y, so",
        "d33 couples Ey.Ey -> Py.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    y -= len(lines) * 0.0305 + 0.035

    fig.text(0.08, y, 'STATUS AT A GLANCE', fontsize=9, weight='bold', color=INK_FAINT)
    y -= 0.03
    pills = [
        ('ridge', 'done, Step 1/1b; strongest family under calibrated SH loss', GOOD),
        ('loaded', 'TiO2 strip ruled out (SH-absorbing); SiN ready, not run', WARN),
        ('hybrid', 'geometry fixed 2026-10-10 (now genuinely embedded); re-run pending', WARN),
        ('pedestal', 'legacy stacked structure (the old hybrid bug); kept for reference only', INK_FAINT),
        ('materials', "AlN's own measured SH absorption explored, REJECTED; 100 dB/cm calibrated value used instead", WARN),
    ]
    for name, desc, color in pills:
        fig.text(0.08, y, name, fontsize=10, weight='bold', color=color, family='monospace')
        fig.text(0.22, y, desc, fontsize=9.5, color=INK_MUTED)
        y -= 0.032

    y -= 0.02
    fig.text(0.08, y, 'WHAT THIS REPORT COVERS, AND WHAT IT DOESN\'T', fontsize=9, weight='bold',
              color=INK_FAINT)
    y -= 0.03
    lines = [
        "Covers: status, loss model (incl. the AlN rejection/calibration story), geometry",
        "families with real cross-sections, and the gotchas most likely to bite again.",
        "Deliberately omits operational material (how to launch a run, notebook vs. hands-off,",
        "terminal commands) -- that lives on the live artifact, where it's actually actionable;",
        "see PLAN.md or the artifact link for those. Figures of merit (NCE, peak efficiency) are",
        "defined once, canonically, in input_assumptions_report.pdf section 0 -- not repeated here.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def page2_status(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.94, 'Where things stand', fontsize=16, weight='bold', color=INK)
    y = 0.90

    rows = [
        ('ridge', GOOD, [
            "Done for Step 1/1b. Best design: TM00->TM04, h=350/w=500nm, 227.9nm, NCE",
            "4.8 %/W/cm^2. Still the strongest family once AlN's own SH-band loss is included:",
            "median calibrated peak efficiency ~41,000x above `loaded`'s, best-to-best ~4,700x",
            "(aln_loss_report.pdf). No TM02/TM20 partner phase-matches near the window.",
        ]),
        ('loaded', WARN, [
            "Geometry verified against EMode's own render. TiO2 strip sweep (8 geometries):",
            "lossless NCE far exceeds ridge (159 %/W/cm^2) but TiO2's own bulk SH absorption is",
            "so strong `loaded` stays worst-in-class even under the calibrated 100 dB/cm",
            "assumption. Next: SiN strip (ready, not run) or ScAlN (blocked on d33(Sc)).",
        ]),
        ('hybrid', WARN, [
            "AlN core embedded on the sides+above by a SiN shell -- tests the Honda et al. 2025",
            "TM00->TM20 mechanism. A geometry bug (core stacked ON the shell, not embedded)",
            "went undetected through several runs; fixed 2026-10-10. Not re-run since the fix --",
            "queued, Simulation Study Plan row 6, launching with the calibrated SH-loss default.",
        ]),
        ('pedestal', INK_FAINT, [
            "The stacked structure `hybrid` was accidentally building pre-fix -- renamed to its",
            "own family 2026-10-12 rather than discarded (real hardware, wrong mechanism). 3",
            "runs, 416 refined crossings, AlN-lossless only: field exports absent on both",
            "machines, re-solve costed at ~9.5hr EMode time for a family being superseded.",
        ]),
        ('materials', WARN, [
            "AlN/sapphire/SiO2 built in. TiO2, ScAlN (not wired into a geometry yet) fit from",
            "literature. AlN's own UV k: AM187-LT6 MOCVD sample fit and wired as an opt-in",
            "mechanism, but its SH-band implication (~100,000 dB/cm) was checked against real",
            "device output and found 3-4 orders of magnitude too high. NOT USED -- a flat,",
            "empirically-calibrated 100 dB/cm placeholder is the standing assumption instead.",
        ]),
        ('EMode env.', GOOD, [
            "Desktop on v1.0.5 as of 2026-10-12 (updated from v1.0.0, independently, since the",
            "last check -- version drift between machines is a recurring silent risk; nothing",
            "tracks it). Two EMode defects remain open, not re-tested against v1.0.5.",
        ]),
    ]
    for name, color, lines in rows:
        fig.text(0.08, y, name, fontsize=11, weight='bold', color=color, family='monospace')
        text_block(fig, 0.22, y, lines, fontsize=9, color=INK_MUTED, linespacing=1.45)
        y -= len(lines) * 0.0225 + 0.028
    pdf.savefig(fig)
    plt.close(fig)


def page3_loss_model(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.94, 'Loss model', fontsize=16, weight='bold', color=INK)
    y = 0.895
    lines = [
        "Three base mechanisms, summed per mode per band: EMode-native roughness scattering",
        "(em.scattering(), Volume Current Method); post-processed interface absorption",
        "(dislocations, C/Si/O impurities, pump-band only); confinement-weighted bulk material",
        "absorption (a lossy region's own k(lambda) x the mode's power fraction inside it, a",
        "post-solve perturbation -- re-solving EMode with a lossy material crashes em.FDM()",
        "outright on every version tried, and the one mechanism that doesn't crash",
        "(shape(loss_dB_per_m=...), deprecated) was found to corrupt SH-mode re-identification",
        "when the loss is large enough to shift the eigenvalue search -- TiO2's case dropped a",
        "nominally-unchanged crossing's overlap_shape 0.051->0.0036 with a different mode label.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    y -= len(lines) * 0.0305 + 0.02

    fig.text(0.08, y, "AlN's own SH-band absorption: measured, rejected, replaced (2026-10-12)",
              fontsize=11, weight='bold', color=WARN)
    y -= 0.028
    lines = [
        "AlN was assumed lossless in every result before this. A real MOCVD sample (AM187-LT6,",
        "team's own ellipsometry_data repo, lowest non-negative k_e among all MOCVD positions)",
        "gave a measured k_e, fit to 3 Lorentzians, wired the same way as the bulk mechanism",
        "above. Implies ~100,000 dB/cm of SH-band loss for the best-matching real device",
        "geometry -- checked against that device's actual measured SH output (~200nW best",
        "case, ~10s of nW typically, ~200mW pump, 10-50% unmeasured coupling) by inverting",
        "shg_physics.loss_limited_length at the real fixed device length. Bounds true SH loss",
        "to ~15-680 dB/cm depending on coupling -- 3-4 orders of magnitude below AM187's number.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    y -= len(lines) * 0.0305 + 0.02

    fig.text(0.08, y, 'Working value: 100 dB/cm, confinement-weighted, SH-band only', fontsize=10.5,
              weight='bold', color=INK)
    y -= 0.026
    lines = [
        "A round number inside the empirically-bounded range, not a measurement of any specific",
        "mechanism -- geometry.sh_absorption_calibrated_dB_per_m, confinement-weighted like the",
        "bulk mechanism above, added on top of (not replacing) native scattering. The standing",
        "assumption for every new run from here on. Full derivation: input_assumptions_report.pdf",
        "section 3b; PLAN.md's 2026-10-12 \"empirical SH-loss bound\" entries.",
    ]
    text_block(fig, 0.08, y, lines, fontsize=9.5, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def render_cross_section(ax, g, title):
    x0, x1, y0, y1 = g.bbox()
    half_w = g.window_width / 2
    x = np.arange(max(-half_w, x0 - 500.0), min(half_w, x1 + 500.0), 5.0)
    y = np.arange(0.0, y1 + 600.0, 5.0)
    regions = g.region_masks(x, y)
    handles = []
    for name, (mask, material) in regions.items():
        if not mask.any():
            continue
        color = REGION_COLOR.get(name, '#898781')
        rgba = np.zeros((*mask.shape, 4))
        rgba[mask] = matplotlib.colors.to_rgba(color)
        ax.imshow(rgba, origin='lower', extent=[x[0], x[-1], y[0], y[-1]], aspect='equal')
        handles.append(mpatches.Patch(color=color, label=f"{name} ({material})"))
    ax.set_xlabel('x [nm]'); ax.set_ylabel('y [nm]')
    ax.set_title(title, fontsize=10)
    ax.legend(handles=handles, loc='upper right', fontsize=7, framealpha=0.9)
    style_ax(ax)


def page4_geometry_families(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.07, 0.95, 'Geometry families', fontsize=16, weight='bold', color=INK)
    fig.text(0.07, 0.925,
              'family name + a params dict; every family implements the same build()/region_masks()/'
              'chi2_map()/bbox() interface', fontsize=9, color=INK_MUTED)

    specs = [
        ('ridge', {'h_core': 350.0, 'w_core': 400.0}, 'Ridge (h=350, w=400 nm)'),
        ('loaded', {'etch_depth': 0.0, 'w_rib': 500.0, 'strip_material': 'TiO2', 't_film': 354.0,
                    'h_s': 70.0, 'w_s': 500.0}, 'Loaded, h_A=full film (etch_depth=0)'),
        ('hybrid', {'h_core': 300.0, 'w_core': 400.0, 'sin_width': 800.0, 'sin_height': 600.0},
         'hybrid, corrected embedded (h=300, w=400)'),
        ('pedestal', {'h_core': 300.0, 'w_core': 400.0, 'sin_width': 800.0, 'sin_height': 600.0},
         'pedestal, legacy stacked (same params)'),
    ]
    positions = [(0.07, 0.60), (0.54, 0.60), (0.07, 0.07), (0.54, 0.07)]
    for (family, params, title), (x, ybot) in zip(specs, positions):
        ax = fig.add_axes((x, ybot, 0.40, 0.30))
        g = geo.make_geometry(family, params)
        render_cross_section(ax, g, title)

    fig.text(0.07, 0.52,
              "ridge: bare AlN core on substrate, no A/B layers. loaded: AlN film capped by a",
              fontsize=8.5, color=INK_MUTED)
    fig.text(0.07, 0.503,
              "narrower loading strip (TiO2 shown; SH-absorbing, ruled out). hybrid: core wrapped",
              fontsize=8.5, color=INK_MUTED)
    fig.text(0.07, 0.486,
              "on the sides AND above by the shell (corrected 2026-10-10). pedestal: the same",
              fontsize=8.5, color=INK_MUTED)
    fig.text(0.07, 0.469,
              "params, but core sits ON TOP of the shell -- what hybrid built before the fix.",
              fontsize=8.5, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def page5_gotchas(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.94, 'Gotchas most likely to bite again', fontsize=16, weight='bold', color=INK)
    y = 0.89
    items = [
        ('A geometry param can auto-stack instead of embed', [
            "em.shape()'s position defaults to (0,'auto'), which STACKS a new shape on top of",
            "whatever's there; an explicit position is CENTER-referenced, not bottom-referenced.",
            "This is exactly how `hybrid` silently built the stacked `pedestal` structure for",
            "months -- it ran, gave plausible numbers, looked fine until someone checked the",
            "actual rendered cross-section. Verify any new embedding geometry two independent",
            "ways (em.get_shape() metadata + an em.confinement() power-fraction check).",
        ]),
        ('EMode version matters, and nothing tracks it', [
            "Check (Get-Item \"...\\EMode.exe\").VersionInfo before debugging an EMode-API-shaped",
            "issue as code, on EITHER machine, every time -- a prior session's note can already",
            "be stale (found 2026-10-12: desktop had moved to v1.0.5 without it being logged).",
        ]),
        ('Binary field exports do not travel with git, or scale through chat tools', [
            "runs/*/exports/*.npz is gitignored (~270MB per 8-geometry sweep). A cloud-drive MCP",
            "tool's per-file download doesn't scale past a handful of files (each lands as base64",
            "text in context). What works: download the whole folder as a zip from the web UI,",
            "copy over the local filesystem directly.",
        ]),
        ('A great NCE can be a simulation-window artifact', [
            "Box modes (quantized by the window's hard walls, not real confinement) can carry a",
            "genuine local field enhancement, so NCE/overlap_shape alone don't catch them --",
            "check shg_physics.lateral_edge_ratio; survey.py/summarize_run.py now filter",
            "automatically, but a pre-2026-10-05 run's crossings weren't checked at all.",
        ]),
        ('Raw mode index is not a stable identifier', [
            "Can shift by 7+ from a modest width or wavelength change. Every tracking step",
            "identifies modes by field-overlap similarity against the previous step, never by",
            "raw index -- new analysis code against the exports should do the same.",
        ]),
    ]
    for title, lines in items:
        fig.text(0.08, y, title, fontsize=10.5, weight='bold', color=INK)
        y -= 0.026
        text_block(fig, 0.08, y, lines, fontsize=9, color=INK_MUTED, linespacing=1.45)
        y -= len(lines) * 0.0225 + 0.028
    pdf.savefig(fig)
    plt.close(fig)


def page6_results_index(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.94, 'Results index', fontsize=16, weight='bold', color=INK)
    y = 0.885
    rows = [
        ('input_assumptions_report.pdf', 'Loss model, material dispersion, figures of merit. Canonical -- every other report should cite it.'),
        ('aln_loss_report.pdf', 'Lossless vs. calibrated-SH-loss comparison, across every reprocessed run.'),
        ('simulation_study_plan.pdf', 'The 10-row geometry x material design matrix, sequencing, standing assumptions.'),
        ('field_guide_report.pdf', 'This document.'),
        ('runs/<name>/summary/summary.md', "Per-run ranking tables, the human-readable version of that run's CSVs."),
        ('runs/<name>/crossings.csv', 'Every phase match: NCE, overlap, losses, L_opt, peak efficiency, per refined/screened row.'),
        ('PLAN.md', 'The dated lab notebook -- every finding above traces back to an entry there. "Open items" is the live backlog.'),
    ]
    for name, desc in rows:
        fig.text(0.08, y, name, fontsize=9.5, weight='bold', color=ACCENT, family='monospace')
        y -= 0.024
        fig.text(0.08, y, desc, fontsize=9, color=INK_MUTED)
        y -= 0.04

    fig.text(0.08, 0.1,
              'Live artifact (interactive, operational instructions included):',
              fontsize=9, color=INK_FAINT)
    fig.text(0.08, 0.08,
              'claude.ai/artifact/AcW4tCTXUH3xXTPhq5zi4a -- updated alongside this PDF, 2026-10-12.',
              fontsize=9, color=INK_MUTED, family='monospace')
    pdf.savefig(fig)
    plt.close(fig)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'runs/field_guide_report.pdf'
    with PdfPages(out) as pdf:
        page1_overview(pdf)
        page2_status(pdf)
        page3_loss_model(pdf)
        page4_geometry_families(pdf)
        page5_gotchas(pdf)
        page6_results_index(pdf)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
