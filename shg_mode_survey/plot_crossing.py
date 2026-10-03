"""Field plots for refined crossings (from their .npz exports): pump |E|, SH Re(Ey) / Re(Ex)
and the nonlinear drive Re(Ey_p^2), with the core outline. No EMode needed.

Usage: python plot_crossing.py <run_name> [max_plots]   -> runs/<run>/plots/*.png
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


def plot_one(row, out_path):
    z = np.load(os.path.join(HERE, row['export_path']))
    x, y, mask = z['x'], z['y'], z['core_mask']
    cy, cx = np.where(mask)
    pad = 450
    xs = (x >= x[cx.min()] - pad) & (x <= x[cx.max()] + pad)
    ys = (y >= y[cy.min()] - pad) & (y <= y[cy.max()] + pad)
    ext = [x[xs][0], x[xs][-1], y[ys][0], y[ys][-1]]

    def crop(a):
        return a[np.ix_(ys, xs)]

    def phase_fix(a):
        k = np.argmax(np.abs(a))
        return np.real(a * np.exp(-1j * np.angle(a.flat[k])))

    sh_dom = 'Ey' if np.sum(np.abs(z['sh_Ey'])**2) >= np.sum(np.abs(z['sh_Ex'])**2) else 'Ex'
    p_dom = 'Ey' if np.sum(np.abs(z['pump_Ey'])**2) >= np.sum(np.abs(z['pump_Ex'])**2) else 'Ex'
    panels = [
        (f"pump {row['pump_label']}  Re({p_dom})", phase_fix(z[f'pump_{p_dom}']), 'RdBu_r'),
        (f"drive Re(Ey_p^2) in core", phase_fix(z['pump_Ey'] ** 2) * mask, 'RdBu_r'),
        (f"SH {row['sh_label']}  Re({sh_dom})", phase_fix(z[f'sh_{sh_dom}']), 'RdBu_r'),
        ("SH |E|", np.sqrt(np.abs(z['sh_Ex'])**2 + np.abs(z['sh_Ey'])**2 + np.abs(z['sh_Ez'])**2), 'magma'),
    ]
    fig, axs = plt.subplots(1, 4, figsize=(16, 4.2))
    for ax, (title, a, cmap) in zip(axs, panels):
        a = crop(a)
        lim = np.abs(a).max() or 1
        ax.imshow(a, origin='lower', extent=ext, cmap=cmap,
                  vmin=(-lim if cmap == 'RdBu_r' else 0), vmax=lim, aspect='equal')
        ax.contour(x[xs], y[ys], crop(mask).astype(float), levels=[0.5], colors='k', linewidths=0.8)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('x [nm]')
    fig.suptitle(f"{row['family']} h={json.loads(row['params'])['h_core']:g} w={json.loads(row['params'])['w_core']:g}\n{row['pump_label']} -> {row['sh_label']} @ "
                 f"{row['wavelength_sh']:.2f} nm   NCE {row['eta_pct_per_W_cm2']:.3g} %/W/cm^2   "
                 f"shape overlap {row['overlap_shape']:.4f}", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def main(run_name, max_plots=20):
    run_dir = os.path.join(HERE, 'runs', run_name)
    d = pd.read_csv(os.path.join(run_dir, 'crossings.csv'))
    d = d[d['status'] == 'refined'].sort_values('eta_pct_per_W_cm2', ascending=False).head(max_plots)
    os.makedirs(os.path.join(run_dir, 'plots'), exist_ok=True)
    for _, row in d.iterrows():
        name = os.path.splitext(os.path.basename(row['export_path']))[0]
        out = os.path.join(run_dir, 'plots', f"{name}_{row['pump_label']}_{row['sh_label']}.png")
        plot_one(row, out)
        print(out)


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20)
