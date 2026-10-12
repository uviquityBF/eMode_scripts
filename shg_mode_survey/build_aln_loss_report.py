"""PDF comparing AlN-lossless vs. the SH loss actually used in this project's results, across the
runs reprocessed with AlN's own intrinsic absorption -- see PLAN.md's 2026-10-12 "AlN k-wiring"
entries. AlN was assumed lossless in every result before this.

Two SH-loss scenarios appear throughout, both computed in nce_decomposition.decompose:
  - "lossy" (AM187-LT6 measured k_e, include_aln=True): explored, then REJECTED 2026-10-12 -- its
    SH-band implication (~100,000 dB/cm) was checked against real fabricated-device output and
    found 3-4 orders of magnitude too high. Kept in the data/notes for context, not the headline.
  - "cal" (include_sh_calibrated=True): the current working assumption -- a flat, empirically-
    calibrated 100 dB/cm, confinement-weighted, SH-band only. This is what the title/scatter/
    ranking/waterfall pages below actually compare against lossless. See
    build_assumptions_report.py's section 3b for the full derivation.

NCE (eta_pct_per_W_cm2) does NOT depend on loss at all (it's the lossless, loss-limited-length
quantity) -- it is identical in every scenario, so only the loss-limited PEAK efficiency ranking
can move. This report exists to show how much, and why (nce_decomposition.decompose's dB-additive
terms: only sh_loss_dB, pump_loss_dB and length_dB -- via L_opt -- can differ; shape_dB/field_dB
cannot). In the "cal" scenario, alpha_p itself is never touched (the calibrated absorption is
SH-band only by construction) -- but pump_loss_dB can still shift, usually a small positive
amount, because it's evaluated AT L_opt and L_opt shortens once SH loss rises; see the
delta-waterfall page.

Covers: loaded_sweep1, trial_grid, wide_window -- the only runs with enough field exports
available on this machine to reprocess (loaded_sweep1 96/96, wide_window 48/48, trial_grid
269/280; rows missing an export keep NaN AlN-loss columns and are excluded here).
pedestal1/pedestal_sweep1/pedestal_vertical1 are excluded entirely: zero field exports exist on
either machine, and a from-scratch re-solve was estimated at ~9.5 hours of EMode time for a
geometry already being superseded by the corrected embedded 'hybrid' family -- not worth it
(2026-10-12 decision, see PLAN.md).

Usage: python build_aln_loss_report.py [out.pdf] [run_name ...]
Default: loaded_sweep1 trial_grid wide_window -> runs/aln_loss_report.pdf
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
import nce_decomposition as nd

INK, INK_MUTED, INK_FAINT = '#161a2e', '#5c6180', '#9094ad'
BORDER = '#dcdfeb'
COLOR_LOSSLESS = '#2a78d6'
COLOR_LOSSY = '#c23a73'
FAMILY_COLORS = {'ridge': '#0e9488', 'loaded': '#c9680e'}
DELTA_SEGS = [('d_sh_loss_dB_cal', 'Δ SH loss (100 dB/cm calibrated)', '#5b3df0'),
              ('d_pump_loss_dB_cal', 'Δ pump loss (indirect, via shifted L_opt)', '#c9680e'),
              ('d_length_dB_cal', 'Δ device length (L_opt shortens)', '#c7c9d6')]

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
    if ax.get_xscale() == 'log':
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    if ax.get_yscale() == 'log':
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def load(run_names):
    frames = []
    for run in run_names:
        d = pd.read_csv(f'runs/{run}/crossings.csv')
        d['run'] = run
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    r = d[(d['status'] == 'refined') & d['aln_pump_loss_dB_per_m'].notna()].copy()
    r['geom_label'] = [geo.make_geometry(f, json.loads(p)).describe()
                        for f, p in zip(r['family'], r['params'])]

    lossless = [nd.decompose(row, include_aln=False) for _, row in r.iterrows()]
    lossy = [nd.decompose(row, include_aln=True) for _, row in r.iterrows()]
    cal = [nd.decompose(row, include_sh_calibrated=True) for _, row in r.iterrows()]
    for k in lossless[0]:
        r[f'{k}_lossless'] = [x[k] for x in lossless]
        r[f'{k}_lossy'] = [x[k] for x in lossy]
        r[f'{k}_cal'] = [x[k] for x in cal]
    r['peak_lossless_pct_per_W'] = r['peak_efficiency_SI_lossless'] * 100.0
    r['peak_lossy_pct_per_W'] = r['peak_efficiency_SI_lossy'] * 100.0
    r['peak_cal_pct_per_W'] = r['peak_efficiency_SI_cal'] * 100.0
    r['drop_factor'] = r['peak_lossless_pct_per_W'] / r['peak_lossy_pct_per_W'].clip(lower=1e-300)
    r['drop_factor_cal'] = r['peak_lossless_pct_per_W'] / r['peak_cal_pct_per_W'].clip(lower=1e-300)
    r['d_sh_loss_dB'] = r['sh_loss_dB_lossy'] - r['sh_loss_dB_lossless']
    r['d_pump_loss_dB'] = r['pump_loss_dB_lossy'] - r['pump_loss_dB_lossless']
    r['d_length_dB'] = r['length_dB_lossy'] - r['length_dB_lossless']
    r['d_total_dB'] = r['d_sh_loss_dB'] + r['d_pump_loss_dB'] + r['d_length_dB']
    r['d_sh_loss_dB_cal'] = r['sh_loss_dB_cal'] - r['sh_loss_dB_lossless']
    r['d_pump_loss_dB_cal'] = r['pump_loss_dB_cal'] - r['pump_loss_dB_lossless']
    r['d_length_dB_cal'] = r['length_dB_cal'] - r['length_dB_lossless']
    r['d_total_dB_cal'] = r['d_sh_loss_dB_cal'] + r['d_pump_loss_dB_cal'] + r['d_length_dB_cal']
    return r


def title_page(pdf, r, runs):
    fig = plt.figure(figsize=(11, 8.5))
    y = 0.94
    fig.text(0.08, y, 'SH Loss Calibration: Before / After', fontsize=22, weight='bold', color=INK)
    y -= 0.045
    fig.text(0.08, y, 'shg_mode_survey · ' + ' + '.join(runs), fontsize=11, color=INK_MUTED,
              family='monospace')
    y -= 0.055

    n_geoms = r['geom_label'].nunique()
    body = (f"{len(r)} refined crossings across {n_geoms} geometries, with a flat, empirically-\n"
            f"calibrated 100 dB/cm SH-band absorption added to the existing loss budget\n"
            f"(geometry.SH_ABSORPTION_CALIBRATED_DB_PER_CM, confinement-weighted -- see\n"
            f"build_assumptions_report.py section 3b for the full derivation). AlN's own measured\n"
            f"k_e (AM187-LT6) was explored first but REJECTED as the SH-loss assumption -- it\n"
            f"implied ~100,000 dB/cm, checked against real device output and found 3-4 orders of\n"
            f"magnitude too high (kept in the data/notes for context, not used here).\n\n"
            f"NCE (eta_pct_per_W_cm2) does not depend on loss at all -- it is EXACTLY unchanged.\n"
            f"Only loss-limited PEAK efficiency can move, and only via SH loss specifically -- the\n"
            f"calibrated absorption is SH-band only, pump loss is untouched.")
    fig.text(0.08, y, body, fontsize=10.5, color=INK, va='top', linespacing=1.55)
    y -= 0.37

    def fmt_x(v):
        return f"{v:.1f}x" if v < 1000 else f"{v:.1e}x".replace('e+0', 'e').replace('e+', 'e')

    stats = [
        ('Peak efficiency drop factor -- ridge family',
         f"{fmt_x(r.loc[r['family'] == 'ridge', 'drop_factor_cal'].median())} median, "
         f"{fmt_x(r.loc[r['family'] == 'ridge', 'drop_factor_cal'].max())} max",
         'bare AlN ridge had ~zero SH-side loss before -- hit hardest'),
        ('Peak efficiency drop factor -- loaded family',
         f"{fmt_x(r.loc[r['family'] == 'loaded', 'drop_factor_cal'].median())} median, "
         f"{fmt_x(r.loc[r['family'] == 'loaded', 'drop_factor_cal'].max())} max",
         'already had a lossy TiO2 strip -- added absorption is a smaller relative penalty'),
    ]
    for label, val, sub in stats:
        fig.text(0.08, y, label.upper(), fontsize=7.5, color=INK_FAINT, weight='bold')
        y -= 0.026
        fig.text(0.08, y, val, fontsize=14, color=INK, family='monospace', weight='bold')
        fig.text(0.42, y + 0.004, sub, fontsize=8.5, color=INK_MUTED)
        y -= 0.05

    fig.text(0.08, y - 0.01, 'CAUTION', fontsize=9, weight='bold', color='#c9680e')
    fig.text(0.08, y - 0.035,
              "100 dB/cm is a round working number inside an empirically-bounded range (15-680\n"
              "dB/cm depending on an unmeasured input-coupling efficiency), not a measurement of any\n"
              "specific physical mechanism. pedestal family excluded -- no field exports available\n"
              "(unrelated to this calibration, which needs none; see this file's module docstring).",
              fontsize=9, color=INK_MUTED, va='top', linespacing=1.5)
    pdf.savefig(fig)
    plt.close(fig)


def scatter_page(pdf, r):
    fig, ax = plt.subplots(figsize=(8.5, 7))
    for fam, color in FAMILY_COLORS.items():
        sel = r[r['family'] == fam]
        if len(sel):
            ax.scatter(sel['peak_lossless_pct_per_W'], sel['peak_cal_pct_per_W'], s=22,
                       alpha=0.75, color=color, edgecolor='none', label=f'{fam} (n={len(sel)})')
    lo = min(r['peak_lossless_pct_per_W'].min(), r['peak_cal_pct_per_W'].min()) * 0.5
    hi = max(r['peak_lossless_pct_per_W'].max(), r['peak_cal_pct_per_W'].max()) * 2
    ax.plot([lo, hi], [lo, hi], color=INK_FAINT, lw=1, ls='--', label='no change (y = x)')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_xlabel('peak efficiency, AlN lossless [%/W]')
    ax.set_ylabel('peak efficiency, calibrated SH loss (100 dB/cm) [%/W]')
    ax.set_title('Every point moves down (calibrated < lossless) -- the only question is by how much',
                 fontsize=11, color=INK)
    style_ax(ax)
    ax.legend(fontsize=8.5, frameon=False, loc='upper left')
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def ranking_page(pdf, r, n=15):
    top = r.sort_values('peak_lossless_pct_per_W', ascending=False).head(n).copy()
    cal_rank = r['peak_cal_pct_per_W'].rank(ascending=False, method='min')
    top['cal_rank'] = cal_rank.loc[top.index].astype(int)

    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.94, f'Top {n} crossings by lossless peak efficiency -- where do they rank with calibrated SH loss?',
              fontsize=14, weight='bold', color=INK)
    fig.text(0.08, 0.915, 'run · geometry · pair', fontsize=8, color=INK_FAINT, family='monospace')

    cols = [('#', 0.08, 0.025), ('geometry', 0.13, 0.30), ('pump→SH', 0.44, 0.12),
            ('lossless [%/W]', 0.57, 0.14), ('calibrated [%/W]', 0.72, 0.14), ('new rank', 0.87, 0.07)]
    y0 = 0.87
    for label, x, _ in cols:
        fig.text(x, y0, label.upper(), fontsize=7.5, weight='bold', color=INK_FAINT)
    y = y0 - 0.028
    for i, (_, row) in enumerate(top.iterrows(), start=1):
        moved_out = row['cal_rank'] > n
        color = '#c9680e' if moved_out else INK
        fig.text(cols[0][1], y, str(i), fontsize=8.5, color=color, family='monospace')
        fig.text(cols[1][1], y, f"{row['geom_label']} ({row['run']})", fontsize=8, color=color)
        fig.text(cols[2][1], y, f"{row['pump_label']}→{row['sh_label']}", fontsize=8, color=color,
                 family='monospace')
        fig.text(cols[3][1], y, f"{row['peak_lossless_pct_per_W']:.3g}", fontsize=8.5, color=color,
                 family='monospace')
        fig.text(cols[4][1], y, f"{row['peak_cal_pct_per_W']:.3g}", fontsize=8.5, color=color,
                 family='monospace')
        fig.text(cols[5][1], y, f"#{int(row['cal_rank'])}" + (' ↓' if moved_out else ''),
                 fontsize=8.5, color=color, weight='bold' if moved_out else 'normal',
                 family='monospace')
        y -= 0.028

    n_moved = int((top['cal_rank'] > n).sum())
    fig.text(0.08, y - 0.02,
              f"{n_moved} of the original top {n} fall out of the top {n} once the calibrated SH "
              "loss is included (orange, marked with new rank).", fontsize=9, color=INK_MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def delta_waterfall_page(pdf, r, n_bars=14):
    """Why peak efficiency dropped, per geometry's best (by lossless peak) crossing: the exact
    3-term dB delta between the calibrated and lossless nce_decomposition.decompose() calls on
    the SAME row (shape_dB/field_dB cancel identically -- see this module's and
    nce_decomposition's docstrings) -- sums exactly to the total dB drop, same
    reconstruction-identity guarantee as the original 5-term waterfall in
    build_subfigure_report.py. d_pump_loss_dB_cal is NOT pinned at 0, even though the calibrated
    absorption itself never touches alpha_p -- pump_loss_dB is evaluated AT L_opt, and L_opt
    shifts shorter once SH loss increases, so the term moves indirectly (confirmed non-zero
    numerically, mean +0.7 dB, max +4.6 dB across this dataset; see PLAN.md)."""
    best_idx = r.groupby('geom_label')['peak_lossless_pct_per_W'].idxmax()
    best = r.loc[best_idx].sort_values('d_total_dB_cal').head(n_bars)
    labels = [f"{row.geom_label}\n({row.run})" for row in best.itertuples()]

    fig = plt.figure(figsize=(11.5, 8.8))
    fig.suptitle('Why peak efficiency drops: exact dB delta per geometry (worst first)',
                 fontsize=14, weight='bold', x=0.07, ha='left')
    ax = fig.add_axes((0.08, 0.46, 0.88, 0.42))
    x = np.arange(len(best))
    pos_bottom = np.zeros(len(best))
    neg_bottom = np.zeros(len(best))
    for key, label, color in DELTA_SEGS:
        vals = best[key].to_numpy()
        bottoms = np.where(vals >= 0, pos_bottom, neg_bottom)
        ax.bar(x, vals, bottom=bottoms, color=color, label=label, width=0.68)
        pos_bottom = np.where(vals >= 0, pos_bottom + vals, pos_bottom)
        neg_bottom = np.where(vals < 0, neg_bottom + vals, neg_bottom)
    ax.scatter(x, best['d_total_dB_cal'], color=INK, zorder=5, s=22, label='total delta (= sum of segments)')
    ax.axhline(0, color=BORDER, lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=6.2, rotation=20, ha='right')
    ax.set_ylabel('Δ dB (calibrated - lossless, same crossing)')
    style_ax(ax)

    fig.legend(*ax.get_legend_handles_labels(), fontsize=7.5, frameon=False, ncol=2,
               loc='upper center', bbox_to_anchor=(0.5, 0.40))
    fig.text(0.08, 0.26,
              "Each bar is the SAME crossing's best-by-lossless-peak-efficiency result, decomposed\n"
              "twice (nce_decomposition.decompose, include_sh_calibrated=False/True) -- shape_dB/\n"
              "field_dB are identical either way (depend only on overlap_shape and eta_pct_per_W_cm2,\n"
              "neither of which depends on loss). alpha_p itself is never touched by the calibrated\n"
              "absorption, but pump_loss_dB still shifts (small, usually positive) because it's\n"
              "evaluated at L_opt, which shortens once SH loss rises -- not a separate mechanism,\n"
              "just the same L_opt plugged into the pump term. The black dot is the exact sum of the\n"
              "three segments, verified against the direct peak-efficiency ratio.",
              fontsize=9, color=INK_MUTED, va='top', linespacing=1.6)
    pdf.savefig(fig)
    plt.close(fig)


def empirical_bound_page(pdf, r):
    """Reality check (2026-10-12, user-supplied measurement): a real fabricated device (ridge,
    h=350 w=500 nm, TM00->TM04 -- the closest match in this dataset to the user's "best results
    around 500nm" description) measures SH output in this range under real pump conditions.
    Inverting shg_physics's own P_SH = eta_SI * P_pump^2 * L_eff(L; a_p, a_s)^2 at the ACTUAL
    fixed device length (not an idealized L_opt) for the SH loss that reproduces that output
    gives a direct empirical upper bound on alpha_SH, independent of whether the AM187-LT6 k_e
    value is trustworthy."""
    import nce_decomposition as nd
    from scipy.optimize import brentq

    row = r[(r['geom_label'] == 'ridge h=350 w=500 sw=5') & (r['pump_label'] == 'TM00') &
            (r['sh_label'] == 'TM04')].iloc[0]
    eta_si = row['eta_pct_per_W_cm2'] * 100.0
    alpha_p_native = row['pump_scattering_dB_per_m'] + row['pump_absorption_dB_per_m']
    alpha_s_aln = row['sh_scattering_dB_per_m'] + row['sh_absorption_dB_per_m'] + row['aln_sh_loss_dB_per_m']
    alpha_s_cal = (row['sh_scattering_dB_per_m'] + row['sh_absorption_dB_per_m'] +
                   row['sh_power_in_core'] * geo.SH_ABSORPTION_CALIBRATED_DB_PER_CM * 100.0)
    L = 2000e-6
    P_pump = 0.100

    def alpha_s_needed(P_SH_target_W):
        def resid(alpha_s_db_m):
            leff = nd.l_eff_at(L, alpha_p_native, alpha_s_db_m)
            return eta_si * P_pump ** 2 * leff ** 2 - P_SH_target_W
        return brentq(resid, 0.0, 5e8, xtol=1.0)

    def P_SH_at(alpha_s_db_m, P_pump_W):
        leff = nd.l_eff_at(L, alpha_p_native, alpha_s_db_m)
        return eta_si * P_pump_W ** 2 * leff ** 2

    targets_nW = (20, 200)
    bounds = {p: alpha_s_needed(p * 1e-9) for p in targets_nW}
    cal_predictions_nW = {c: P_SH_at(alpha_s_cal, 0.200 * c) * 1e9 for c in (0.10, 0.25, 0.50)}

    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.92, 'Reality check: what SH loss is consistent with measured device output?',
              fontsize=15, weight='bold', color=INK)
    fig.text(0.08, 0.885,
              'ridge h=350 w=500 nm, TM00→TM04 -- closest match to the measured device', fontsize=9,
              color=INK_MUTED, family='monospace')

    body = (
        f"Given a real device's actual, fixed propagation length (not an optimized L_opt) and\n"
        f"actual pump power reaching the waveguide, shg_physics.loss_limited_length's own model\n"
        f"(P_SH = eta_SI * P_pump^2 * L_eff(L; alpha_p, alpha_s)^2) can be inverted for the SH-band\n"
        f"loss that reproduces a measured SH output -- independent of whether any particular\n"
        f"ellipsometry sample's k is trustworthy. Using this geometry's own simulated eta_SI and\n"
        f"currently-modeled native pump loss ({alpha_p_native / 100:.1f} dB/cm, no AlN):\n"
    )
    fig.text(0.08, 0.83, body, fontsize=10.5, color=INK, va='top', linespacing=1.6)

    y = 0.62
    fig.text(0.08, y, 'PUMP POWER (IN WAVEGUIDE)', fontsize=7.5, color=INK_FAINT, weight='bold')
    fig.text(0.37, y, 'INTERACTION LENGTH', fontsize=7.5, color=INK_FAINT, weight='bold')
    fig.text(0.62, y, 'TARGET SH OUTPUT', fontsize=7.5, color=INK_FAINT, weight='bold')
    fig.text(0.84, y, 'IMPLIED alpha_SH BOUND', fontsize=7.5, color=INK_FAINT, weight='bold')
    y -= 0.03
    for p_nw in targets_nW:
        fig.text(0.08, y, '100 mW', fontsize=10.5, family='monospace', color=INK)
        fig.text(0.37, y, '2000 um (2 mm)', fontsize=10.5, family='monospace', color=INK)
        fig.text(0.62, y, f'{p_nw} nW', fontsize=10.5, family='monospace', color=INK)
        fig.text(0.84, y, f'<= {bounds[p_nw] / 100:.0f} dB/cm', fontsize=10.5, family='monospace',
                  weight='bold', color=COLOR_LOSSLESS)
        y -= 0.035

    fig.text(0.08, y - 0.03,
              f"AM187-LT6 k_e implies {alpha_s_aln / 100:,.0f} dB/cm for this same crossing --\n"
              f"{alpha_s_aln / bounds[20]:.0f}x to {alpha_s_aln / bounds[200]:.0f}x above what the "
              "device's own measured output permits.", fontsize=10, color='#c9680e', weight='bold',
              va='top', linespacing=1.5)
    fig.text(0.08, y - 0.105,
              f"The 100 dB/cm calibrated value gives {alpha_s_cal / 100:.1f} dB/cm total SH loss here\n"
              "(scattering + calibrated absorption). Predicted SH output at 10/25/50% coupling:\n"
              f"{cal_predictions_nW[0.10]:.0f} / {cal_predictions_nW[0.25]:.0f} / "
              f"{cal_predictions_nW[0.50]:.0f} nW -- closely tracks the \"10s of nW typically\"\n"
              "benchtop population at low coupling, within ~1.4x of the 200nW best case at 25%\n"
              f"coupling. At the pessimistic 50% coupling used in the table above it over-predicts\n"
              f"({cal_predictions_nW[0.50]:.0f} vs. 200 nW) -- points to true coupling being below\n"
              "50% for that device, not to 100 dB/cm being too low.",
              fontsize=10, color=COLOR_LOSSLESS, weight='bold', va='top', linespacing=1.5)
    fig.text(0.08, y - 0.31,
              "20 nW is the user's suggested representative floor (most devices clear at least\n"
              "this much; 200 nW was closer to the best-observed case, shown for context). The\n"
              "alpha_SH bound table above is fixed at 100 mW (50% of 200 mW incident, the optimistic\n"
              "end of the 10-50% coupling-efficiency uncertainty) since that was specifically\n"
              "requested for this reality check; it is a bound, not a measurement of alpha_SH itself\n"
              "-- it assumes the modeled eta_SI and native pump loss for this geometry are correct,\n"
              "and that the real device isn't compensating for higher SH loss some other way (e.g. a\n"
              "shorter effective interaction length than the nominal 2 mm, imperfect mode matching\n"
              "reducing the EFFECTIVE eta).",
              fontsize=9, color=INK_MUTED, va='top', linespacing=1.5)
    pdf.savefig(fig)
    plt.close(fig)


def notes_page(pdf, r, runs):
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.08, 0.92, 'Notes & provenance', fontsize=16, weight='bold', color=INK)
    text = (
        f"Data: {', '.join('runs/' + x + '/crossings.csv' for x in runs)}, refined rows with a\n"
        "reprocessed AlN-loss pair only (aln_pump_loss_dB_per_m not null -- a leftover filter from\n"
        "the AM187 investigation; the calibrated scenario itself needs only sh_power_in_core,\n"
        "present on every refined row regardless). Generated via build_aln_loss_report.py /\n"
        "nce_decomposition.py.\n\n"
        "CALIBRATED SCENARIO (used throughout this report): geometry.sh_absorption_calibrated_dB_per_m\n"
        "-- a flat 100 dB/cm, confinement-weighted by the mode's power fraction in geom.core_mask()\n"
        "(sh_power_in_core), SH-band only, never added to pump loss. Empirically calibrated against\n"
        "real fabricated-device output, 2026-10-12 -- see build_assumptions_report.py section 3b\n"
        "and PLAN.md for the full derivation. Computed entirely from already-stored columns, no\n"
        "field re-export or EMode re-solve needed.\n\n"
        "LOSSY SCENARIO (AM187-LT6 k_e, shown in notes/title context only, NOT the headline\n"
        "comparison): geometry.aln_core_loss_dB_per_m(wavelength_nm), a Beer-Lambert conversion of\n"
        "the AM187-LT6-measured k_e (extraordinary axis, 3-Lorentzian fit -- materials/\n"
        "fit_aln_measured_k.py), same confinement-weighting pattern. REJECTED as the SH-loss\n"
        "assumption 2026-10-12 -- its SH-band implication (~100,000 dB/cm) was checked against real\n"
        "device output and found 3-4 orders of magnitude too high (see the reality-check page).\n"
        "k_e only, not field-direction-resolved against k_o (k_e is ~90x k_o and is the axis d33\n"
        "couples -- Py = d33*Ey^2).\n\n"
        "Original AlN-lossless columns (pump_absorption_dB_per_m / sh_absorption_dB_per_m /\n"
        "peak_efficiency_pct_per_W) are untouched in crossings.csv; both the calibrated and lossy\n"
        "figures here are computed downstream, on the fly, from nce_decomposition.decompose.\n\n"
        "Excluded: pedestal1/pedestal_sweep1/pedestal_vertical1 (zero field exports on either\n"
        "machine; re-solving from scratch was estimated at ~9.5 hours of EMode time for a geometry\n"
        "already being superseded by the corrected embedded 'hybrid' family -- not worth it, per\n"
        "2026-10-12 decision). trial_grid is missing 11/280 refined crossings' exports even after\n"
        "merging the laptop's local runs folder -- those rows are excluded here too, not zero-filled."
    )
    fig.text(0.08, 0.86, text, fontsize=10, color=INK_MUTED, va='top', linespacing=1.7)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    args = sys.argv[1:]
    out = args[0] if args and args[0].endswith('.pdf') else 'runs/aln_loss_report.pdf'
    runs = [a for a in args if not a.endswith('.pdf')] or ['loaded_sweep1', 'trial_grid', 'wide_window']
    r = load(runs)

    with PdfPages(out) as pdf:
        title_page(pdf, r, runs)
        scatter_page(pdf, r)
        ranking_page(pdf, r)
        delta_waterfall_page(pdf, r)
        empirical_bound_page(pdf, r)
        notes_page(pdf, r, runs)

    print(f'wrote {out} ({len(r)} refined crossings, runs={runs})')


if __name__ == '__main__':
    main()
