"""Cross-section plots of every geometry in a run, straight from geometry.py's own mask
functions (no EMode needed -- pure numpy/matplotlib, so this works even if EMode is busy/down).

Usage: python plot_geometry.py <run_name>   -> runs/<run>/summary/geometry/<fingerprint>.png
"""

import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.colors  # noqa: E402
import matplotlib.patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geometry as geo  # noqa: E402

# Material -> color, fixed assignment (dataviz skill default categorical palette, slots chosen to
# keep spatially-adjacent layers (Substrate/film-or-core/strip/TopClad) off the one flagged
# adjacent pair (slot 2 orange next to slot 4 yellow) -- not used here at all.
REGION_COLOR = {'Substrate': '#2a78d6', 'core': '#eb6834', 'film': '#eb6834',
                'strip': '#4a3aa7', 'TopClad': '#1baf7a'}
RESOLUTION_NM = 5.0
MARGIN_X_NM = 500.0
MARGIN_Y_TOP_NM = 600.0


def plot_one(geom, title, out_path):
    x0, x1, y0, y1 = geom.bbox()
    half_w = geom.window_width / 2
    x = np.arange(max(-half_w, x0 - MARGIN_X_NM), min(half_w, x1 + MARGIN_X_NM), RESOLUTION_NM)
    y = np.arange(0.0, y1 + MARGIN_Y_TOP_NM, RESOLUTION_NM)
    regions = geom.region_masks(x, y)

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    handles = []
    for name, (mask, material) in regions.items():
        if not mask.any():
            continue
        color = REGION_COLOR.get(name, '#898781')
        rgba = np.zeros((*mask.shape, 4))
        rgba[mask] = matplotlib.colors.to_rgba(color)
        ax.imshow(rgba, origin='lower', extent=[x[0], x[-1], y[0], y[-1]], aspect='equal')
        handles.append(matplotlib.patches.Patch(color=color, label=f"{name} ({material})"))
    ax.set_xlabel('x [nm]')
    ax.set_ylabel('y [nm]')
    ax.set_title(title, fontsize=10)
    ax.legend(handles=handles, loc='upper right', fontsize=8, framealpha=0.9)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def main(run_name):
    run_dir = os.path.join(HERE, 'runs', run_name)
    g = pd.read_csv(os.path.join(run_dir, 'geometries.csv'))
    out_dir = os.path.join(run_dir, 'summary', 'geometry')
    os.makedirs(out_dir, exist_ok=True)
    for _, row in g[g['status'] == 'ok'].iterrows():
        geom = geo.make_geometry(row['family'], json.loads(row['params']))
        out = os.path.join(out_dir, f"{row['fingerprint']}.png")
        plot_one(geom, f"{geom.describe()}  ({row['fingerprint']})", out)
        print(out)


if __name__ == '__main__':
    main(sys.argv[1])
