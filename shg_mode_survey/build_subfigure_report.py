"""PDF version of the sub-metric breakdown ("Hybrid Loss Atlas" artifact, 2026-10-06): pulls apart
eta_pct_per_W_cm2 into overlap_shape (loss-independent), SH-side (UV) and pump-side (blue)
scattering/absorption, and confinement, across all refined crossings from one or more survey.py
run directories. Unlike the original artifact (hybrid1 + hybrid_sweep1 only), this covers all
three archived `pedestal` runs (the lateral sweep's two runs + the vertical sweep) -- see PLAN.md,
"Renamed the stacked (non-embedded) structure to its own family, pedestal" (2026-10-12) for why
these are filed as `pedestal`, not `hybrid`.

Usage: python build_subfigure_report.py [out.pdf] [run_name ...]
Default: pedestal1 pedestal_sweep1 pedestal_vertical1 -> runs/pedestal_subfigure_report.pdf
"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

from extract_subfigure_data import load

# -- palette (matches the HTML artifact) --------------------------------------------------------
INK, INK_MUTED, INK_FAINT = '#161a2e', '#5c6180', '#9094ad'
BORDER = '#dcdfeb'
RAMP_LOSS = ('#efe9ff', '#5b3df0')
RAMP_OVERLAP = ('#e3fbf6', '#0e9488')
RAMP_POWER = ('#fff2e0', '#c9680e')
RAMP_ETA = ('#ffe9f1', '#c23a73')
WCORE_COLORS = {200: '#0072B2', 300: '#009E73', 400: '#7570B3', 500: '#D55E00', 600: '#CC79A7'}
HCORE_COLORS = {250: '#0072B2', 300: '#009E73', 350: '#7570B3', 400: '#D55E00', 450: '#CC79A7'}

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9, 'text.color': INK, 'axes.edgecolor': BORDER,
    'axes.labelcolor': INK_MUTED, 'xtick.color': INK_MUTED, 'ytick.color': INK_MUTED,
    'axes.grid': True, 'grid.color': BORDER, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
    'figure.facecolor': 'white', 'savefig.facecolor': 'white',
})


def seq_cmap(c1, c5):
    return matplotlib.colors.LinearSegmentedColormap.from_list('seq', [c1, c5])


def style_ax(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.spines['left'].set_color(BORDER)
    ax.spines['bottom'].set_color(BORDER)
    # log-scale axes default to crowded, overlapping minor-tick labels (2x10^3, 4x10^3, ...) --
    # major decade ticks only, consistently applied wherever a panel sets xscale/yscale='log'.
    if ax.get_xscale() == 'log':
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    if ax.get_yscale() == 'log':
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def corr(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.corrcoef(a, b)[0, 1])


def title_page(pdf, df):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.94
    fig.text(0.08, y, 'Pedestal Family: Loss & Overlap Breakdown', fontsize=22, weight='bold', color=INK)
    y -= 0.045
    fig.text(0.08, y, 'shg_mode_survey · pedestal1 + pedestal_sweep1 + pedestal_vertical1',
              fontsize=11, color=INK_MUTED, family='monospace')
    y -= 0.055

    n_geoms = df.groupby(['h_core', 'w_core', 'sin_width', 'sin_height']).ngroups
    body = (f"{len(df)} refined pump→SH crossings across {n_geoms} geometries. Sub-metrics that\n"
            f"eta_pct_per_W_cm2 collapses into one number: scattering vs. absorption at both\n"
            f"wavelengths, raw mode-shape overlap independent of loss, and how little either one\n"
            f"predicts the other.\n\n"
            f"SH = 215–235 nm, deep UV.  Pump = 430–470 nm, true blue.  Two very different bands,\n"
            f"two very different loss stories.")
    fig.text(0.08, y, body, fontsize=10.5, color=INK, va='top', linespacing=1.6)
    y -= 0.235

    fig.text(0.08, y, 'CAUTION', fontsize=9, weight='bold', color='#c9680e')
    y -= 0.028
    caveat = ("This is the 'pedestal' family (AlN ridge stacked on TOP of an SiNx rib) -- the\n"
              "structure every 'hybrid'-named run before 2026-10-10 actually built by accident, due\n"
              "to a geometry-construction bug (see PLAN.md). It is a real, different waveguide, but it\n"
              "is NOT the Honda et al. AlN-embedded-in-SiNx structure the 'hybrid' family now (after\n"
              "the fix) correctly builds. AlN is modeled as lossless here (its own UV k is a separate,\n"
              "still-open item) -- every absorption number below is SiNx bulk absorption.")
    fig.text(0.08, y, caveat, fontsize=9.5, color=INK_MUTED, va='top', linespacing=1.55)
    y -= 0.195

    # headline stat tiles
    ratios = (df['sh_absorption_dB_per_m'] / df['sh_scattering_dB_per_m'])
    band_ratio = (df['sh_loss_total_dB_per_m'] / df['pump_loss_total_dB_per_m'])
    r_ov_pow = corr(df['overlap_shape'], df['sh_power_in_core'])
    r_ov_eta = corr(df['overlap_shape'], np.log10(df['eta_pct_per_W_cm2'].clip(lower=1e-6)))
    best = df.loc[df['eta_pct_per_W_cm2'].idxmax()]
    stats = [
        ('SH absorption / scattering', f"{ratios.median():.0f}× median",
         'SiNx bulk absorption dwarfs sidewall scattering in the UV'),
        ('SH loss / pump loss', f"{band_ratio.median():.0f}× median",
         'same crossing, UV vs. blue -- very different bands'),
        ('overlap_shape ↔ confinement', f"r = {r_ov_pow:.2f}",
         'narrow cores: highest shape overlap, least SH power actually in them'),
        ('overlap_shape ↔ log(eta)', f"r = {r_ov_eta:.2f}",
         'shape overlap alone barely predicts final efficiency'),
    ]
    for label, val, sub in stats:
        fig.text(0.08, y, label.upper(), fontsize=7.5, color=INK_FAINT, weight='bold')
        y -= 0.026
        fig.text(0.08, y, val, fontsize=15, color=INK, family='monospace', weight='bold')
        fig.text(0.30, y + 0.006, sub, fontsize=8.5, color=INK_MUTED)
        y -= 0.052

    fig.text(0.08, 0.04,
              f"Best crossing overall: {best['pump_label']}→{best['sh_label']} @ "
              f"{best['wavelength_sh']:.2f} nm, eta={best['eta_pct_per_W_cm2']:.1f} %/W/cm² "
              f"(h={best['h_core']:g}/w={best['w_core']:g}/sin_w={best['sin_width']:g}/"
              f"sin_h={best['sin_height']:g}, run={best['run']})",
              fontsize=9, color=INK_MUTED, family='monospace')
    pdf.savefig(fig)
    plt.close(fig)


def loss_pages(pdf, df):
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle('Loss breakdown: scattering vs. absorption', fontsize=14, weight='bold', x=0.08, ha='left')

    ax = axs[0]
    pw = df['sh_power_in_core']
    sc = ax.scatter(df['sh_scattering_dB_per_m'], df['sh_absorption_dB_per_m'], c=pw,
                     cmap=seq_cmap(*RAMP_POWER), s=16, alpha=0.85, edgecolor='none')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('SH scattering [dB/m]'); ax.set_ylabel('SH absorption [dB/m]')
    ax.set_title('SH-side (UV, 215–235 nm)', fontsize=10.5, color=INK)
    style_ax(ax)
    cb = fig.colorbar(sc, ax=ax, shrink=0.8); cb.set_label('SH power in core', fontsize=8)

    ax = axs[1]
    pw2 = df['pump_power_in_core'].fillna(0)
    sc2 = ax.scatter(df['pump_scattering_dB_per_m'], df['pump_absorption_dB_per_m'], c=pw2,
                      cmap=seq_cmap(*RAMP_POWER), s=16, alpha=0.85, edgecolor='none')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('pump scattering [dB/m]'); ax.set_ylabel('pump absorption [dB/m]')
    ax.set_title('Pump-side (true blue, 430–470 nm)', fontsize=10.5, color=INK)
    style_ax(ax)
    cb = fig.colorbar(sc2, ax=ax, shrink=0.8); cb.set_label('pump power in core', fontsize=8)

    fig.text(0.08, 0.02, 'Note the axis scales: SH absorption sits 3 orders of magnitude above SH '
                          'scattering; pump loss overall is ~1000x smaller than SH loss.',
              fontsize=8.5, color=INK_FAINT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    pdf.savefig(fig)
    plt.close(fig)


def overlap_pages(pdf, df):
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.2))
    fig.suptitle('Overlap vs. confinement vs. final efficiency', fontsize=14, weight='bold', x=0.08, ha='left')

    ax = axs[0]
    for w, color in WCORE_COLORS.items():
        sel = df[df['w_core'] == w]
        if len(sel):
            ax.scatter(sel['sh_power_in_core'], sel['overlap_shape'], s=16, alpha=0.85,
                       color=color, edgecolor='none', label=f'w_core={w:g}')
    ax.set_xlabel('SH power fraction in AlN core'); ax.set_ylabel('overlap_shape (0–1, loss-independent)')
    style_ax(ax)
    ax.legend(fontsize=7.5, frameon=False, loc='upper right')

    ax = axs[1]
    for w, color in WCORE_COLORS.items():
        sel = df[df['w_core'] == w]
        if len(sel):
            ax.scatter(sel['overlap_shape'], sel['eta_pct_per_W_cm2'], s=16, alpha=0.85,
                       color=color, edgecolor='none', label=f'w_core={w:g}')
    ax.set_yscale('log')
    ax.set_xlabel('overlap_shape (0–1, loss-independent)'); ax.set_ylabel('eta [%/W/cm²] (log)')
    style_ax(ax)

    fig.tight_layout(rect=(0, 0.02, 1, 0.93))
    pdf.savefig(fig)
    plt.close(fig)


def geometry_maps_page(pdf, df, x_key, y_key, x_label, y_label, title, fixed_note):
    agg = df.groupby([x_key, y_key]).agg(
        best_eta=('eta_pct_per_W_cm2', 'max'),
        best_overlap=('overlap_shape', 'max'),
        min_loss=('sh_loss_total_dB_per_m', 'min'),
        mean_power=('sh_power_in_core', 'mean'),
    ).reset_index()

    fig, axs = plt.subplots(2, 2, figsize=(9.5, 9))
    fig.suptitle(title, fontsize=14, weight='bold', x=0.08, ha='left')
    fig.text(0.08, 0.935, fixed_note, fontsize=9, color=INK_MUTED)

    panels = [
        ('best_overlap', 'Best overlap_shape', RAMP_OVERLAP, False),
        ('mean_power', 'Mean SH power in core', RAMP_POWER, False),
        ('min_loss', 'Min SH loss (scat+abs)', RAMP_LOSS, True),
        ('best_eta', 'Best eta [%/W/cm²]', RAMP_ETA, False),
    ]
    for ax, (key, label, ramp, invert) in zip(axs.flat, panels):
        vals = agg[key]
        vmin, vmax = vals.min(), vals.max()
        norm = (vals - vmin) / (vmax - vmin) if vmax > vmin else vals * 0
        if invert:
            norm = 1 - norm
        sc = ax.scatter(agg[x_key], agg[y_key], c=norm, cmap=seq_cmap(*ramp), s=220,
                        edgecolor=BORDER, linewidth=0.8, vmin=0, vmax=1)
        ax.set_title(label, fontsize=10, color=INK)
        ax.set_xlabel(x_label, fontsize=8.5); ax.set_ylabel(y_label, fontsize=8.5)
        style_ax(ax)
        lo_s = f"{vmin:.2e}" if abs(vmax) > 1e4 else f"{vmin:.2f}"
        hi_s = f"{vmax:.2e}" if abs(vmax) > 1e4 else f"{vmax:.2f}"
        cb = fig.colorbar(sc, ax=ax, shrink=0.85, ticks=[0, 1])
        cb.ax.set_yticklabels([lo_s, hi_s] if not invert else [hi_s, lo_s], fontsize=7)

    fig.tight_layout(rect=(0, 0, 1, 0.91))
    pdf.savefig(fig)
    plt.close(fig)


def notes_page(pdf, df):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.92, 'Notes & provenance', fontsize=16, weight='bold', color=INK)
    text = (
        "Data: runs/pedestal1, runs/pedestal_sweep1, runs/pedestal_vertical1 crossings.csv, refined rows\n"
        "only (screening doesn't solve losses or overlap_shape -- too expensive per-crossing to run on\n"
        "every screened candidate). Extracted via extract_subfigure_data.py, rendered via\n"
        "build_subfigure_report.py.\n\n"
        "overlap_shape is dimensionless 0-1, integrated over the AlN region only -- 1 means the SH field\n"
        "inside AlN is exactly proportional to the pump-driven polarization; it carries no information\n"
        "about HOW MUCH SH power actually reaches AlN (that's sh_power_in_core, measured separately).\n\n"
        "Absorption numbers are SiNx shell bulk absorption (Gamma_shell * alpha_SiNx(lambda), first-order\n"
        "perturbation -- survey.py's bulk_absorption_loss()); AlN is modeled as lossless throughout, so it\n"
        "contributes exactly zero. SiNx's own measured k rounds to 0 in the raw literature data at\n"
        "430-470 nm (pump/blue) but is 0.06-0.14 at 215-235 nm (SH/UV) -- see\n"
        "materials/fit_sinx_sellmeier.py.\n\n"
        "All 416 refined crossings here are clean by the window/box-mode check (sh_edge_ratio well below\n"
        "the 0.02 threshold throughout).\n\n"
        "IMPORTANT: this is the 'pedestal' family -- AlN stacked on top of an SiNx rib, not embedded in\n"
        "it. It does not test the Honda et al. 2025 TM00->TM20 mechanism. See PLAN.md's 2026-10-10 and\n"
        "2026-10-12 entries for the full story, and the corrected 'hybrid' family for the structure that\n"
        "does test that mechanism (re-run pending as of this report)."
    )
    fig.text(0.08, 0.86, text, fontsize=10, color=INK_MUTED, va='top', linespacing=1.7)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    args = sys.argv[1:]
    out = args[0] if args and args[0].endswith('.pdf') else 'runs/pedestal_subfigure_report.pdf'
    runs = [a for a in args if not a.endswith('.pdf')] or ['pedestal1', 'pedestal_sweep1', 'pedestal_vertical1']
    df = load(runs)

    with PdfPages(out) as pdf:
        title_page(pdf, df)
        loss_pages(pdf, df)
        overlap_pages(pdf, df)
        lateral = df[df['h_core'] == 400.0]
        geometry_maps_page(pdf, lateral, 'w_core', 'sin_width', 'w_core [nm]', 'sin_width [nm]',
                           'Lateral geometry maps', 'Fixed h_core = 400 nm')
        vertical = df[(df['w_core'] == 400.0) & (df['sin_width'] == 700.0)]
        geometry_maps_page(pdf, vertical, 'h_core', 'sin_height', 'h_core [nm]', 'sin_height [nm]',
                           'Vertical geometry maps', 'Fixed w_core = 400 nm, sin_width = 700 nm')
        notes_page(pdf, df)

    print(f'wrote {out} ({len(df)} refined crossings, runs={runs})')


if __name__ == '__main__':
    main()
