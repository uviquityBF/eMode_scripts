"""Plot loss vs. waveguide width from sweep_loss_vs_dimensions.py's output: sidewall
scattering loss (Payne-Lacey, calibrated), total loss (scattering + post-processed absorption),
and a per-physical-mechanism breakdown of the absorption contributions -- all computed from the
exported mode profiles with no further EMode calls.

Every loss-contributor assumption (absorption MECHANISMS, sidewall sigma/Lc, n_core/n_clad,
calibration_factor) is bundled into one `assumptions` dict (see default_assumptions()) that gets
threaded through every function here, rather than being fixed module constants -- so a caller
(e.g. the notebook's "live update" section) can build its own dict with live-edited values and
pass it straight through to these same plotting functions.
"""

import csv
import os

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 -- registers projection='3d'

import absorption_model as am
import scattering_model as scm
from sweep_loss_vs_dimensions import RESULTS_CSV, EQ_O, WAVELENGTH_PUMP, ROUGHNESS_RMS, CORRELATION_LENGTH

# --- Absorption mechanisms (edit and re-run -- no EMode calls needed) ---------------------
# Each: 'localization' is 'interface' (varies with height above the core/substrate interface)
# or 'sidewall' (varies with lateral distance from the nearest sidewall); 'shape' is 'step' or
# 'exp'; 'alpha0' [dB/m] is the LOCAL absorption coefficient right at the interface/sidewall;
# 'L' [nm] is the characteristic penetration depth. Values below are illustrative placeholders,
# not derived from any measurement -- replace with your own best estimates per mechanism.
MECHANISMS = [
    {'name': 'Dislocations (growth interface)', 'localization': 'interface',
     'shape': 'exp', 'alpha0': 3.0e4, 'L': 60.0},
    {'name': 'C impurities (growth interface)', 'localization': 'interface',
     'shape': 'exp', 'alpha0': 1.5e4, 'L': 40.0},
    {'name': 'Si impurities (growth interface)', 'localization': 'interface',
     'shape': 'exp', 'alpha0': 1.0e4, 'L': 40.0},
    {'name': 'O impurities (growth interface)', 'localization': 'interface',
     'shape': 'exp', 'alpha0': 2.0e4, 'L': 50.0},
    {'name': 'Oxidation ingress (sidewall)', 'localization': 'sidewall',
     'shape': 'exp', 'alpha0': 2.5e4, 'L': 50.0},
    {'name': 'Sidewall contamination (Si)', 'localization': 'sidewall',
     'shape': 'step', 'alpha0': 1.5e4, 'L': 30.0},
    {'name': 'Sidewall damage', 'localization': 'sidewall',
     'shape': 'exp', 'alpha0': 5.0e4, 'L': 75.0},
]

# Fixed categorical order (dataviz skill palette, light mode, 8-slot order -- validated for the
# "lines" chart form at full length) -- color follows mechanism identity, never rank, so this
# order/assignment stays the same across every height subplot.
MECHANISM_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7']


def height_colors(n):
    """n colors along a single-hue sequential blue ramp (dataviz skill: height is an ORDERED
    quantity, not a fixed set of independent categories like the mechanisms -- a sequential
    ramp that scales to any n avoids the old fixed 3-color list silently cycling/reusing colors
    once a sweep grows past 3 heights, which made the legend ambiguous).
    """
    if n == 1:
        return ['#2a78d6']
    return [plt.cm.Blues(x) for x in np.linspace(0.4, 0.9, n)]


GRID_COLOR = '#e1e0d9'
AXIS_COLOR = '#c3c2b7'
MUTED_TEXT = '#898781'
PRIMARY_TEXT = '#0b0b0b'


def default_assumptions():
    """Standalone-script defaults -- n_core/sigma/Lc match what was actually fed to EMode for
    the sweep, but calibration_factor=1.0 is a placeholder (NOT a real calibration). For real
    numbers, load calibrate_scattering.py's fitted values instead:

        import calibrate_scattering as cs
        calibration = cs.load_calibration()
        assumptions = plv.default_assumptions()
        assumptions.update(n_core=calibration['n_core'], n_clad=calibration['n_clad'],
                            calibration_factor=calibration['calibration_factor'])
    """
    return {
        'mechanisms': MECHANISMS,
        'n_core': scm.sellmeier_n(EQ_O, WAVELENGTH_PUMP),
        'n_clad': 1.47,
        'n_substrate': scm.N_SUBSTRATE_DEFAULT,
        'sigma_sidewall': ROUGHNESS_RMS[0],
        'Lc_sidewall': CORRELATION_LENGTH[0],
        'sigma_horizontal': ROUGHNESS_RMS[1],
        'Lc_horizontal': CORRELATION_LENGTH[1],
        'calibration_factor': 1.0,
        'calibration_factor_horizontal': 1.0,
    }


def load_results(csv_path, roughness_filter='latest'):
    """Load every 'ok' row from a sweep's results CSV.

    The pipeline is designed around ONE roughness_rms/correlation_length setting per results
    file (see sweep_loss_vs_dimensions.py's checkpoint docs) -- but nothing stops you from
    changing those constants and re-running into the SAME file, which appends a second set of
    rows (possibly for the same (h, w) points) logged under the new setting. This is harmless
    for scattering_loss_for_row()/mechanism_losses_for_row() (they use the live `assumptions`
    dict, not each row's own logged roughness columns, and the exported mode profile itself
    doesn't depend on roughness at all -- EMode's roughness_rms/correlation_length only feed the
    separate, perturbative em.scattering() call AFTER FDM solves the nominal smooth-boundary
    mode). It DOES matter for anything reading scattering_loss_dB_per_m/
    scattering_vertical_dB_per_m/scattering_horizontal_dB_per_m directly (EMode's own native
    values, which genuinely depend on roughness) -- e.g. plotting those alongside width would
    silently zigzag if two different roughness settings' rows for the same (h, w) got mixed in.

    `roughness_filter`:
      - 'latest' (default): if more than one distinct (roughness_rms, correlation_length) pair
        is present, warn loudly and keep only the rows logged under the MOST RECENTLY-WRITTEN
        one (CSV rows are append-only, so this is simply the last distinct pair encountered).
      - 'all': disable filtering, return every row regardless of roughness (old behavior).
      - an explicit (roughness_rms_json, correlation_length_json) tuple, matching the exact JSON
        strings as logged (e.g. ('[2.0, 0.3]', '[50.0, 10.0]')) -- keep only rows matching that
        specific historical setting.
    """
    rows = []
    with open(csv_path, newline='') as f:
        for row in csv.DictReader(f):
            if row['status'] == 'ok':
                row['h_core'] = float(row['h_core'])
                row['w_core'] = float(row['w_core'])
                row['n_eff'] = float(row['n_eff'])
                row['scattering_loss_dB_per_m'] = float(row['scattering_loss_dB_per_m'])
                row['scattering_vertical_dB_per_m'] = float(row['scattering_vertical_dB_per_m'])
                row['scattering_horizontal_dB_per_m'] = float(row['scattering_horizontal_dB_per_m'])
                rows.append(row)

    distinct = list(dict.fromkeys((r['roughness_rms'], r['correlation_length']) for r in rows))
    if len(distinct) > 1:
        print(f"WARNING: {csv_path} has {len(distinct)} distinct roughness/correlation "
              f"settings mixed together:")
        for rc in distinct:
            n = sum(1 for r in rows if (r['roughness_rms'], r['correlation_length']) == rc)
            print(f"    roughness_rms={rc[0]}, correlation_length={rc[1]}: {n} row(s)")

    if roughness_filter == 'all' or len(distinct) <= 1:
        return rows
    target = distinct[-1] if roughness_filter == 'latest' else roughness_filter
    print(f"    -> keeping only roughness_rms={target[0]}, correlation_length={target[1]} "
          f"(roughness_filter={roughness_filter!r}; pass 'all' to disable this filtering)")
    return [r for r in rows if (r['roughness_rms'], r['correlation_length']) == target]


def mechanism_losses_for_row(row, mechanisms):
    """{mechanism_name: loss_dB_per_m} for one results row, independent per mechanism."""
    data = np.load(row['export_path'])
    return am.compute_mechanism_losses(
        data['core_mask'], dx=float(data['x'][1] - data['x'][0]), y=data['y'], Sz=data['Sz'],
        mechanisms=mechanisms)


def scattering_loss_for_row(row, n_core, n_clad, sigma_sidewall, Lc_sidewall, calibration_factor):
    """Payne-Lacey (calibrated) SIDEWALL-ONLY (vertical-edge) scattering loss [dB/m] for one
    results row, using the row's own exported mode profile but LIVE sigma/Lc/n_core/n_clad/
    calibration_factor -- these don't have to match whatever roughness_rms/correlation_length
    were actually fed to EMode for this row, since only the mode profile itself (fixed at solve
    time) comes from that. Kept separate from total_scattering_loss_for_row (vertical +
    horizontal) specifically for the apples-to-apples vertical-only EMode comparison in Section 7.
    """
    data = np.load(row['export_path'])
    return scm.compute_scattering_loss(data, n_core, n_clad, sigma_sidewall, Lc_sidewall,
                                        calibration_factor=calibration_factor)


def total_scattering_loss_for_row(row, assumptions):
    """Payne-Lacey (calibrated) TOTAL scattering loss [dB/m] -- sidewall (vertical) + top/bottom
    (horizontal), each with its own live sigma/Lc/calibration_factor from `assumptions`. See
    scattering_model.py's module docstring for the horizontal term's caveats -- in particular,
    its per-point fit quality is noticeably worse than the vertical term's for tall/narrow cores
    (see calibrate_scattering.py's report), so treat "total scatter" results with more caution
    than sidewall-only ones until that's investigated further.
    """
    data = np.load(row['export_path'])
    return scm.compute_total_scattering_loss(
        data, assumptions['n_core'], assumptions['n_clad'], assumptions['n_substrate'],
        assumptions['sigma_sidewall'], assumptions['Lc_sidewall'],
        assumptions['sigma_horizontal'], assumptions['Lc_horizontal'],
        calibration_factor_vertical=assumptions['calibration_factor'],
        calibration_factor_horizontal=assumptions['calibration_factor_horizontal'])


def absorption_total_for_row(row, mechanisms):
    """Sum of every mechanism's contribution -- total absorption loss [dB/m] for one row."""
    return sum(mechanism_losses_for_row(row, mechanisms).values())


def total_loss_dB_per_m(row, assumptions):
    scattering = total_scattering_loss_for_row(row, assumptions)
    absorption = absorption_total_for_row(row, assumptions['mechanisms'])
    return scattering + absorption


def style_axis(ax, ylabel):
    ax.set_xlabel('Core width w [nm]', color=PRIMARY_TEXT)
    ax.set_ylabel(ylabel, color=PRIMARY_TEXT)
    ax.grid(True, color=GRID_COLOR, linewidth=1)
    ax.set_axisbelow(True)
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    for spine in ('left', 'bottom'):
        ax.spines[spine].set_color(AXIS_COLOR)
    ax.tick_params(colors=MUTED_TEXT)


def plot_totals(rows, heights, assumptions, log_scale=False):
    """Three panels: total scattering (vertical + horizontal, Payne-Lacey calibrated), total
    absorption (sum of all mechanisms), and total loss (their sum) -- all vs. core width, one
    line per height. `log_scale=True` log-scales both axes on all three panels -- useful since
    loss vs. width often looks closer to a power law than a simple exponential/polynomial decay,
    which shows up as straight-line-ish behavior on log-log axes that's hard to judge on linear
    ones.

    NOTE: the horizontal-scattering term feeding the scattering/total panels has a noticeably
    worse fit against EMode for tall/narrow cores than the sidewall term does (see
    calibrate_scattering.py's per-point report) -- treat those panels with more caution than a
    sidewall-only view for that geometry range until investigated further.
    """
    fig, (ax_scat, ax_abs, ax_total) = plt.subplots(1, 3, figsize=(16, 4.5), facecolor='#fcfcfb')
    for ax in (ax_scat, ax_abs, ax_total):
        ax.set_facecolor('#fcfcfb')

    colors = height_colors(len(heights))
    for i, h in enumerate(heights):
        color = colors[i]
        h_rows = sorted((r for r in rows if r['h_core'] == h), key=lambda r: r['w_core'])
        widths = [r['w_core'] for r in h_rows]
        scat_dB_cm = [total_scattering_loss_for_row(r, assumptions) / 100 for r in h_rows]
        abs_dB_cm = [absorption_total_for_row(r, assumptions['mechanisms']) / 100 for r in h_rows]
        total_dB_cm = [s + a for s, a in zip(scat_dB_cm, abs_dB_cm)]

        ax_scat.plot(widths, scat_dB_cm, '-o', color=color, linewidth=2, markersize=6,
                     label=f'h={h:.0f} nm')
        ax_abs.plot(widths, abs_dB_cm, '-o', color=color, linewidth=2, markersize=6,
                    label=f'h={h:.0f} nm')
        ax_total.plot(widths, total_dB_cm, '-o', color=color, linewidth=2, markersize=6,
                      label=f'h={h:.0f} nm')

    ax_scat.set_title('Total scattering (Payne-Lacey, calibrated)', color=PRIMARY_TEXT,
                       fontsize=11)
    ax_abs.set_title('Total absorption (all mechanisms)', color=PRIMARY_TEXT, fontsize=11)
    ax_total.set_title('Total loss (scattering + absorption)', color=PRIMARY_TEXT, fontsize=11)
    for ax in (ax_scat, ax_abs, ax_total):
        style_axis(ax, 'Loss [dB/cm]')
        ax.legend(frameon=False, labelcolor=PRIMARY_TEXT)

    if log_scale:
        for ax in (ax_scat, ax_abs, ax_total):
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.grid(True, which='minor', color=GRID_COLOR, linewidth=0.5, alpha=0.5)

    suptitle = 'Fundamental TM00 loss vs. core width'
    if log_scale:
        suptitle += ' (log-log)'
    fig.suptitle(suptitle, color=PRIMARY_TEXT, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def plot_mechanism_breakdown(rows, heights, assumptions):
    """One subplot per height, each showing every mechanism's absorption loss vs. width --
    small multiples, one shared legend, consistent mechanism->color mapping across panels.
    """
    mechanisms = assumptions['mechanisms']
    fig, axes = plt.subplots(1, len(heights), figsize=(5 * len(heights), 5.8),
                              facecolor='#fcfcfb', sharey=True, squeeze=False)
    axes = axes[0]

    for ax, h in zip(axes, heights):
        ax.set_facecolor('#fcfcfb')
        h_rows = sorted((r for r in rows if r['h_core'] == h), key=lambda r: r['w_core'])
        widths = [r['w_core'] for r in h_rows]
        per_row_losses = [mechanism_losses_for_row(r, mechanisms) for r in h_rows]

        for i, mechanism in enumerate(mechanisms):
            name = mechanism['name']
            color = MECHANISM_COLORS[i % len(MECHANISM_COLORS)]
            loss_dB_cm = [losses[name] / 100 for losses in per_row_losses]
            ax.plot(widths, loss_dB_cm, '-o', color=color, linewidth=2, markersize=5, label=name)

        ax.set_title(f'h = {h:.0f} nm', color=PRIMARY_TEXT, fontsize=11)
        style_axis(ax, 'Absorption loss [dB/cm]')

    fig.suptitle('Absorption loss by physical mechanism vs. core width', color=PRIMARY_TEXT,
                 fontsize=13)
    fig.tight_layout(rect=(0, 0.22, 1, 0.93))

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=min(len(mechanisms), 3),
               frameon=False, labelcolor=PRIMARY_TEXT, bbox_to_anchor=(0.5, 0.0))
    return fig


def loss_grid(rows, assumptions, quantity='total'):
    """(heights, widths, Z) arrays for plot_loss_surface -- Z[i, j] is the loss [dB/cm] at
    (heights[i], widths[j]), NaN for any (h, w) combination missing from `rows` (e.g. a failed
    sweep point) so the surface just shows a gap there rather than crashing.

    `quantity`: 'total' (scattering + all mechanisms), 'scattering' (total scattering, vertical +
    horizontal), 'scattering_vertical' (sidewall only), 'absorption' (sum of all mechanisms), or
    a mechanism name from assumptions['mechanisms'] (that mechanism's contribution alone).
    """
    heights = sorted(set(r['h_core'] for r in rows))
    widths = sorted(set(r['w_core'] for r in rows))
    lookup = {(r['h_core'], r['w_core']): r for r in rows}

    Z = np.full((len(heights), len(widths)), np.nan)
    for i, h in enumerate(heights):
        for j, w in enumerate(widths):
            r = lookup.get((h, w))
            if r is None:
                continue
            if quantity == 'total':
                value = total_loss_dB_per_m(r, assumptions)
            elif quantity == 'scattering':
                value = total_scattering_loss_for_row(r, assumptions)
            elif quantity == 'scattering_vertical':
                value = scattering_loss_for_row(
                    r, assumptions['n_core'], assumptions['n_clad'],
                    assumptions['sigma_sidewall'], assumptions['Lc_sidewall'],
                    assumptions['calibration_factor'])
            elif quantity == 'absorption':
                value = absorption_total_for_row(r, assumptions['mechanisms'])
            else:
                value = mechanism_losses_for_row(r, assumptions['mechanisms'])[quantity]
            Z[i, j] = value / 100  # dB/cm
    return np.array(heights), np.array(widths), Z


def plot_loss_surface(rows, assumptions, quantity='total'):
    """3D surface of loss [dB/cm] vs. (h, w) -- plotted directly off the sweep's regular grid,
    no curve/surface fitting (unlike the phase-matching pipeline's Hermite fit, which combines
    VALUE + LOCAL GRADIENT data specifically because ITS points are sampled irregularly; this
    sweep is on a regular height x width grid with no gradient data available, so a raw gridded
    surface is both simpler and sufficient here). Needs >=2 distinct heights and >=2 distinct
    widths in `rows` -- returns None (printing why) otherwise.
    """
    heights, widths, Z = loss_grid(rows, assumptions, quantity)
    if len(heights) < 2 or len(widths) < 2:
        print(f"Need >=2 distinct heights and widths for a surface (have {len(heights)} "
              f"height(s), {len(widths)} width(s)) -- skipping.")
        return None

    W, H = np.meshgrid(widths, heights)
    fig = plt.figure(figsize=(7.5, 6), facecolor='#fcfcfb')
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(W, H, Z, cmap='Blues', edgecolor='#0b0b0b22', linewidth=0.3)
    ax.set_xlabel('Core width w [nm]', color=PRIMARY_TEXT)
    ax.set_ylabel('Core height h [nm]', color=PRIMARY_TEXT)
    ax.set_zlabel('Loss [dB/cm]', color=PRIMARY_TEXT)
    title = {'total': 'Total loss', 'scattering': 'Total scattering (Payne-Lacey)',
             'scattering_vertical': 'Sidewall scattering (Payne-Lacey)',
             'absorption': 'Total absorption'}.get(quantity, quantity)
    ax.set_title(f'{title} vs. core (h, w)', color=PRIMARY_TEXT, fontsize=12)
    fig.tight_layout()
    return fig


def main(assumptions=None):
    assumptions = assumptions or default_assumptions()
    rows = load_results(RESULTS_CSV)
    if not rows:
        print(f"No completed points in {RESULTS_CSV} yet -- run sweep_loss_vs_dimensions.py first.")
        return
    heights = sorted(set(r['h_core'] for r in rows))

    fig_totals = plot_totals(rows, heights, assumptions)
    fig_totals.savefig('loss_vs_dimensions.png', dpi=150, facecolor=fig_totals.get_facecolor())
    print("Saved loss_vs_dimensions.png")

    fig_totals_log = plot_totals(rows, heights, assumptions, log_scale=True)
    fig_totals_log.savefig('loss_vs_dimensions_loglog.png', dpi=150,
                            facecolor=fig_totals_log.get_facecolor())
    print("Saved loss_vs_dimensions_loglog.png")

    fig_breakdown = plot_mechanism_breakdown(rows, heights, assumptions)
    fig_breakdown.savefig('loss_by_mechanism.png', dpi=150, facecolor=fig_breakdown.get_facecolor())
    print("Saved loss_by_mechanism.png")

    plt.show()


if __name__ == '__main__':
    main()
