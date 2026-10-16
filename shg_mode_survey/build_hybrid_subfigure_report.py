"""PDF sub-metric breakdown for the corrected 'hybrid' family (AlN embedded IN an SiNx shell --
the Honda et al. 2025 structure, post the 2026-10-10 geometry-construction fix; see PLAN.md). Twin
of build_subfigure_report.py (which covers the unrelated 'pedestal' family -- AlN stacked ON TOP
of SiNx, what every pre-fix 'hybrid'-named run actually built by accident), rebuilt rather than
parameterized because this family's story is different in two ways the pedestal report doesn't
need to carry: (1) this is the first hybrid-family run with the 2026-10-12 SH-loss calibration
wired in (sh_absorption_calibrated=True, geometry.SH_ABSORPTION_CALIBRATED_DB_PER_CM added into
sh_absorption_dB_per_m, separately recoverable via sh_calibrated_dB_per_m -- see
extract_subfigure_data.py), and (2) this campaign was explicitly run to test two physics questions
(does TM00->TM20 or a close analogue appear; does "smaller sin_height keeps winning" from the
pedestal archival data continue to the new sin_height=450 boundary point) that deserve their own
pages rather than being left implicit in the geometry maps.

Usage: python build_hybrid_subfigure_report.py [out.pdf] [run_name ...]
Default: row6_hybrid_lateral row6_hybrid_vertical -> runs/hybrid_subfigure_report.pdf
"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from extract_subfigure_data import load

# -- palette (matches build_subfigure_report.py / the HTML artifact) ----------------------------
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
    fig.text(0.08, y, 'Hybrid Family: Loss & Overlap Breakdown', fontsize=22, weight='bold', color=INK)
    y -= 0.045
    fig.text(0.08, y, 'shg_mode_survey · row6_hybrid_lateral (lateral) + row6_hybrid_vertical (vertical)',
              fontsize=11, color=INK_MUTED, family='monospace')
    y -= 0.055

    n_geoms = df.groupby(['h_core', 'w_core', 'sin_width', 'sin_height']).ngroups
    body = (f"{len(df)} refined pump→SH crossings across {n_geoms} geometries -- AlN core embedded\n"
            f"IN an SiNx shell (not stacked on top; see the 'pedestal' report for that earlier,\n"
            f"accidental structure). First hybrid-family campaign run with the 2026-10-12 SH-loss\n"
            f"calibration wired in from launch (100 dB/cm flat, confinement-weighted, SH-band only).\n\n"
            f"SH = 215-235 nm, deep UV.  Pump = 430-470 nm, true blue.")
    fig.text(0.08, y, body, fontsize=10.5, color=INK, va='top', linespacing=1.6)
    y -= 0.205

    fig.text(0.08, y, 'WHAT THIS CAMPAIGN WAS BUILT TO TEST', fontsize=9, weight='bold', color='#c9680e')
    y -= 0.028
    caveat = (
        "1. Does the Honda et al. TM00->TM20 mechanism (or a close analogue) actually appear now that\n"
        "   AlN is correctly embedded? NOT exactly -- no crossing hits TM20 itself. Closest analogues\n"
        "   are higher-vertical-order TM2n (n=5-9) crossings; see the dedicated page below.\n"
        "2. Does the pedestal data's 'smaller sin_height keeps winning' trend continue to the new\n"
        "   sin_height=450 boundary point? NO -- it reverses. Best NCE peaks at sin_height=500, not\n"
        "   at the smallest tested value; see the dedicated page below.\n"
        "Both are genuine, useful answers -- a campaign that confirmed the naive hypothesis either way\n"
        "would have told us less than finding the real optimum sits in the interior of the range."
    )
    fig.text(0.08, y, caveat, fontsize=9.5, color=INK_MUTED, va='top', linespacing=1.55)
    y -= 0.215

    cal_frac = df['sh_calibrated_dB_per_m'] / df['sh_absorption_dB_per_m']
    ratios = (df['sh_absorption_dB_per_m'] / df['sh_scattering_dB_per_m'])
    band_ratio = (df['sh_loss_total_dB_per_m'] / df['pump_loss_total_dB_per_m'])
    r_ov_eta = corr(df['overlap_shape'], np.log10(df['eta_pct_per_W_cm2'].clip(lower=1e-6)))
    best = df.loc[df['eta_pct_per_W_cm2'].idxmax()]
    stats = [
        ('calibrated SH loss / total SH absorption', f"{cal_frac.median()*100:.3f}% median",
         'native SiNx shell bulk UV absorption swamps the calibrated device-anchored term'),
        ('SH absorption / scattering', f"{ratios.median():.0f}× median",
         'same dominance pattern as the pedestal family, even stronger here'),
        ('SH loss / pump loss', f"{band_ratio.median():.0f}× median",
         'same crossing, UV vs. blue -- very different bands'),
        ('overlap_shape ↔ log(eta)', f"r = {r_ov_eta:.2f}",
         'shape overlap alone barely predicts final efficiency'),
    ]
    for label, val, sub in stats:
        fig.text(0.08, y, label.upper(), fontsize=7.5, color=INK_FAINT, weight='bold')
        y -= 0.026
        fig.text(0.08, y, val, fontsize=15, color=INK, family='monospace', weight='bold')
        fig.text(0.38, y + 0.006, sub, fontsize=8.5, color=INK_MUTED)
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
    ax.set_xlabel('SH scattering [dB/m]'); ax.set_ylabel('SH absorption [dB/m] (incl. calibrated term)')
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

    fig.text(0.08, 0.02, 'SH absorption on the left already includes the calibrated SH-loss term '
                          '(sh_calibrated_dB_per_m) summed in -- see the next page for how small a '
                          'share of the total that term actually is.',
              fontsize=8.5, color=INK_FAINT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    pdf.savefig(fig)
    plt.close(fig)


def calibrated_fraction_page(pdf, df):
    """Hybrid-specific: how much of sh_absorption_dB_per_m is the 2026-10-12 device-calibrated
    term (100 dB/cm, confinement-weighted) vs. native SiNx shell bulk UV absorption. Not a question
    the pedestal report could ask (that family predates the calibration entirely)."""
    fig, axs = plt.subplots(1, 2, figsize=(11, 6.2))
    fig.suptitle('Calibrated SH loss vs. native SiNx shell absorption', fontsize=14, weight='bold',
                 x=0.08, ha='left')

    cal_frac_pct = 100.0 * df['sh_calibrated_dB_per_m'] / df['sh_absorption_dB_per_m']
    ax = axs[0]
    ax.hist(cal_frac_pct, bins=30, color=RAMP_LOSS[1], alpha=0.85)
    ax.set_xlabel('calibrated term / total SH absorption [%]')
    ax.set_ylabel('count (refined crossings)')
    style_ax(ax)

    ax = axs[1]
    for w, color in WCORE_COLORS.items():
        sel = df[df['w_core'] == w]
        if len(sel):
            ax.scatter(sel['sh_power_in_core'], sel['sh_calibrated_dB_per_m'], s=16, alpha=0.85,
                       color=color, edgecolor='none', label=f'w_core={w:g}')
    ax.set_yscale('log')
    ax.set_xlabel('SH power fraction in AlN core'); ax.set_ylabel('calibrated SH loss [dB/m] (log)')
    style_ax(ax)
    ax.legend(fontsize=7.5, frameon=False, loc='lower right')

    fig.text(0.08, 0.26,
              f"Median calibrated share of total SH absorption: {cal_frac_pct.median():.3f}%. The\n"
              f"device-anchored 100 dB/cm estimate (right panel, scales linearly with confinement as\n"
              f"designed) is real but {int(round(1/(cal_frac_pct.median()/100))):,}x smaller than the "
              f"native SiNx shell's own UV bulk\nabsorption at these overlaps -- the AM187 story mattered "
              f"for setting a sane SH-loss scale,\nbut in this geometry family it's not the dominant term.",
              fontsize=8.5, color=INK_FAINT, va='top', linespacing=1.6)
    fig.tight_layout(rect=(0, 0.33, 1, 0.92))
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


def mechanism_search_page(pdf, sweep_run='row6_hybrid_lateral', vertical_run='row6_hybrid_vertical'):
    """Dedicated answer to question 1: did TM00->TM20 (or an analogue) show up? Reads crossings.csv
    directly (not the refined-only subfigure frame) since this needs sh_label text matching across
    both status types for context, and the summary counts quoted in PLAN.md/to the user came from
    this exact query."""
    rows = []
    for run in (sweep_run, vertical_run):
        c = pd.read_csv(f'runs/{run}/crossings.csv')
        r = c[c['status'] == 'refined'].copy()
        hits = r[r['sh_label'].astype(str).str.match(r'^TM2[0-9]\??$')]
        hits = hits.assign(run=run)
        rows.append(hits)
    hits = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    hits = hits.sort_values('eta_pct_per_W_cm2', ascending=False) if len(hits) else hits

    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.92, 'Mechanism search: did TM00→TM20 (or an analogue) appear?', fontsize=16,
              weight='bold', color=INK)
    fig.text(0.08, 0.875,
              "Honda et al. 2025: AlN confined to one sign-lobe of a lateral TM2n mode lets d33 avoid\n"
              "self-cancellation across the mode's alternating-sign lobes -- the mechanism this\n"
              "lateral/vertical sweep pair was purpose-built to find.",
              fontsize=9.5, color=INK_MUTED, va='top', linespacing=1.5)

    fig.text(0.08, 0.775, 'RESULT: not found exactly, but close analogues exist', fontsize=10,
              weight='bold', color='#c9680e')
    fig.text(0.08, 0.745,
              f"No refined crossing in either run hits SH label TM20 itself. {len(hits)} refined\n"
              f"crossings hit the broader TM2n family (m=2 lateral, any vertical order) -- all at\n"
              f"n=5-9, not n=0. That IS the right lateral order (m=2, the self-cancellation-avoiding\n"
              f"signature), just with more vertical structure than the idealized target.",
              fontsize=9.5, color=INK_MUTED, va='top', linespacing=1.5)

    ax = fig.add_axes((0.08, 0.28, 0.86, 0.32))
    if len(hits):
        run_colors = {sweep_run: '#0072B2', vertical_run: '#D55E00'}
        x = np.arange(len(hits))
        colors = [run_colors.get(r, INK_FAINT) for r in hits['run']]
        ax.bar(x, hits['eta_pct_per_W_cm2'], color=colors, width=0.6)
        labels = [f"{p}→{s}\n{wl:.1f}nm" for p, s, wl in
                  zip(hits['pump_label'], hits['sh_label'], hits['wavelength_sh'])]
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5)
        ax.set_ylabel('eta [%/W/cm²]')
        style_ax(ax)
        from matplotlib.patches import Patch
        handles = [Patch(color=run_colors[sweep_run], label='row6_hybrid_lateral (lateral)'),
                   Patch(color=run_colors[vertical_run], label='row6_hybrid_vertical (vertical)')]
        ax.legend(handles=handles, fontsize=8, frameon=False, loc='upper right')
        ax.set_title('Every refined TM2n crossing found, ranked by eta', fontsize=10, color=INK)
    else:
        fig.text(0.5, 0.5, 'No TM2n crossings found', ha='center', fontsize=12, color=INK_FAINT)

    fig.text(0.08, 0.20,
              "Reading: these ARE the m=2 lateral family the mechanism predicts, achieving competitive\n"
              "NCE (up to ~12 %/W/cm² in the vertical sweep, ~10 %/W/cm² in the lateral sweep) despite\n"
              "not being the literal TM20. Worth a closer look at the actual field plots before\n"
              "concluding whether the extra vertical nodes are incidental or point to a geometry that\n"
              "would reach true TM20 with a different sin_height/sin_width combination than searched\n"
              "here -- not done as part of this report.",
              fontsize=9, color=INK_MUTED, va='top', linespacing=1.5)
    pdf.savefig(fig)
    plt.close(fig)


def sin_height_trend_page(pdf, vertical_run='row6_hybrid_vertical'):
    """Dedicated answer to question 2: does the pedestal family's 'smaller sin_height keeps
    winning' trend continue to the new sin_height=450 boundary point added 2026-10-12?"""
    import json
    c = pd.read_csv(f'runs/{vertical_run}/crossings.csv')
    r = c[c['status'] == 'refined'].copy()
    r['sin_height'] = r['params'].apply(lambda p: json.loads(p)['sin_height'])
    r['h_core'] = r['params'].apply(lambda p: json.loads(p)['h_core'])
    pivot = r.groupby(['h_core', 'sin_height'])['eta_pct_per_W_cm2'].max().unstack()

    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.92, 'Vertical sweep: does smaller sin_height keep winning?', fontsize=16,
              weight='bold', color=INK)
    fig.text(0.08, 0.875,
              "The pedestal family's archival data trended toward smaller sin_height across\n"
              "500-1100 nm without bottoming out in that range -- motivating this sweep's new\n"
              "sin_height=450 boundary point (h_core=250, the smallest margin-valid combination).",
              fontsize=9.5, color=INK_MUTED, va='top', linespacing=1.5)

    fig.text(0.08, 0.775, 'RESULT: no -- the trend reverses, peak is at sin_height=500', fontsize=10,
              weight='bold', color='#c9680e')
    fig.text(0.08, 0.745,
              "Best NCE at h_core=250: 71.8 %/W/cm² at sin_height=450 vs. 125.8 %/W/cm² at\n"
              "sin_height=500 -- the new boundary point is WORSE than its neighbor, not better. The\n"
              "real optimum sits in the interior of the tested range, not at either edge.",
              fontsize=9.5, color=INK_MUTED, va='top', linespacing=1.5)

    ax = fig.add_axes((0.10, 0.30, 0.82, 0.28))
    for h in sorted(pivot.index):
        row = pivot.loc[h].dropna()
        if len(row) < 2:
            continue
        color = HCORE_COLORS.get(int(h), INK_FAINT)
        marker = 'o'
        ax.plot(row.index, row.values, '-o', color=color, label=f'h_core={h:g}', markersize=5)
    ax.scatter([450], [pivot.loc[250.0, 450.0]], s=140, facecolor='none', edgecolor='#c9680e',
               linewidth=2, zorder=5)
    ax.annotate('new 2026-10-12\nboundary point', xy=(450, pivot.loc[250.0, 450.0]),
                xytext=(520, pivot.loc[250.0, 450.0] - 20), fontsize=8, color='#c9680e',
                arrowprops=dict(arrowstyle='->', color='#c9680e', lw=1))
    ax.set_xlabel('sin_height [nm]'); ax.set_ylabel('best eta [%/W/cm²] (per h_core)')
    ax.set_title('Best NCE per (h_core, sin_height), full vertical grid', fontsize=10.5, color=INK)
    style_ax(ax)
    ax.legend(fontsize=7.5, frameon=False, loc='upper right')

    fig.text(0.08, 0.20,
              "Every h_core row shows the same qualitative shape where tested widely enough: NCE rises\n"
              "from the tall/loose end down to an interior maximum, then falls again toward the\n"
              "tightest margin (more confinement helps up to a point, then the mode distorts/loss\n"
              "rises faster than overlap gains). h_core=250 is the only row dense enough near the\n"
              "boundary to resolve the turnaround explicitly; the global best (TM10→TM100,\n"
              "125.8 %/W/cm²) sits right at that interior peak.",
              fontsize=9, color=INK_MUTED, va='top', linespacing=1.5)
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
        ('min_loss', 'Min SH loss (scat+abs, incl. calibrated)', RAMP_LOSS, True),
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


def waterfall_page(pdf, df, n_bars=14):
    """One bar per geometry (its best crossing by eta), stacked into the dB-additive decomposition
    from nce_decomposition.py. Calls decompose(row) with BOTH flags at their False default: for
    this (hybrid, post-calibration) dataset sh_absorption_dB_per_m already has the calibrated term
    summed in at refine time (see survey.py's refine_crossing), so passing
    include_sh_calibrated=True here would double-count it -- that flag exists for REPROCESSING
    older rows that don't have it baked in, not for live hybrid-campaign rows."""
    import nce_decomposition as nd

    best_idx = df.groupby(['h_core', 'w_core', 'sin_width', 'sin_height'])['eta_pct_per_W_cm2'].idxmax()
    best = df.loc[best_idx].copy()
    decomps = [nd.decompose(row) for _, row in best.iterrows()]
    best = best.assign(**{k: [d[k] for d in decomps] for k in decomps[0]})
    best = best.sort_values('total_dB', ascending=False).head(n_bars)
    labels = [f"h{r.h_core:.0f}\nw{r.w_core:.0f}\nsw{r.sin_width:.0f}\nsh{r.sin_height:.0f}"
              for r in best.itertuples()]

    segs = [('shape_dB', 'overlap shape', '#0e9488'), ('field_dB', 'mode size / field', '#7570B3'),
            ('sh_loss_dB', 'SH loss', '#5b3df0'), ('pump_loss_dB', 'pump loss', '#c9680e'),
            ('length_dB', 'device length (5th, see notes)', '#c7c9d6')]

    fig = plt.figure(figsize=(11.5, 8.8))
    fig.suptitle('NCE breakdown: dB-additive waterfall per geometry', fontsize=14, weight='bold', x=0.07, ha='left')
    ax = fig.add_axes((0.08, 0.46, 0.88, 0.42))
    x = np.arange(len(best))
    pos_bottom = np.zeros(len(best))
    neg_bottom = np.zeros(len(best))
    for key, label, color in segs:
        vals = best[key].to_numpy()
        bottoms = np.where(vals >= 0, pos_bottom, neg_bottom)
        ax.bar(x, vals, bottom=bottoms, color=color, label=label, width=0.68)
        pos_bottom = np.where(vals >= 0, pos_bottom + vals, pos_bottom)
        neg_bottom = np.where(vals < 0, neg_bottom + vals, neg_bottom)
    ax.scatter(x, best['total_dB'], color=INK, zorder=5, s=22, label='total (= sum of segments)')
    ax.axhline(0, color=BORDER, lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=6.5)
    ax.set_ylabel('dB (10·log₁₀ of each power-like ratio)')
    style_ax(ax)

    fig.legend(*ax.get_legend_handles_labels(), fontsize=7.5, frameon=False, ncol=3,
               loc='upper center', bbox_to_anchor=(0.5, 0.40))

    fig.text(0.08, 0.28,
              "Top geometries by peak efficiency (hybrid family, best crossing per geometry). Positive\n"
              "segments stack upward, negative downward, from 0 -- the black dot always lands exactly on\n"
              "their sum. 'Mode size / field' is the one unbounded segment (a physical scale set by\n"
              "confinement and the d-tensor, not a 0-1 quality factor like the other three); everything\n"
              "else is <= 0 dB by construction (overlap_shape <= 1, loss always reduces L_eff).",
              fontsize=9, color=INK_MUTED)
    fig.text(0.08, 0.13,
              "'Device length' is a 5th, unrequested-but-necessary term: each bar is evaluated at ITS OWN\n"
              "optimal propagation length (loss_limited_length's L_opt, same quantity behind this project's\n"
              "usual peak_efficiency_pct_per_W) rather than one shared length -- without it the other four\n"
              "terms alone would not sum to the true total. See nce_decomposition.py's docstring for the\n"
              "two earlier (rejected) versions that didn't reconstruct the total on real data.",
              fontsize=8.5, color=INK_FAINT)
    pdf.savefig(fig)
    plt.close(fig)


def notes_page(pdf, df):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.92, 'Notes & provenance', fontsize=16, weight='bold', color=INK)
    text = (
        "Data: runs/row6_hybrid_lateral (lateral, w_core x sin_width @ fixed h_core=400/sin_height=700) and\n"
        "runs/row6_hybrid_vertical (vertical, h_core x sin_height @ fixed w_core=400/sin_width=700)\n"
        "crossings.csv, refined rows only. Extracted via extract_subfigure_data.py, rendered via\n"
        "build_hybrid_subfigure_report.py. Both launched together 2026-10-12 overnight, completed\n"
        "clean the next morning: 24/24 and 23/23 geometries 'ok', zero errors, cerenkov_allowed_any\n"
        "False on every refined crossing in both runs (nothing to flag per the standing checklist item).\n\n"
        "This is the CORRECTED 'hybrid' family -- AlN core embedded inside an SiNx shell, the actual\n"
        "Honda et al. 2025 structure -- not the 'pedestal' family (AlN stacked on top of SiNx), which\n"
        "is what every hybrid-named run before the 2026-10-10 geometry-construction fix had actually\n"
        "been building by accident. See the pedestal report and PLAN.md for that earlier story.\n\n"
        "sh_absorption_dB_per_m here already has the 2026-10-12 SH-loss calibration term summed in at\n"
        "refine time (survey.py's refine_crossing: abs_s = mechanisms + bulk_s + cal_s); the calibrated\n"
        "contribution alone is separately available as sh_calibrated_dB_per_m, used on the calibrated-\n"
        "fraction page above. Do not re-add it via nce_decomposition.decompose(..., "
        "include_sh_calibrated=True)\n"
        "on these rows -- that flag is for reprocessing OLDER rows that don't have it baked in; calling\n"
        "it here double-counts.\n\n"
        "overlap_shape is dimensionless 0-1, integrated over the AlN region only -- 1 means the SH field\n"
        "inside AlN is exactly proportional to the pump-driven polarization; it carries no information\n"
        "about HOW MUCH SH power actually reaches AlN (that's sh_power_in_core, measured separately).\n\n"
        "AlN is still modeled as lossless in its own right throughout (its own UV k remains a separate,\n"
        "open item, deliberately rejected as the SH-loss basis 2026-10-12 -- see build_assumptions_report\n"
        "section 3b); every absorption number above is SiNx shell bulk absorption plus the calibrated\n"
        "device-anchored term, never AlN's own intrinsic loss."
    )
    fig.text(0.08, 0.86, text, fontsize=9.5, color=INK_MUTED, va='top', linespacing=1.55)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    args = sys.argv[1:]
    out = args[0] if args and args[0].endswith('.pdf') else 'runs/hybrid_subfigure_report.pdf'
    runs = [a for a in args if not a.endswith('.pdf')] or ['row6_hybrid_lateral', 'row6_hybrid_vertical']
    df = load(runs)

    with PdfPages(out) as pdf:
        title_page(pdf, df)
        loss_pages(pdf, df)
        calibrated_fraction_page(pdf, df)
        overlap_pages(pdf, df)
        mechanism_search_page(pdf, runs[0] if len(runs) > 0 else 'row6_hybrid_lateral',
                               runs[1] if len(runs) > 1 else 'row6_hybrid_vertical')
        sin_height_trend_page(pdf, runs[1] if len(runs) > 1 else 'row6_hybrid_vertical')
        lateral = df[df['h_core'] == 400.0]
        geometry_maps_page(pdf, lateral, 'w_core', 'sin_width', 'w_core [nm]', 'sin_width [nm]',
                           'Lateral geometry maps', 'Fixed h_core = 400 nm, sin_height = 700 nm')
        vertical = df[(df['w_core'] == 400.0) & (df['sin_width'] == 700.0)]
        geometry_maps_page(pdf, vertical, 'h_core', 'sin_height', 'h_core [nm]', 'sin_height [nm]',
                           'Vertical geometry maps', 'Fixed w_core = 400 nm, sin_width = 700 nm')
        waterfall_page(pdf, df)
        notes_page(pdf, df)

    print(f'wrote {out} ({len(df)} refined crossings, runs={runs})')


if __name__ == '__main__':
    main()
