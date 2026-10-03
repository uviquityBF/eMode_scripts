"""Summary tables + plots for a survey run (no EMode needed).

Writes runs/<run>/summary/:
  summary.md                 top crossings by NCE and by loss-limited peak efficiency, best per geometry
  top_by_nce.csv, top_by_peak.csv
  nce_vs_width.png           NCE (log) vs core width, one panel per height, coloured by pump mode
  peak_vs_width.png          loss-limited peak efficiency vs width (refined crossings only)
  lambda_vs_width.png        phase-matching wavelength vs width
  dispersion/<fp>.png        pump n_eff(lambda_SH) curves, SH tracks, crossings -- per geometry
Usage: python summarize_run.py <run_name>
"""

import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
# fixed categorical order (pump identity), never cycled; anything else -> muted gray
PUMP_COLORS = {'TM00': '#2a78d6', 'TM10': '#eb6834', 'TM01': '#1baf7a', 'TE00': '#eda100',
               'TE01': '#e87ba4', 'TM20': '#008300', 'TE10': '#4a3aa7', 'TM02': '#e34948'}
OTHER = '#898781'
GRID = '#e1e0d9'
INK = '#0b0b0b'
MUTED = '#898781'


def style(ax):
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#c3c2b7')
    ax.tick_params(colors=MUTED, labelsize=8)


def load(run_dir):
    c = pd.read_csv(os.path.join(run_dir, 'crossings.csv'))
    g = pd.read_csv(os.path.join(run_dir, 'geometries.csv'))
    for df in (c, g):
        p = df['params'].apply(json.loads)
        df['h'] = p.apply(lambda d: d.get('h_core'))
        df['w'] = p.apply(lambda d: d.get('w_core'))
    c['pair'] = c['pump_label'] + '->' + c['sh_label']
    return c, g


def scatter_vs_width(c, ycol, ylabel, path, log=True, title=''):
    hs = sorted(c['h'].unique())
    fig, axs = plt.subplots(1, len(hs), figsize=(4.2 * len(hs), 3.8), sharey=True, squeeze=False)
    pumps_seen = []
    for ax, h in zip(axs[0], hs):
        d = c[c['h'] == h]
        for pump, dd in d.groupby('pump_label'):
            col = PUMP_COLORS.get(pump, OTHER)
            pumps_seen.append(pump)
            ref = dd[dd['status'] == 'refined']
            scr = dd[dd['status'] != 'refined']
            ax.scatter(scr['w'], scr[ycol], s=22, facecolors='none', edgecolors=col, linewidths=1.0)
            ax.scatter(ref['w'], ref[ycol], s=30, color=col, edgecolors='white', linewidths=0.8)
        # label the best point per width with its SH mode
        for w, dd in d.groupby('w'):
            b = dd.loc[dd[ycol].idxmax()]
            if np.isfinite(b[ycol]) and b[ycol] > 0:
                ax.annotate(b['sh_label'], (w, b[ycol]), textcoords='offset points', xytext=(0, 6),
                            ha='center', fontsize=7, color=INK)
        ax.set_title(f'h = {h:g} nm', fontsize=10, color=INK)
        ax.set_xlabel('core width w [nm]', fontsize=9, color=INK)
        if log:
            ax.set_yscale('log')
        style(ax)
    axs[0][0].set_ylabel(ylabel, fontsize=9, color=INK)
    handles = [plt.Line2D([], [], marker='o', ls='', color=PUMP_COLORS.get(p, OTHER), label=f'pump {p}')
               for p in sorted(set(pumps_seen), key=lambda p: list(PUMP_COLORS).index(p) if p in PUMP_COLORS else 99)]
    handles += [plt.Line2D([], [], marker='o', ls='', color=MUTED, label='refined'),
                plt.Line2D([], [], marker='o', ls='', mfc='none', color=MUTED, label='screened only')]
    fig.legend(handles=handles, loc='upper center', ncol=len(handles), fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, 1.0))
    fig.suptitle(title, fontsize=10, y=1.07, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)


def dispersion_plot(run_dir, fp, c, title, path):
    t = np.load(os.path.join(run_dir, 'traces', f'{fp}.npz'))
    lam = t['lambda_sh']
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for row in t['sh_n']:
        ax.plot(lam, row, color='#c3c2b7', linewidth=0.8)
    if 'n_guided_cutoff' in t:
        ax.plot(lam, t['n_guided_cutoff'], color=MUTED, linewidth=1.2, linestyle='--',
                label='guided cutoff (max clad index)')
    for lbl, n in zip(t['pump_labels'], t['pump_n']):
        ax.plot(lam, n, color=PUMP_COLORS.get(str(lbl), OTHER), linewidth=2, label=f'pump {lbl}')
    cc = c[c['fingerprint'] == fp]
    for _, r in cc.iterrows():
        ax.scatter(r['wavelength_sh'], r['n_eff_sh'], s=26, color=PUMP_COLORS.get(r['pump_label'], OTHER),
                   edgecolors='white', linewidths=0.8, zorder=5)
    ax.set_xlabel('SH wavelength [nm]  (pump at 2x)', fontsize=9, color=INK)
    ax.set_ylabel('effective index', fontsize=9, color=INK)
    ax.set_title(title, fontsize=10, color=INK)
    style(ax)
    ax.legend(fontsize=7, frameon=False, loc='best')
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def md_table(df, cols, fmt):
    lines = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in df.iterrows():
        lines.append('| ' + ' | '.join(fmt.get(k, '{}').format(r[k]) for k in cols) + ' |')
    return '\n'.join(lines)


def main(run_name):
    run_dir = os.path.join(HERE, 'runs', run_name)
    out = os.path.join(run_dir, 'summary')
    os.makedirs(os.path.join(out, 'dispersion'), exist_ok=True)
    c, g = load(run_dir)
    fmt = {'h': '{:g}', 'w': '{:g}', 'wavelength_sh': '{:.2f}', 'eta_pct_per_W_cm2': '{:.3g}',
           'overlap_shape': '{:.4f}', 'A_shg_um2': '{:.3g}', 'A_eff_pump_um2': '{:.3f}',
           'A_eff_sh_um2': '{:.3f}', 'L_opt_mm': '{:.2f}', 'peak_efficiency_pct_per_W': '{:.3g}',
           'sh_te_fraction': '{:.2f}', 'pump_scattering_dB_per_m': '{:.0f}',
           'sh_scattering_dB_per_m': '{:.0f}'}
    cols = ['h', 'w', 'pump_label', 'sh_label', 'sh_te_fraction', 'wavelength_sh', 'eta_pct_per_W_cm2',
            'overlap_shape', 'A_shg_um2', 'A_eff_pump_um2', 'A_eff_sh_um2', 'status']
    top_nce = c.sort_values('eta_pct_per_W_cm2', ascending=False).head(25)
    ref = c[c['status'] == 'refined']
    top_peak = ref.sort_values('peak_efficiency_pct_per_W', ascending=False).head(25)
    top_nce.to_csv(os.path.join(out, 'top_by_nce.csv'), index=False)
    top_peak.to_csv(os.path.join(out, 'top_by_peak.csv'), index=False)
    best = c.loc[c.groupby('fingerprint')['eta_pct_per_W_cm2'].idxmax()].sort_values(['h', 'w'])
    tm = c[(c['sh_te_fraction'] < 0.5) & c['pump_label'].str.startswith('TM')]
    pair_best = (tm.sort_values('eta_pct_per_W_cm2', ascending=False)
                 .groupby('pair').head(1).head(20))
    with open(os.path.join(out, 'summary.md'), 'w', encoding='utf-8') as f:
        f.write(f"# Survey run `{run_name}`\n\n{len(g)} geometries "
                f"({(g['status'] == 'ok').sum()} ok, {(g['status'] != 'ok').sum()} failed), "
                f"{len(c)} guided phase-match crossings ({len(ref)} refined).\n\n")
        f.write("NCE = normalized conversion efficiency [%/W/cm^2], lossless; peak = "
                "loss-limited eta*L_eff^2 [%/W] at L_opt (pump: native scattering + interface "
                "absorption; SH: native scattering only, no UV absorption data yet). "
                "overlap_shape is 0..1; A_shg is the plane-wave-equivalent interaction area for "
                "AlN d33.\n\n")
        f.write("## Top 25 by NCE\n\n" + md_table(top_nce, cols, fmt) + "\n\n")
        f.write("## Top 25 by loss-limited peak efficiency (refined)\n\n" +
                md_table(top_peak, cols[:6] + ['eta_pct_per_W_cm2', 'pump_scattering_dB_per_m',
                                               'sh_scattering_dB_per_m', 'L_opt_mm',
                                               'peak_efficiency_pct_per_W'], fmt) + "\n\n")
        f.write("## Best TM->TM pairs (best instance of each pump->SH pair)\n\n" +
                md_table(pair_best, cols, fmt) + "\n\n")
        f.write("## Best crossing per geometry\n\n" + md_table(best, cols, fmt) + "\n")
    scatter_vs_width(c, 'eta_pct_per_W_cm2', 'NCE [%/W/cm²]', os.path.join(out, 'nce_vs_width.png'),
                     title='Guided phase matches in the SH window: normalized conversion efficiency')
    if len(ref):
        scatter_vs_width(ref, 'peak_efficiency_pct_per_W', 'peak efficiency [%/W]',
                         os.path.join(out, 'peak_vs_width.png'),
                         title='Loss-limited peak efficiency at the optimum length (refined crossings)')
    scatter_vs_width(c, 'wavelength_sh', 'phase-matched SH wavelength [nm]',
                     os.path.join(out, 'lambda_vs_width.png'), log=False,
                     title='Where each phase match falls in the SH window')
    for _, r in g[g['status'] == 'ok'].iterrows():
        tp = os.path.join(run_dir, 'traces', f"{r['fingerprint']}.npz")
        if os.path.exists(tp):
            dispersion_plot(run_dir, r['fingerprint'], c, f"h={r['h']:g} w={r['w']:g}",
                            os.path.join(out, 'dispersion', f"h{r['h']:g}_w{r['w']:g}.png"))
    print(f"wrote {out}")


if __name__ == '__main__':
    main(sys.argv[1])
