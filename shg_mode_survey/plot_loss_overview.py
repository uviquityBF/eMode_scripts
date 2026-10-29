"""Material k + loss-assumption overview, with a dB/cm readout (EMode-free; reads the CSV written by
compute_scattering_reference.py). Extends the Input Assumptions report's k panel (page 3):

  * AlN measured k_o / k_e (AM187-LT6), SiNx, TiO2 (as before)
  * ScAlN k from the Baumler fits at 23 / 32 / 41 % Sc (solid = as fitted); shaded band = the loss-case range
    x0.25 .. x2 of the fit (cerenkov_scenarios.K_SCALES); circles = the fitted k at the 450 nm pump
  * black bar at 215-235 nm = the calibrated SH loss actually USED (100 dB/cm)
  * black bars at 450 nm = what the pump-loss model puts on AlN: (upper) the summed in-layer alpha0 of the four
    growth-interface defect mechanisms, (lower) the confinement-weighted modal absorption it produces for the
    TM00 pump of the reference ridge
  * light-gray dashed = EMode-native roughness scattering (survey roughness 2.5/0.3 nm rms) of the fundamental
    TM mode of the reference ridge, expressed as an equivalent k
  * two right-hand axes: dB/cm at 225 nm (SH) and at 450 nm (pump) -- the k <-> dB/cm factor scales as 1/lambda,
    so each axis is exact only at its own wavelength.
Everything is converted with loss[dB/cm] = (10/ln10) * 4*pi*k/lambda, i.e. an "equivalent k" for the non-k items.
Usage (from shg_mode_survey/): python plot_loss_overview.py [h] [w]
"""
import csv
import json
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
import geometry as geo  # noqa: E402
import cerenkov_scenarios as sc  # noqa: E402
from survey_config import SETTINGS as CFG  # noqa: E402
import build_assumptions_report as bar  # noqa: E402

INK, MUTED = bar.INK, bar.INK_MUTED
SC_COLORS = {'0.23': '#6baed6', '0.32': '#2171b5', '0.41': '#08306b'}


def dB_per_cm_per_k(lam_nm):
    return 10 / math.log(10) * 4 * math.pi / (lam_nm * 1e-9) / 100.0


def k_equiv(loss_dB_cm, lam_nm):
    return loss_dB_cm / dB_per_cm_per_k(lam_nm)


def main(h=350.0, w=400.0):
    data = bar.precompute_dispersion_data()
    lam = data['lam_core']
    aln_m = data['aln_meas']
    sc_fits = json.load(open('materials/ScAlN_Baumler2019_sellmeier_fits.json'))['fits']
    lam_sc = np.linspace(207, 600, 500)

    fig, ax = plt.subplots(figsize=(13, 8.6))
    # --- measured / literature materials
    ax.plot(aln_m['wavelength_nm'], aln_m['k_o'], color='#C23A73', lw=1.6, alpha=0.65, label='AlN k_o (measured, AM187-LT6)')
    ax.plot(aln_m['wavelength_nm'], aln_m['k_e'], color='#C23A73', ls='--', lw=1.6, alpha=0.65, label='AlN k_e (measured, AM187-LT6)')
    ax.plot(lam, data['sinx_k'], color='#009E73', lw=1.4, label='SiNx (Beliaev 2022 fit)')
    ax.plot(lam, data['tio2_k'], color='#D55E00', lw=1.4, label='TiO2 (Siefke 2016 fit)')
    # --- ScAlN fits + loss-case bands + pump-band markers
    for key, col in SC_COLORS.items():
        fit = sc_fits[key]
        k = np.array([bar.eval_k(fit['emode_equation_complex'], l) for l in lam_sc])
        lo, hi = sc.K_SCALES['fit_x0.25'], sc.K_SCALES['fit_x2']
        ax.fill_between(lam_sc, np.clip(lo * k, 1e-12, None), np.clip(hi * k, 1e-12, None), color=col, alpha=0.16, lw=0)
        ax.plot(lam_sc, k, color=col, lw=1.9, label=f'ScAlN {float(key) * 100:.0f}% Sc (Baumler fit)')
        k450 = bar.eval_k(fit['emode_equation_complex'], 450.0)
        ax.errorbar([450], [k450], yerr=[[k450 - lo * k450], [hi * k450 - k450]], fmt='o', color=col, ms=6,
                    mfc='white', mew=1.6, capsize=3, lw=1.2, zorder=6)
        ax.annotate(f'{float(key) * 100:.0f}% Sc: k(450) = {k450:.1e}  ({k450 * dB_per_cm_per_k(450.0):.0f} dB/cm)',
                    (450, k450), xytext=(-12, {'0.23': -4, '0.32': -4, '0.41': 4}[key]), textcoords='offset points',
                    fontsize=7.5, color=col, ha='right', va='center')
    ax.plot([], [], 's', color=SC_COLORS['0.32'], alpha=0.3, ms=9, label='shaded band = loss cases x0.25 ... x2 of the fit')
    ax.plot([], [], 'o', mfc='white', color=SC_COLORS['0.32'], label='circle = fitted k at the 450 nm pump (bars: x0.25..x2)')
    # --- loss-model markers (black)
    lam_sh = data['lam_sh_only']
    ax.plot(lam_sh, data['sh_cal_k'], color='black', lw=3.2, solid_capstyle='round',
            label='SH loss USED: calibrated 100 dB/cm (flat, confinement-weighted)')
    mech = CFG['pump_absorption_mechanisms']
    alpha0_cm = sum(m['alpha0'] for m in mech) / 100.0                     # dB/cm, in-layer, 4 mechanisms summed
    k_layer = k_equiv(alpha0_cm, 450.0)
    cmp_csv = os.path.join('runs', 'pump_loss_assumption_comparison.csv')
    modal_cm = None
    if os.path.exists(cmp_csv):
        for r in csv.DictReader(open(cmp_csv)):
            if abs(float(r['w_core']) - w) < 1e-6:
                modal_cm = float(r['abs_code_dB_per_cm'])
    ax.plot([430, 470], [k_layer, k_layer], color='black', lw=3.2, solid_capstyle='round',
            label=f'pump loss model: AlN growth-interface defect layer, in-layer alpha0 = {alpha0_cm:.0f} dB/cm (sum of 4 mechanisms, 40-50 nm thick)')
    ax.annotate(f'{alpha0_cm:.0f} dB/cm in the 40-50 nm interface layer', (470, k_layer), xytext=(10, 6),
                textcoords='offset points', fontsize=8, color='black')
    if modal_cm:
        k_modal = k_equiv(modal_cm, 450.0)
        ax.plot([430, 470], [k_modal, k_modal], color='black', lw=1.8, ls=(0, (1, 1.5)), solid_capstyle='butt',
                label=f'... as seen by the TM00 mode (confinement-weighted, h={h:g} w={w:g}): {modal_cm:.1f} dB/cm')
        ax.annotate(f'{modal_cm:.1f} dB/cm modal', (470, k_modal), xytext=(10, -12), textcoords='offset points',
                    fontsize=8, color='black')
    # --- scattering reference (EMode-native), light gray dashed
    sp = os.path.join('materials', f'scattering_reference_h{h:g}_w{w:g}.csv')
    if os.path.exists(sp):
        rows = list(csv.DictReader(open(sp)))
        rows = [r for r in rows if float(r['lambda_nm']) >= 215.0]  # <215 nm: AlN index-equation pole, unreliable
        ls_ = np.array([float(r['lambda_nm']) for r in rows])
        ks_ = np.array([k_equiv(float(r['scattering_dB_per_cm']), float(r['lambda_nm'])) for r in rows])
        ax.plot(ls_, ks_, color='#b4b4ac', ls='--', lw=2.0, zorder=2,
                label=f'roughness scattering, EMode-native, TM00 of ridge h={h:g} w={w:g} '
                      f'(sidewall {CFG["roughness_rms"][0]:g} nm rms, corr {CFG["correlation_length"][0]:g} nm) -> equivalent k')
    bar.shade_bands(ax)
    ax.set_yscale('log')
    ax.set_xlim(195, 600)
    ax.set_ylim(1e-6, 3.0)
    ax.set_xlabel('wavelength [nm]   (shaded: SH 215-235 nm, pump 430-470 nm)')
    ax.set_ylabel('k  (log) -- non-k loss items shown as the k that would give the same dB/cm')
    # secondary dB/cm axes (log), exact at their own wavelength
    for loc, lam0, lab in ((1.0, 225.0, 'dB/cm  (at 225 nm, SH)'), (1.085, 450.0, 'dB/cm  (at 450 nm, pump)')):
        c = dB_per_cm_per_k(lam0)
        sec = ax.secondary_yaxis(loc, functions=(lambda k, c=c: k * c, lambda d, c=c: d / c))
        sec.set_ylabel(lab, color=MUTED)
        sec.tick_params(colors=MUTED)
    fig.text(0.5, 0.005, 'Each dB/cm axis is exact only at its own wavelength (loss = 54.6*k/lambda): read the 225 nm axis for the SH band, '
             'the 450 nm axis for the pump band. Non-k items are drawn as the k giving the same dB/cm at that wavelength.',
             ha='center', fontsize=7.5, color=MUTED)
    ax.set_title('Material k and loss assumptions, with dB/cm readout\n'
                 'black = what the simulation\'s loss model assumes; blue = ScAlN fits and loss cases; gray dashed = scattering',
                 fontsize=11, color=INK)
    bar.style_ax(ax)
    ax.legend(fontsize=7.4, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.09), ncol=2)
    fig.tight_layout(rect=(0, 0.02, 0.93, 1))
    out = os.path.join('runs', 'loss_overview_k_dBcm.png')
    fig.savefig(out, dpi=140)
    print('wrote', out)
    return out


if __name__ == '__main__':
    a = [float(x) for x in sys.argv[1:]]
    main(*a)
