"""Post-hoc TM00 mode-identity check for every point in field_exports/ -- no EMode calls, works
on ANY exported point (including ones solved before sweep_loss_vs_dimensions.py's live
TE_fraction warning existed, since that value was only ever printed, never saved).

For each h{h}_w{w}.npz: plots |Ex|, |Ey|, |Ez| (with the core outline overlaid) to
field_profile_plots/h{h}_w{w}.png, so you can flip through and visually confirm TM00 character,
and prints/reports a quick numeric proxy alongside each plot.

CAVEAT: this proxy is NOT guaranteed to exactly reproduce EMode's own TE_fraction (computed
internally by FDM() from the full mode solution -- possibly using the H-field structure, which
isn't exported here) -- it's the standard quasi-TE/quasi-TM classification heuristic used in
integrated photonics: the fraction of total E-field energy in the in-plane (Ex, "TE-like") vs.
vertical (Ey, "TM-like") component. Treat it as a strongly-correlated cross-check, not a
guaranteed match to EMode's number -- the field plots are the more trustworthy verification.
"""

import glob
import os

import numpy as np
import matplotlib.pyplot as plt

FIELD_EXPORTS_DIR = 'field_exports'
OUTPUT_DIR = 'field_profile_plots'
TE_LIKE_WARN_THRESHOLD = 0.1  # matches sweep_loss_vs_dimensions.TE_FRACTION_WARN_THRESHOLD

GRID_COLOR = '#e1e0d9'
CORE_OUTLINE = '#eb6834'
PRIMARY_TEXT = '#0b0b0b'
FLAG_TEXT = '#d03b3b'


def te_like_energy_fractions(Ex, Ey, Ez):
    """(frac_x, frac_y, frac_z): each component's share of total |E|^2 energy. For this
    pipeline's TM-boundary-condition convention, TM-like modes are Ey-dominant (vertical);
    TE-like modes are Ex-dominant (in-plane/horizontal) -- see module docstring.
    """
    energy_x = float(np.sum(np.abs(Ex) ** 2))
    energy_y = float(np.sum(np.abs(Ey) ** 2))
    energy_z = float(np.sum(np.abs(Ez) ** 2))
    total = energy_x + energy_y + energy_z
    return energy_x / total, energy_y / total, energy_z / total


def plot_one(npz_path, out_dir):
    data = np.load(npz_path)
    x, y = data['x'], data['y']
    Ex, Ey, Ez = data['Ex'], data['Ey'], data['Ez']
    core_mask = data['core_mask']
    h_core, w_core = float(data['h_core']), float(data['w_core'])
    n_eff = float(data['n_eff']) if 'n_eff' in data else None

    frac_x, frac_y, frac_z = te_like_energy_fractions(Ex, Ey, Ez)
    flagged = frac_x > TE_LIKE_WARN_THRESHOLD

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), facecolor='#fcfcfb')
    fields = {'Ex': (Ex, frac_x), 'Ey': (Ey, frac_y), 'Ez': (Ez, frac_z)}
    for ax, name in zip(axes, ('Ex', 'Ey', 'Ez')):
        field, frac = fields[name]
        ax.set_facecolor('#fcfcfb')
        ax.pcolormesh(x, y, np.abs(field), shading='auto', cmap='Blues')
        ax.contour(x, y, core_mask.astype(float), levels=[0.5], colors=CORE_OUTLINE,
                   linewidths=1.3)
        ax.set_title(f"|{name}|  (energy frac={frac * 100:.1f}%)", fontsize=10.5,
                     color=PRIMARY_TEXT)
        ax.set_aspect('equal')
        ax.set_xlabel('x [nm]', color=PRIMARY_TEXT)
    axes[0].set_ylabel('y [nm]', color=PRIMARY_TEXT)

    tag = '  <-- CHECK: TE-like energy fraction is high' if flagged else ''
    title = f"h={h_core:.0f} nm, w={w_core:.0f} nm"
    if n_eff is not None:
        title += f", n_eff={n_eff:.4f}"
    title += f" -- Ex={frac_x * 100:.1f}%, Ey={frac_y * 100:.1f}%, Ez={frac_z * 100:.1f}%{tag}"
    fig.suptitle(title, fontsize=11, color=(FLAG_TEXT if flagged else PRIMARY_TEXT))
    fig.tight_layout(rect=(0, 0, 1, 0.90))

    name = os.path.splitext(os.path.basename(npz_path))[0]
    out_path = os.path.join(out_dir, f"{name}.png")
    fig.savefig(out_path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    return {'h_core': h_core, 'w_core': w_core, 'frac_x': frac_x, 'frac_y': frac_y,
            'frac_z': frac_z, 'flagged': flagged, 'path': out_path}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    npz_files = sorted(glob.glob(os.path.join(FIELD_EXPORTS_DIR, '*.npz')))
    print(f"Found {len(npz_files)} exported point(s) in {FIELD_EXPORTS_DIR}/")

    results = []
    for path in npz_files:
        try:
            r = plot_one(path, OUTPUT_DIR)
            results.append(r)
            flag = '  <-- FLAGGED' if r['flagged'] else ''
            print(f"  h={r['h_core']:>5.0f} w={r['w_core']:>5.0f}: "
                  f"Ex={r['frac_x'] * 100:5.1f}%  Ey={r['frac_y'] * 100:5.1f}%  "
                  f"Ez={r['frac_z'] * 100:5.1f}%{flag}")
        except Exception as e:
            print(f"  FAILED on {path}: {e!r}")

    flagged = [r for r in results if r['flagged']]
    print(f"\n{len(results)} plotted to {OUTPUT_DIR}/, {len(flagged)} flagged "
          f"(TE-like energy fraction > {TE_LIKE_WARN_THRESHOLD * 100:.0f}%)")
    if flagged:
        print("Flagged points (check these plots first):")
        for r in flagged:
            print(f"  h={r['h_core']:.0f} w={r['w_core']:.0f}: {r['path']}")
    return results


if __name__ == '__main__':
    main()
