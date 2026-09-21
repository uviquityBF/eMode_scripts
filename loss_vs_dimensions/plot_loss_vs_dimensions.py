"""Plot loss vs. waveguide width from sweep_loss_vs_dimensions.py's output: sidewall
scattering loss (native EMode), total loss (scattering + post-processed absorption), and a
per-physical-mechanism breakdown of the absorption contributions -- all re-computable here with
no further EMode calls. Edit MECHANISMS below and re-run this script freely to explore
assumptions; your exported sweep data doesn't need to be regenerated.
"""

import csv
import os

import numpy as np
import matplotlib.pyplot as plt

import absorption_model as am
from sweep_loss_vs_dimensions import RESULTS_CSV

# --- Absorption mechanisms to apply (edit and re-run -- no EMode calls needed) -------------
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
HEIGHT_COLORS = MECHANISM_COLORS[:3]  # totals plot only ever needs a few heights
GRID_COLOR = '#e1e0d9'
AXIS_COLOR = '#c3c2b7'
MUTED_TEXT = '#898781'
PRIMARY_TEXT = '#0b0b0b'


def load_results(csv_path):
    rows = []
    with open(csv_path, newline='') as f:
        for row in csv.DictReader(f):
            if row['status'] == 'ok':
                row['h_core'] = float(row['h_core'])
                row['w_core'] = float(row['w_core'])
                row['n_eff'] = float(row['n_eff'])
                row['scattering_loss_dB_per_m'] = float(row['scattering_loss_dB_per_m'])
                rows.append(row)
    return rows


def mechanism_losses_for_row(row):
    """{mechanism_name: loss_dB_per_m} for one results row, independent per mechanism."""
    data = np.load(row['export_path'])
    return am.compute_mechanism_losses(
        data['core_mask'], dx=float(data['x'][1] - data['x'][0]), y=data['y'], Sz=data['Sz'],
        mechanisms=MECHANISMS)


def total_loss_dB_per_m(row):
    return row['scattering_loss_dB_per_m'] + sum(mechanism_losses_for_row(row).values())


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


def plot_totals(rows, heights):
    fig, (ax_scat, ax_total) = plt.subplots(1, 2, figsize=(11, 4.5), facecolor='#fcfcfb')
    for ax in (ax_scat, ax_total):
        ax.set_facecolor('#fcfcfb')

    for i, h in enumerate(heights):
        color = HEIGHT_COLORS[i % len(HEIGHT_COLORS)]
        h_rows = sorted((r for r in rows if r['h_core'] == h), key=lambda r: r['w_core'])
        widths = [r['w_core'] for r in h_rows]
        scat_dB_cm = [r['scattering_loss_dB_per_m'] / 100 for r in h_rows]
        total_dB_cm = [total_loss_dB_per_m(r) / 100 for r in h_rows]

        ax_scat.plot(widths, scat_dB_cm, '-o', color=color, linewidth=2, markersize=6,
                     label=f'h={h:.0f} nm')
        ax_total.plot(widths, total_dB_cm, '-o', color=color, linewidth=2, markersize=6,
                      label=f'h={h:.0f} nm')

    ax_scat.set_title('Sidewall scattering loss (native EMode)', color=PRIMARY_TEXT, fontsize=11)
    ax_total.set_title('Total loss (scattering + absorption)', color=PRIMARY_TEXT, fontsize=11)
    style_axis(ax_scat, 'Loss [dB/cm]')
    style_axis(ax_total, 'Loss [dB/cm]')
    ax_scat.legend(frameon=False, labelcolor=PRIMARY_TEXT)
    ax_total.legend(frameon=False, labelcolor=PRIMARY_TEXT)

    fig.suptitle('Fundamental TM00 loss vs. core width', color=PRIMARY_TEXT, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def plot_mechanism_breakdown(rows, heights):
    """One subplot per height, each showing every mechanism's absorption loss vs. width --
    small multiples, one shared legend, consistent mechanism->color mapping across panels.
    """
    fig, axes = plt.subplots(1, len(heights), figsize=(5 * len(heights), 5.8),
                              facecolor='#fcfcfb', sharey=True, squeeze=False)
    axes = axes[0]

    for ax, h in zip(axes, heights):
        ax.set_facecolor('#fcfcfb')
        h_rows = sorted((r for r in rows if r['h_core'] == h), key=lambda r: r['w_core'])
        widths = [r['w_core'] for r in h_rows]
        per_row_losses = [mechanism_losses_for_row(r) for r in h_rows]

        for i, mechanism in enumerate(MECHANISMS):
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
    fig.legend(handles, labels, loc='lower center', ncol=min(len(MECHANISMS), 3),
               frameon=False, labelcolor=PRIMARY_TEXT, bbox_to_anchor=(0.5, 0.0))
    return fig


def main():
    rows = load_results(RESULTS_CSV)
    if not rows:
        print(f"No completed points in {RESULTS_CSV} yet -- run sweep_loss_vs_dimensions.py first.")
        return
    heights = sorted(set(r['h_core'] for r in rows))

    fig_totals = plot_totals(rows, heights)
    fig_totals.savefig('loss_vs_dimensions.png', dpi=150, facecolor=fig_totals.get_facecolor())
    print("Saved loss_vs_dimensions.png")

    fig_breakdown = plot_mechanism_breakdown(rows, heights)
    fig_breakdown.savefig('loss_by_mechanism.png', dpi=150, facecolor=fig_breakdown.get_facecolor())
    print("Saved loss_by_mechanism.png")

    plt.show()


if __name__ == '__main__':
    main()
