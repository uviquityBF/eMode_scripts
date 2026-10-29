"""Chart: EMode-native vs Payne-Lacey-adapted sidewall scattering vs wavelength for TM00 and TM04 of ridge
350x400 at several sidewall correlation lengths (data: materials/scattering_models_vs_lambda.csv from
compute_scattering_models_vs_lambda.py). Top row = absolute dB/cm; bottom row = each curve divided by its own
value at the reference wavelength, with 1/lambda^2, ^3, ^4 guide curves through 1 there.
Usage: python plot_scattering_models.py [ref_wavelength_nm=450]
TM04 points with bound=0 (n_eff below the cladding/substrate cutoff, i.e. leaky) are drawn as hollow markers.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLORS = {2.0: '#1baf7a', 10.0: '#eb6834', 50.0: '#2a78d6'}


def at_ref(L, V, ref=450.0):
    """Value at the reference wavelength (log-interpolated between the computed wavelengths)."""
    return float(np.exp(np.interp(ref, L, np.log(V))))


def main(ref=450.0):
    rows = list(csv.DictReader(open(os.path.join(HERE, 'materials', 'scattering_models_vs_lambda.csv'))))
    d = {}
    for r in rows:
        d.setdefault((r['mode'], float(r['Lc_nm'])), []).append(
            (float(r['lambda_nm']), float(r['emode_dB_per_cm']), float(r['payne_lacey_dB_per_cm']),
             r.get('bound', '') != '0'))
    fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=False)
    lam_g = np.linspace(220, 600, 100)
    for col, mode in enumerate(('TM00', 'TM04')):
        for lc, c in COLORS.items():
            pts = sorted(d.get((mode, lc), []))
            if not pts:
                continue
            L, E, P, B = (np.array(a) for a in zip(*pts))
            for row in (0, 1):
                ok = np.isfinite(E)
                nE = nP = 1.0
                if row == 1 and mode == 'TM04':
                    # TM04 is guided only near the SH (n_eff falls below the substrate index by ~250 nm), so it cannot be
                    # tracked to the reference wavelength: plot SH-mode scattering / pump TM00 scattering at `ref` instead
                    t0 = np.array(sorted(d[('TM00', lc)]))[:, :3]
                    nE, nP = (at_ref(t0[:, 0], t0[:, k], ref) for k in (1, 2))
                    ok = ok & B
                elif row == 1:
                    nE, nP = at_ref(L, E, ref), at_ref(L, P, ref)
                axs[row, col].plot(L[ok], E[ok] / nE, '-', color=c, lw=2, label=f'EMode, Lc={lc:g} nm' if row == 0 else None)
                axs[row, col].plot(L[ok & B], E[ok & B] / nE, 'o', color=c, ms=4)
                axs[row, col].plot(L[ok & ~B], E[ok & ~B] / nE, 'o', mfc='white', color=c, ms=5)
                axs[row, col].plot(L[ok] if row == 1 and mode == 'TM04' else L, (P[ok] if row == 1 and mode == 'TM04' else P) / nP, '--', color=c, lw=1.6, label=f'Payne-Lacey, Lc={lc:g} nm' if row == 0 else None)
        ax = axs[1, col]
        if mode == 'TM00':
            for p, ls in ((2, ':'), (3, '-.'), (4, (0, (5, 1)))):
                ax.plot(lam_g, (ref / lam_g) ** p, color='#555555', lw=1.3, ls=ls, label=f'1/λ^{p}')
        else:
            for r_, ls in ((5, ':'), (10, '-.')):
                ax.axhline(r_, color='#555555', lw=1.3, ls=ls, label=f'{r_}x  (Loss_SH = {r_} x Loss_pump)')
            ax.set_xlim(215, 245)
            ax.set_ylim(1, 15)
        axs[0, col].set_title(f'{mode}{" (tracked by field overlap from 230 nm)" if mode == "TM04" else ""} (ridge 350x400, sidewall rms 2.5 nm)', fontsize=10)
        axs[0, col].set_yscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('wavelength [nm]')
        axs[0, col].set_ylabel('scattering [dB/cm]  (Payne-Lacey uncalibrated)')
        ax.set_ylabel(f'scattering / value at {ref:g} nm' if mode == 'TM00' else f'TM04 scattering / TM00 scattering at {ref:g} nm')
        for a in (axs[0, col], ax):
            a.grid(True, color='#e1e0d9', lw=0.6)
            for s in ('top', 'right'):
                a.spines[s].set_visible(False)
    axs[0, 1].plot([], [], 'o', mfc='white', color='#555', label='hollow = leaky (unbound) point')
    axs[0, 1].legend(fontsize=8, frameon=False, loc='lower right', ncol=2)
    axs[0, 1].set_xlim(215, 390)
    axs[0, 1].axvspan(215, 247, color='#e8f1fb', alpha=0.6, lw=0)
    axs[0, 1].text(218, 40, 'guided', fontsize=8, color='#2a78d6')
    axs[0, 0].legend(fontsize=8, frameon=False, ncol=2)
    axs[1, 0].legend(fontsize=8, frameon=False, ncol=1)
    axs[1, 1].legend(fontsize=8, frameon=False, ncol=1, loc='upper left')
    fig.suptitle('Sidewall-roughness scattering vs wavelength: EMode-native vs Payne-Lacey '
                 '(left: TM00 with 1/λ^n guides; right: TM04 SH mode, bottom = SH/pump ratio)', fontsize=12)
    fig.tight_layout()
    out = os.path.join(HERE, 'runs', 'scattering_models_vs_lambda.png')
    fig.savefig(out, dpi=140)
    print('wrote', out)


if __name__ == '__main__':
    main(*[float(a) for a in sys.argv[1:]])
