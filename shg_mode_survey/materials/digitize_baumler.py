"""Digitize n(E) and k(E) for wurtzite Al(1-x)Sc(x)N from Baumler et al., J. Appl. Phys. 126,
045715 (2019), Fig. (a) n and (b) k, x = 0 ... 0.41 (Baumler2019_Fig_nk.jpg, 700x310 px).

Method: axis calibration from tick pixels (measured once, constants below), then per column the
median row of pixels matching each curve's legend colour (nearest-colour classification with a
distance cut), linear interpolation over dash gaps / occlusions, resampled on a 0.02 eV grid.
Accuracy is limited by the small source image: ~1 px = 0.021 eV in E, 0.006 in n, 0.008 in k,
plus overlap where curves coincide (k ~ 0 below ~4 eV; all curves overlap there, so the low-E k
is effectively 'below ~0.01' and is set to 0 below 3.5 eV). Writes ScAlN_Baumler2019_nk_digitized.csv and an overlay PNG.
"""

import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
X = [0.00, 0.06, 0.09, 0.14, 0.17, 0.23, 0.32, 0.41]
COLORS = np.array([(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255),
                   (255, 0, 255), (128, 128, 0), (0, 0, 128)])
# calibration (pixels): energy = 1 eV + (col - c1) / px_per_eV ; panel b is panel a shifted
PANELS = {
    'n': {'cols': (48, 340), 'rows': (44, 267), 'c1': 71.0, 'px_eV': 47.1,
          'row0': 251.0, 'val0': 2.0, 'px_per_unit': 173.0},
    'k': {'cols': (405, 697), 'rows': (44, 267), 'c1': 427.5, 'px_eV': 47.1,
          'row0': 243.0, 'val0': 0.0, 'px_per_unit': 125.3},
}
K_ZERO_BELOW_EV = 3.5
LEGEND_BOX = {'n': (55, 185, 48, 175), 'k': (55, 195, 405, 535)}  # (row0, row1, col0, col1): legends excluded


def extract(im, panel):
    p = PANELS[panel]
    c0, c1 = p['cols']
    r0, r1 = p['rows']
    sub = im[r0:r1, c0:c1].astype(float)
    d = np.linalg.norm(sub[:, :, None, :] - COLORS[None, None, :, :], axis=3)  # (ny, nx, 8)
    best = np.argmin(d, axis=2)
    ok = d.min(axis=2) < 70
    if panel in LEGEND_BOX:
        a0, a1, b0, b1 = LEGEND_BOX[panel]
        ok[max(a0 - r0, 0):a1 - r0, max(b0 - c0, 0):b1 - c0] = False
    E = 1.0 + (np.arange(c0, c1) - p['c1']) / p['px_eV']
    curves = {}
    for i, x in enumerate(X):
        rows = np.full(c1 - c0, np.nan)
        for j in range(c1 - c0):
            hit = np.where(ok[:, j] & (best[:, j] == i))[0]
            if hit.size:
                rows[j] = np.median(hit) + r0
        good = ~np.isnan(rows)
        vals = p['val0'] + (p['row0'] - rows) / p['px_per_unit']
        curves[x] = (E[good], vals[good])
    return curves


def main():
    im = np.asarray(Image.open(os.path.join(HERE, 'Baumler2019_Fig_nk.jpg')).convert('RGB')).astype(int)
    grid = np.round(np.arange(0.6, 6.62, 0.02), 3)
    out = {'E_eV': grid, 'wavelength_nm': 1239.84193 / grid}
    raw = {}
    for panel in ('n', 'k'):
        raw[panel] = extract(im, panel)
        for x, (E, v) in raw[panel].items():
            col = np.interp(grid, E, v, left=np.nan, right=np.nan)
            if panel == 'k':
                # Below K_ZERO_BELOW_EV every curve lies on k = 0 in the figure (and overlapping
                # curves / the black frame make pixel picks there meaningless): set 0, then fill
                # occlusion gaps above it by linear interpolation along E.
                col = np.where(grid < K_ZERO_BELOW_EV, 0.0, np.clip(col, 0, None))
                good = ~np.isnan(col)
                col = np.interp(grid, grid[good], col[good])
            out[f'{panel}_x{x:.2f}'] = col
    header = list(out)
    data = np.column_stack([out[h] for h in header])
    np.savetxt(os.path.join(HERE, 'ScAlN_Baumler2019_nk_digitized.csv'), data, delimiter=',',
               header=','.join(header), comments='', fmt='%.5g')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(14, 6.2))
    for ax, panel in zip(axs, ('n', 'k')):
        ax.imshow(im, origin='upper')
        p = PANELS[panel]
        for (x, (E, v)), c in zip(raw[panel].items(), COLORS):
            cols = p['c1'] + (E - 1.0) * p['px_eV']
            rows = p['row0'] - (v - p['val0']) * p['px_per_unit']
            ax.plot(cols, rows, '.', ms=1.2, color='#e34948' if x == 0 else '#1baf7a')
        ax.set_xlim(*(np.array(p['cols']) + [-10, 10]))
        ax.set_ylim(275, 35)
        ax.set_title(f'panel {panel}: digitized points (red: x=0, green: others) over source')
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'ScAlN_Baumler2019_digitized_overlay.png'), dpi=110)
    print('wrote CSV + overlay')


if __name__ == '__main__':
    main()
