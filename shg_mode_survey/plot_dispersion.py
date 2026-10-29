"""Dispersion diagram with every phase-match crossing of one geometry (no EMode needed).

x: SH wavelength (pump at 2x), y: effective index. Gray lines = tracked SH modes, coloured thick lines =
pump modes, dashed = guided cutoff (max cladding/substrate index). Each crossing is a marker at the
point where an SH track crosses a pump curve: size ~ log10(NCE), filled = refined, hollow = screened
only, red ring = window/box-mode artifact (sh_edge_ratio > 0.02, excluded from refinement/ranking).
The best crossings by NCE are labelled "pump->SH (NCE)".

Usage: python plot_dispersion.py <run_with_crossings> <h_core> <w_core> [traces_run] [out.png]
  traces_run: run folder holding traces/<fp>.npz if different (traces/ is gitignored and was left
  under the pre-rename name for the early ridge runs, e.g. crossings in row1_ridge_v1, traces in trial_grid).
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
PUMP_COLORS = {'TM00': '#2a78d6', 'TM10': '#eb6834', 'TM01': '#1baf7a', 'TE00': '#eda100',
               'TE01': '#e87ba4', 'TM20': '#008300', 'TE10': '#4a3aa7', 'TM02': '#e34948'}
MAX_EDGE = 0.02
OFFSETS = [(10, 16), (-40, -34), (-150, 22), (14, 34), (-120, -22), (12, -18)]  # label offsets, rank order


def main(run, h, w, traces_run=None, out=None, n_label=6):
    run_dir = os.path.join(HERE, 'runs', run)
    g = pd.read_csv(os.path.join(run_dir, 'geometries.csv'))
    p = g['params'].apply(json.loads)
    g = g[(p.apply(lambda d: d.get('h_core')) == h) & (p.apply(lambda d: d.get('w_core')) == w)]
    fp = g.iloc[0]['fingerprint']
    c = pd.read_csv(os.path.join(run_dir, 'crossings.csv'))
    c = c[c['fingerprint'] == fp].copy()
    t = np.load(os.path.join(HERE, 'runs', traces_run or run, 'traces', f'{fp}.npz'), allow_pickle=True)
    lam = t['lambda_sh']
    edge = c['sh_edge_ratio'] if 'sh_edge_ratio' in c else pd.Series(np.nan, index=c.index)
    if 'sh_edge_ratio_screen' in c:
        edge = edge.fillna(c['sh_edge_ratio_screen'])
    c['window_limited'] = edge > MAX_EDGE

    fig, ax = plt.subplots(figsize=(10, 6.4))
    for i, row in enumerate(t['sh_n']):
        ax.plot(lam, row, color='#c9c8bf', linewidth=0.8, zorder=1, label='SH modes (tracked)' if i == 0 else None)
    ax.plot(lam, t['n_guided_cutoff'], '--', color='#7a7971', linewidth=1.2, zorder=2,
            label='guided cutoff (max clad index)')
    for lbl, n in zip(t['pump_labels'], t['pump_n']):
        ax.plot(lam, n, color=PUMP_COLORS.get(str(lbl), '#898781'), linewidth=2.6, zorder=3, label=f'pump {lbl}')
    size = 18 + 26 * np.clip(np.log10(np.clip(c['eta_pct_per_W_cm2'], 1e-3, None)) + 3, 0, 5)
    for status, filled in (('screened', False), ('refined', True)):
        s = c['status'] == status
        for lbl, grp in c[s].groupby('pump_label'):
            col = PUMP_COLORS.get(lbl, '#898781')
            ax.scatter(grp['wavelength_sh'], grp['n_eff_sh'], s=size[grp.index], zorder=5,
                       facecolors=col if filled else 'white', edgecolors=col, linewidths=1.3)
    wl = c[c['window_limited']]
    ax.scatter(wl['wavelength_sh'], wl['n_eff_sh'], s=size[wl.index] + 90, facecolors='none',
               edgecolors='#d1242f', linewidths=1.2, zorder=6)
    top = c[~c['window_limited']].sort_values('eta_pct_per_W_cm2', ascending=False).head(n_label)
    for k, (_, r) in enumerate(top.iterrows()):
        ax.annotate(f"{r['pump_label']}→{r['sh_label']} ({r['eta_pct_per_W_cm2']:.3g})",
                    (r['wavelength_sh'], r['n_eff_sh']), xytext=OFFSETS[k % len(OFFSETS)],
                    textcoords='offset points', fontsize=8, arrowprops=dict(arrowstyle='-', color='#7a7971', lw=0.6))
    # legend proxies for the marker encoding
    ax.scatter([], [], s=60, facecolors='#555', edgecolors='#555', label='crossing, refined (filled)')
    ax.scatter([], [], s=60, facecolors='white', edgecolors='#555', label='crossing, screened only (hollow)')
    ax.scatter([], [], s=120, facecolors='none', edgecolors='#d1242f', label='window/box-mode artifact (ringed)')
    ax.set_xlabel('SH wavelength [nm]   (pump at 2×)')
    ax.set_ylabel('effective index')
    ax.set_title(f"{run}: ridge h={h:g} nm, w={w:g} nm — {len(c)} crossings "
                 f"({(c['status'] == 'refined').sum()} refined, {int(c['window_limited'].sum())} window-limited)\n"
                 "marker size ∝ log NCE; labels give NCE in %/W/cm²", fontsize=10)
    ax.grid(True, color='#e1e0d9', linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False, loc='upper right', ncol=2)
    for s_ in ('top', 'right'):
        ax.spines[s_].set_visible(False)
    fig.tight_layout()
    out = out or os.path.join(run_dir, f'dispersion_h{h:g}_w{w:g}.png')
    fig.savefig(out, dpi=140)
    print('wrote', out, f"({len(c)} crossings; ranked top: {len(top)})")
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    main(a[0], float(a[1]), float(a[2]), a[3] if len(a) > 3 else None, a[4] if len(a) > 4 else None)
