"""Simulation Study Plan: documents the geometry x material design matrix agreed with the user
(2026-10-12, building on the generalized-geometry discussion from the same day) before launching
the corrected-geometry 'hybrid' re-run and any broader campaign. Includes real cross-section
diagrams (pulled straight from geometry.py's own mask functions, via plot_geometry.py -- the same
families already built and verified) for the families that exist, and a schematic (hand-built,
nothing to render yet) for the one that doesn't: embedded-Cerenkov.

Usage: python build_study_plan_report.py [out.pdf]
"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
    'figure.facecolor': 'white', 'savefig.facecolor': 'white',
})

MATRIX = [
    dict(n=1, topology='Ridge', h_a='n/a (no A layer)', core='AlN', shell='—', substrate='Al2O3',
         purpose='baseline', status='done (`row1_ridge`); loss comparison done', ok=True),
    dict(n='1.2', topology='Ridge', h_a='0 → film thickness', core='AlN', shell='— (no strip, B=0)',
         substrate='Al2O3', purpose='bare partial-etch rib, no strip -- between row 1 and row 4',
         status='done; best NCE 2.25, peak_eff up to 0.0038 %/W (~row-1-like, no strip = no bulk loss)', ok=True),
    dict(n=2, topology='Ridge', h_a='n/a', core='ScAlN', shell='—', substrate='Al2O3',
         purpose='Sc-enhanced d33 alone, no loading', status='ready — d33(Sc) set, AT RISK', ok=True),
    dict(n=3, topology='Rib-loaded', h_a='0 → film thickness', core='AlN', shell='TiO2', substrate='Al2O3',
         purpose='baseline', status='done — found bad (SH-absorbing)', ok=True),
    dict(n=4, topology='Rib-loaded', h_a='0 → film thickness', core='AlN', shell='SiN', substrate='Al2O3',
         purpose='SiN strip instead of TiO2', status='done; best NCE 9.49 %/W/cm², Cerenkov-flagged (structural)', ok=True),
    dict(n='5.1', topology='Rib-loaded', h_a='0 → film thickness', core='AlN', shell='ScAlN (9% Sc)',
         substrate='Al2O3', purpose='LOW: index boost to pull the mode up',
         status='done; best NCE 1.57 %/W/cm² (below row 4)', ok=True),
    dict(n='5.2', topology='Rib-loaded', h_a='0 → film thickness', core='AlN', shell='ScAlN (41% Sc)',
         substrate='Al2O3', purpose='HIGH: chase the d33 boost',
         status='done; best NCE 2313 %/W/cm² (~244x row 4), d33 EXTRAPOLATED', ok=True),
    dict(n='5.3', topology='Rib-loaded', h_a='0 → film thickness', core='AlN', shell='ScAlN (23% Sc)',
         substrate='Al2O3', purpose='MIDDLE: fill the low/high gap',
         status='done; best NCE 11.2 %/W/cm² (above row 4, nowhere near 5.2 — grid-specific overlap, not monotonic with Sc%)', ok=True),
    dict(n=6, topology='Embedded (guided)', h_a='0 → TBD*', core='AlN', shell='SiN', substrate='Al2O3',
         purpose='corrected `hybrid` — Honda et al. mechanism', status='done (`row6_hybrid_lateral`/`_vertical`); TM20 not found, close analogues', ok=True),
    dict(n=7, topology='Embedded (guided)', h_a='0 → TBD*', core='AlN', shell='ScAlN', substrate='Al2O3',
         purpose='both-active variant', status='ready — d33(Sc) set, AT RISK', ok=True),
    dict(n=8, topology='Embedded (Cerenkov)', h_a='0 → TBD*', core='ScAlN', shell='AlN (blanket)', substrate='Al2O3 or AlN',
         purpose="buried high-index channel radiating into thick AlN", status='d33 set; needs embedded-Cerenkov geometry (not built)', ok=False),
    dict(n=9, topology='Embedded (Cerenkov)', h_a='0 → TBD*', core='GaAlN', shell='AlN (blanket)', substrate='Al2O3 or AlN',
         purpose='same, GaAlN channel', status='need full GaAlN n/k/d33', ok=False),
    dict(n=10, topology='any (cross-cutting)', h_a='—', core='—', shell='—', substrate='AlN instead of Al2O3',
         purpose='substrate swap', status='eqns exist, anisotropic treatment TBD', ok=False),
]


def style_ax(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.spines['left'].set_color(BORDER)
    ax.spines['bottom'].set_color(BORDER)


def text_block(fig, x, y, lines, fontsize=10, color=INK, linespacing=1.6, weight='normal'):
    fig.text(x, y, '\n'.join(lines), fontsize=fontsize, color=color, va='top',
              linespacing=linespacing, weight=weight)


def page1_title(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.90
    fig.text(0.08, y, 'Simulation Study Plan', fontsize=24, weight='bold', color=INK)
    y -= 0.045
    fig.text(0.08, y, 'shg_mode_survey · geometry × material design matrix, agreed 2026-10-12',
              fontsize=11, color=INK_MUTED)
    y -= 0.07
    text_block(fig, 0.08, y, [
        "This documents the campaign -- originally ten geometry/material combinations, now 13 after",
        "splitting row 5 into 3 Sc-composition levels and adding row 1.2 (bare rib, 2026-10-14)",
        "(MATRIX, next page), grouped into four underlying cross-section topologies (one page each,",
        "with a real diagram where the family already exists, a schematic where it doesn't yet).",
        "",
        "Built from the generalized-geometry sketches shared 2026-10-12: a 3-layer stack (A = base",
        "film/rib, C = core ridge, B = loading/shell region), where whether B just caps C's top or",
        "wraps around its sides, and how large B is, span both the guided-mode families already in",
        "this repo (ridge, loaded, the corrected hybrid) and the not-yet-built Cerenkov case in one",
        "consistent vocabulary -- not four unrelated structures.",
    ], fontsize=10.5)
    y -= 0.33

    fig.text(0.08, y, 'READING THE MATRIX', fontsize=9, weight='bold', color=INK_FAINT)
    y -= 0.03
    text_block(fig, 0.08, y, [
        "status: ✓ ready to run now, with existing materials data.",
        "        ○ blocked on a materials gap (d33(Sc), GaAlN n/k/d33, or an anisotropic-substrate",
        "        decision) -- see the Input Assumptions report for what's known and what isn't.",
        "h_A: the base-layer thickness, free 0 (pure ridge/no embedding base) up to a full film",
        "     (rib/loaded) -- only wired up in the `loaded` family today; adding it to the embedded",
        "     topologies (rows 6-9) is new geometry work, not yet done (marked TBD*).",
    ], fontsize=9.5, color=INK_MUTED, linespacing=1.5)
    y -= 0.175

    fig.text(0.08, y, 'STANDING ASSUMPTION FOR EVERY NEW RUN FROM HERE ON', fontsize=9, weight='bold',
              color=WARN)
    y -= 0.03
    text_block(fig, 0.08, y, [
        "AlN's own measured SH-band absorption (AM187-LT6 k_e) was explored and REJECTED (it implied",
        "~100,000 dB/cm, checked against real device output and found 3-4 orders of magnitude too",
        "high). Every row below should instead launch with geom.params['sh_absorption_calibrated'] =",
        "True -- a flat, empirically-calibrated 100 dB/cm SH-band addition, confinement-weighted,",
        "layered on top of native scattering (unaffected). See Input Assumptions report section 3b",
        "and PLAN.md's 2026-10-12 entries for the full derivation.",
    ], fontsize=9.5, color=INK_MUTED, linespacing=1.5)

    fig.text(0.08, 0.06,
              "Not a commitment to run all ten at once -- user direction, 2026-10-12: check in before each batch.",
              fontsize=9, color=WARN, weight='bold')
    pdf.savefig(fig)
    plt.close(fig)


def page2_matrix(pdf):
    """Paginates once a row would overflow the bottom margin (Y_FLOOR) -- added 2026-10-14 when
    splitting row 5 into 3 composition levels and adding row 1.2 pushed the matrix from 10 to 13
    rows; cramming all 13 onto one page by shortening status text further would have started
    losing real information instead of just fixing layout."""
    import textwrap
    Y_FLOOR = 0.06
    cols = [('#', 0.015, 3), ('topology', 0.06, 14), ('h_A', 0.20, 13), ('core (C)', 0.345, 9),
            ('shell/outer (B)', 0.435, 13), ('substrate', 0.575, 11), ('purpose', 0.705, 24),
            ('status', 0.895, 13)]

    def new_page(page_n):
        fig = plt.figure(figsize=(11, 8.5))
        fig.text(0.06, 0.94, 'Design matrix' + (f' (cont. {page_n})' if page_n > 1 else ''),
                  fontsize=18, weight='bold', color=INK)
        if page_n == 1:
            fig.text(0.06, 0.905, f'{len(MATRIX)} rows, grouped by topology — see the following '
                      'pages for diagrams of each', fontsize=10, color=INK_MUTED)
        y0 = 0.86 if page_n == 1 else 0.90
        for label, x, _ in cols:
            fig.text(x, y0, label.upper(), fontsize=8, weight='bold', color=INK_FAINT)
        fig.add_artist(plt.Line2D([0.02, 0.99], [y0 - 0.012, y0 - 0.012], color=BORDER, lw=1,
                                  transform=fig.transFigure))
        return fig, y0 - 0.035

    page_n = 1
    fig, y = new_page(page_n)
    for i, row in enumerate(MATRIX):
        vals = [row['topology'], row['h_a'], row['core'], row['shell'], row['substrate'],
                row['purpose'], row['status']]
        max_lines = max(textwrap.fill(val, width=w).count('\n') + 1 for (_, _, w), val in
                        zip(cols[1:], vals))
        row_h = 0.022 + max_lines * 0.022
        if y - row_h < Y_FLOOR:
            pdf.savefig(fig)
            plt.close(fig)
            page_n += 1
            fig, y = new_page(page_n)

        mark = '✓' if row['ok'] else '○'
        mark_color = GOOD if row['ok'] else WARN
        fig.text(cols[0][1], y, f"{row['n']}", fontsize=8.5, color=mark_color, weight='bold', va='top')
        fig.text(cols[0][1] + 0.018, y, mark, fontsize=9, color=mark_color, va='top')
        for (label, x, w), val in zip(cols[1:], vals):
            wrapped = textwrap.fill(val, width=w)
            fig.text(x, y, wrapped, fontsize=8, color=INK, linespacing=1.4, va='top')
        y -= row_h
        if i < len(MATRIX) - 1:
            fig.add_artist(plt.Line2D([0.02, 0.99], [y + 0.01, y + 0.01],
                                      color=BORDER, lw=0.5, alpha=0.6, transform=fig.transFigure))
    pdf.savefig(fig)
    plt.close(fig)


def render_cross_section(ax, geom, title):
    import numpy as np
    x0, x1, y0, y1 = geom.bbox()
    half_w = geom.window_width / 2
    x = np.arange(max(-half_w, x0 - 500.0), min(half_w, x1 + 500.0), 5.0)
    y = np.arange(0.0, y1 + 600.0, 5.0)
    regions = geom.region_masks(x, y)
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
    ax.legend(handles=handles, loc='upper right', fontsize=7.5, framealpha=0.9)
    style_ax(ax)


def topology_page(pdf, title, diagram_fn, rows, notes, is_schematic=False):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.07, 0.94, title, fontsize=16, weight='bold', color=INK)
    tag = 'SCHEMATIC — not yet built' if is_schematic else 'real cross-section, from geometry.py'
    fig.text(0.07, 0.91, tag, fontsize=9, color=WARN if is_schematic else GOOD, weight='bold')

    ax = fig.add_axes((0.08, 0.38, 0.52, 0.48))
    diagram_fn(ax)

    import textwrap
    fig.text(0.65, 0.84, 'MATRIX ROWS', fontsize=8.5, weight='bold', color=INK_FAINT)
    y = 0.81
    for r in rows:
        mark = '✓' if r['ok'] else '○'
        mark_color = GOOD if r['ok'] else WARN
        fig.text(0.65, y, f"{mark} #{r['n']}", fontsize=9, color=mark_color, weight='bold', va='top')
        wrapped = textwrap.fill(f"{r['core']} / {r['shell']} — {r['purpose']}", width=32)
        fig.text(0.70, y, wrapped, fontsize=8, color=INK_MUTED, linespacing=1.4, va='top')
        y -= 0.028 * (wrapped.count('\n') + 1) + 0.012

    text_block(fig, 0.08, 0.28, notes, fontsize=9.5, color=INK_MUTED, linespacing=1.55)
    pdf.savefig(fig)
    plt.close(fig)


def page3_ridge(pdf):
    def diagram(ax):
        g = geo.make_geometry('ridge', {'h_core': 350.0, 'w_core': 400.0})
        render_cross_section(ax, g, 'Ridge (h=350, w=400 nm)')
    topology_page(pdf, 'Topology 1: Ridge', diagram, [r for r in MATRIX if r['topology'] == 'Ridge'], [
        "Bare AlN (or ScAlN) core directly on substrate -- no A layer, no B/shell at all. Still the",
        "best-surviving structure under real (calibrated) SH loss (aln_loss_report.pdf): median",
        "calibrated peak efficiency ~41,000x above `loaded`'s. Row 2 asks whether Sc-doping the core",
        "alone beats even this -- ready, 32%-Sc working d33 (section 6b, AT RISK). Row 1.2 asks a",
        "different question: a PARTIALLY etched bare rib (no strip) -- the B=0 edge case of the",
        "Rib-loaded topology (row 4), grouped here since it's still bare AlN. Needs a `geometry.",
        "Loaded` no-strip code path (not yet done) -- user-approved 2026-10-14, building now.",
        "SWEPT RANGE (row 1, done): h_core 300-400nm x w_core 300-800nm -- best h=350/w=500, NCE",
        "14.9 %/W/cm^2 (num_sh_modes 30->45 fix confirmed this unchanged from the v1 data). Row 1.2:",
        "t_film range TBD. Row 2: not yet run, row 1's range proposed.",
    ])


def page4_rib_loaded(pdf):
    def diagram(ax):
        g = geo.make_geometry('loaded', {'etch_depth': 0.0, 'w_rib': 500.0, 'strip_material': 'TiO2',
                                          't_film': 354.0, 'h_s': 70.0, 'w_s': 500.0})
        render_cross_section(ax, g, 'Rib-loaded, h_A=full film (etch_depth=0)')
    topology_page(pdf, 'Topology 2: Rib-loaded (cap-only)', diagram,
                 [r for r in MATRIX if r['topology'] == 'Rib-loaded'], [
        "A (AlN film) with a loading strip B capping only its top -- the `loaded` family, always run",
        "at etch_depth=0 (unetched film) so far (the B=0/full-etch extreme is row 1.2 instead). Row 3",
        "(TiO2) found bad -- SH-absorbing, ~40,000x below ridge's. Row 4 (SiN) -- done, NCE 9.49, but",
        "linearly inert (no chi(2)). Row 5 (ScAlN, nonlinear-active) split into 3 compositions",
        "(2026-10-14): 5.1 (9%, done, NCE 1.57, below row 4), 5.2 (41%, done, NCE 2313 ~244x row 4 --",
        "real d33 boost, verified via edge-ratio + effective-area checks, not an artifact; d33",
        "EXTRAPOLATED), 5.3 (23%, next, d33 INTERPOLATED -- lower risk). ALL refined crossings in rows",
        "4/5.1/5.2 are Cerenkov-flagged -- structural to etch_depth=0 (an extended same-material AlN",
        "slab always exists), not material-specific; unquantified (no FDFD rate solve run yet).",
        "SWEPT RANGE: t_film {354,436,518,600}nm x h_s {70,150}nm x w_s {500,1000}nm, etch_depth=0 --",
        "identical across rows 3/4/5.1/5.2/5.3 so only the strip material/composition varies.",
    ])


def page5_embedded_guided(pdf):
    def diagram(ax):
        g = geo.make_geometry('hybrid', {'h_core': 300.0, 'w_core': 400.0, 'sin_width': 800.0, 'sin_height': 600.0})
        render_cross_section(ax, g, 'Embedded, guided (h=300, w=400, sin_w=800, sin_h=600)')
    topology_page(pdf, 'Topology 3: Embedded (guided)', diagram,
                 [r for r in MATRIX if r['topology'] == 'Embedded (guided)'], [
        "Core C wrapped on the sides (and above) by shell B (w_C <= w_B) -- the corrected `hybrid`",
        "family, fixed 2026-10-10 after the earlier 'pedestal' geometry bug (core was stacked on top",
        "of the shell, not embedded in it -- see PLAN.md). Tests the Honda et al. 2025 TM00->TM20",
        "mechanism; the re-run (row 6) is the next EMode campaign queued, launching with the",
        "standing sh_absorption_calibrated=True assumption from the start (already wired into both",
        "configs below). Row 7 (ScAlN shell) is ready too, using the 32%-Sc working d33 (section 6b",
        "of Input Assumptions, AT RISK).",
        "SWEPT RANGE: lateral (`hybrid_sweep`) w_core 200-600 x sin_width 700-1500nm, fixed",
        "h_core=400/sin_height=700, 24 pts; vertical (`hybrid_vertical`) h_core 250-450 x sin_height",
        "450-1100nm at the lateral sweep's best point, 23 pts (450 added to probe the pedestal",
        "data's \"smaller wins\" trend to the 200nm-margin boundary).",
    ])


def page6_embedded_cerenkov(pdf):
    def diagram(ax):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10)
        ax.axis('off')
        # substrate
        ax.add_patch(mpatches.Rectangle((0.5, 0.3), 9, 1.3, facecolor='#d9dce6', edgecolor=BORDER))
        ax.text(5, 0.95, 'Substrate', ha='center', va='center', fontsize=9, color=INK_MUTED)
        # A layer
        ax.add_patch(mpatches.Rectangle((0.5, 1.6), 9, 0.9, facecolor=REGION_COLOR['Substrate'],
                                        alpha=0.35, edgecolor=BORDER))
        ax.text(5, 2.05, 'A (AlN, thin)', ha='center', va='center', fontsize=8.5, color=INK_MUTED)
        # B blanket
        ax.add_patch(mpatches.Rectangle((0.5, 2.5), 9, 6.5, facecolor='#f0ad4e', alpha=0.55, edgecolor=BORDER))
        ax.text(5, 8.3, 'B = AlN (blanket, h_B >> 1µm — room for the\nradiative SH mode to leave without a boundary artifact)',
                ha='center', va='center', fontsize=8, color='#8a5a12')
        # C channel
        ax.add_patch(mpatches.Rectangle((4.1, 2.5), 1.8, 1.0, facecolor=REGION_COLOR['core'], edgecolor=INK))
        ax.text(5, 3.0, 'C', ha='center', va='center', fontsize=10, weight='bold', color='white')
        ax.annotate('C = ScAlN or GaAlN\n(buried channel, guides the pump)', xy=(5, 3.0),
                   xytext=(7.3, 4.6), fontsize=8, color=INK, ha='left',
                   arrowprops=dict(arrowstyle='-', color=INK_FAINT, lw=0.8))
        ax.annotate('pump guided here;\nSH radiates UP into B', xy=(5, 3.5),
                   xytext=(0.7, 5.3), fontsize=8, color=INK, ha='left',
                   arrowprops=dict(arrowstyle='-', color=INK_FAINT, lw=0.8))
    topology_page(pdf, 'Topology 4: Embedded (Cerenkov)', diagram,
                 [r for r in MATRIX if r['topology'] == 'Embedded (Cerenkov)'], [
        "Same wrap-around embedding as Topology 3, but the material roles flip and B grows large:",
        "C (small, buried) carries the enhanced index/nonlinearity (ScAlN or GaAlN) and guides the",
        "pump; B becomes a blanket AlN cladding thick enough (>>1 um) to host a genuinely radiative",
        "SH continuum rather than a tightly confined guided mode. No new plumbing needed for the",
        "Cerenkov physics itself -- `cerenkov_fdfd.py`'s driven 2D solve already takes eps_fn/d_fn/",
        "bbox generically from any geometry class, the same interface every existing family",
        "implements. What's missing is the geometry class itself (not yet written) and, for row 9",
        "specifically, a live transparency check -- GaAlN's favorable (higher-d33) direction is",
        "Ga-rich, but GaN's bandgap sits below the SH photon energy, so the useful window may be",
        "narrow or may not exist; not yet checked quantitatively (Input Assumptions report, section 5).",
    ], is_schematic=True)


def page7_sequencing(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.90
    fig.text(0.08, y, 'Sequencing', fontsize=18, weight='bold', color=INK)
    y -= 0.06
    text_block(fig, 0.08, y, [
        "Proposed order, each step its own check-in (user direction, 2026-10-12: not a green light",
        "to run all rows unsupervised) -- every step launches with",
        "geom.params['sh_absorption_calibrated']=True from the start (page 1), not reprocessed later --",
        "",
        "1. DONE (2026-10-12/13): Row 6, `row6_hybrid_lateral`/`row6_hybrid_vertical` -- 47",
        "   geometries, 376 refined crossings, zero errors. TM00->TM20 itself not found; closest",
        "   analogues are TM0x->TM2(5-9). See runs/hybrid_subfigure_report.pdf.",
        "2. DONE (2026-10-13): Row 1 refresh, `row1_ridge` -- num_sh_modes 30->45 fixed a coverage",
        "   gap found in `row1_ridge_v1`'s log; best crossing unchanged (h=350/w=500, NCE 14.9).",
        "3. DONE (2026-10-13/14): Row 4 (`row4_loaded_sin`, SiN) -- best NCE 9.49. Row 5 split into 3",
        "   Sc-composition levels (2026-10-14): 5.1 (9%, low) and 5.2 (41%, high) both done -- best",
        "   NCE 1.57 and 2313 respectively, the latter a confirmed real d33 boost (~244x row 4,",
        "   verified against edge-ratio and effective-area artifacts). ALL refined crossings in rows",
        "   4/5.1/5.2 Cerenkov-flagged (structural, etch_depth=0 -- see Topology 2 page).",
        "4. NEXT (2026-10-14, user-approved): Row 1.2 (bare partially-etched rib, no strip -- needs a",
        "   geometry.Loaded code change, building now) and Row 5.3 (23% Sc middle composition,",
        "   interpolated d33=44.2/d31=2.8 pm/V, lower risk than 5.2's extrapolated value).",
        "5. THEN (2026-10-14, user-approved, geometries TBD -- discuss before launching): Row 8",
        "   (embedded-Cerenkov, ScAlN channel) and Row 9 (embedded-Cerenkov, GaAlN channel). Row 8's",
        "   d33 is set (same AT RISK value); both still need the embedded-Cerenkov geometry class",
        "   (topology 4) built -- doesn't exist yet. Row 9 also needs GaAlN n/k sourced first (Input",
        "   Assumptions report, section 5).",
        "6. Row 2/7: ridge and embedded-guided ScAlN variants -- d33 question resolved (section 6b),",
        "   configs not yet written (mirror row 1/6's grids with ScAlN swapped in). Not yet sequenced",
        "   relative to rows 8/9 -- revisit after those.",
        "7. Row 10: substrate swap, cross-cutting -- can run alongside any of the above once the",
        "   anisotropic-vs-isotropic AlN-substrate treatment is settled (user direction, 2026-10-12:",
        "   anisotropic).",
    ], fontsize=9.5, linespacing=1.5)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'runs/simulation_study_plan.pdf'
    with PdfPages(out) as pdf:
        page1_title(pdf)
        page2_matrix(pdf)
        page3_ridge(pdf)
        page4_rib_loaded(pdf)
        page5_embedded_guided(pdf)
        page6_embedded_cerenkov(pdf)
        page7_sequencing(pdf)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
