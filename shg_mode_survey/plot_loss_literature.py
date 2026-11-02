"""Literature-based lowest-loss overview (same axes/style as plot_loss_overview.py): what published data says about the
intrinsic absorption of SiN, TiO2, ScAlN/AlN, SiC, AlGaN and LiNbO3 near the 450 nm pump and toward the 215-235 nm SH.

Every plotted number is in materials/literature_loss_points.csv (written here; read by nothing else yet) with its source,
location in the paper, and the confinement weight Gamma used. Conversion everywhere: loss[dB/cm] = (10/ln10)*4*pi*k/lambda.

Reading the symbols (see the figure legend):
  filled triangle (down) = UPPER BOUND on core absorption from a waveguide/ring result, loss_wg / Gamma, with Gamma from EMode
                           (materials/literature_gamma.csv) or already de-rated by the authors (Corato-Zanarella's 'bulk-film' alpha)
  open triangle (down)   = upper bound where Gamma was NOT computed: plotted at Gamma = 1 -- the true bound can only be HIGHER
  solid line             = tabulated measurement (ellipsometry / WGRAS); dotted where below the instrument's resolving power
  dashed line            = model extrapolation (Urbach tail) -- not a measurement
Usage (from shg_mode_survey/): python plot_loss_literature.py
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
from survey_config import SETTINGS as CFG  # noqa: E402
import build_assumptions_report as bar  # noqa: E402

LIT = r'G:\Shared drives\Corp Main\Engineering\Design & SHG Analysis (Brent)\eMode Modeling\Literature_Material_Loss'
INK, MUTED = bar.INK, bar.INK_MUTED
COL = {'SiN': '#009E73', 'TiO2': '#D55E00', 'ScAlN': '#2171b5', 'AlN': '#C23A73', 'SiC': '#7b3294',
       'AlGaN': '#B8860B', 'LN': '#8c564b'}
HC = 1239.84198  # eV*nm


def dB_per_cm_per_k(lam_nm):
    return 10 / math.log(10) * 4 * math.pi / (lam_nm * 1e-9) / 100.0


def k_of(loss_dB_cm, lam_nm):
    return loss_dB_cm / dB_per_cm_per_k(lam_nm)


def gamma_lookup():
    g = {}
    p = os.path.join('materials', 'literature_gamma.csv')
    for r in csv.DictReader(open(p)):
        if r['gamma_abs_pert']:
            g[(r['case'], r['pol'])] = float(r['gamma_abs_pert'])
    return g


def main():
    G = gamma_lookup()
    pts = []   # rows for the CSV

    def add(material, label, kind, lam, loss_dB_cm, gamma, gamma_src, source, where, note=''):
        bound = loss_dB_cm / gamma
        pts.append(dict(material=material, label=label, kind=kind, wavelength_nm=lam, wg_loss_dB_per_cm=loss_dB_cm,
                        gamma_used=gamma, gamma_source=gamma_src, bound_dB_per_cm=bound, k_equiv=k_of(bound, lam),
                        source=source, location=where, note=note))
        return pts[-1]

    # ---- SiN: Corato-Zanarella bulk-film absorption (already de-rated by their eta_abs = 1.0025 ~ 1; paper says UPPER BOUND)
    # published (Opt. Express 32, 5718, Fig. 5 text): TE, 4 um wide ring propagation loss; the 780 nm value differs from the preprint's 0.02 dB/cm
    cz = [(461, 2.4), (488, 1.2), (532, 0.20), (644, 0.060), (780, 0.0362)]
    for lam, a in cz:
        add('SiN', 'Corato-Zanarella 2023 (LPCVD Si/N=0.82), film absorption', 'bound_closed', lam, a, 1.0,
            'authors: eta_abs=1.0025 (preprint Table S21); EMode check 1.0015', 'Corato-Zanarella et al. Opt. Express 32, 5718 (2024)',
            'Sec. 3 / Fig. 5 caption p.7', 'TE, 4 um wide ring; near absorption limit (authors); preprint Table S23 had 2.49/1.2/0.20/0.06/0.02')
    # ---- SiN: Chauhan 2020 20 nm x 1.3 um core, 0.08 dB/cm at 450 nm; polarization unstated -> TE and TM bounds
    add('SiN', 'Chauhan 2020 (20 nm core) if TE', 'bound_closed', 450, 0.08, G[('Chauhan_20x1300_450', 'TE')],
        'EMode, gamma_for_literature.py (n_core 2.10 assumed)', 'Chauhan et al. CLEO 2020', 'abstract p.1, Table 1 p.2',
        'polarization not stated; coupling loss subtracted, 2 m spiral')
    add('SiN', 'Chauhan 2020 (20 nm core) if TM', 'bound_closed', 450, 0.08, G[('Chauhan_20x1300_450', 'TM')],
        'EMode, gamma_for_literature.py (n_core 2.10 assumed)', 'Chauhan et al. CLEO 2020', 'abstract p.1, Table 1 p.2',
        'polarization not stated')
    # ---- SiN: Morin/Chang 2021 (Optica 8, 755), 24 nm core, TE-only 0.8 um guide; cutback at ~450 and 405 nm
    add('SiN', 'Morin 2021 (24 nm core, 2.8 um wide, TE) 450 nm', 'bound_closed', 450, 0.22, G[('Morin_24x2800_450', 'TE')],
        'EMode, gamma_for_literature.py (n_core 2.05 assumed)', 'Morin et al. Optica 8, 755 (2021)', 'p.2 col.1',
        'cutback; sidewall scattering still contributes -> upper bound')
    add('SiN', 'Morin 2021 (24 nm core, 0.8 um wide, TE) 450 nm', 'bound_closed', 450, 0.35, G[('Morin_24x800_450', 'TE')],
        'EMode, gamma_for_literature.py (n_core 2.05 assumed)', 'Morin et al. Optica 8, 755 (2021)', 'p.2 col.1',
        'cutback; narrower guide -> more sidewall scattering')
    add('SiN', 'Morin 2021 (24 nm core, 0.8 um wide, TE) 405 nm', 'bound_closed', 405, 0.93, G[('Morin_24x800_405', 'TE')],
        'EMode, gamma_for_literature.py (n_core 2.07 assumed)', 'Morin et al. Optica 8, 755 (2021)', 'p.2 col.1',
        'cutback; 2.8 um guide gave 0.9 dB/cm too (sidewall not dominant at 405 nm)')
    # ---- SiN PECVD: Sacher 2019 Wafer 2 (PECVD, 135 nm x 340 nm), band-average 466-500 nm: TE <= 4.1, TM <= 2.8 dB/cm
    add('SiN', 'Sacher 2019 PECVD (135 nm core, 340 nm wide) TE', 'bound_closed', 483, 4.1, G[('Sacher_135x340_483', 'TE')],
        'EMode, gamma_for_literature.py (n_core 1.90 assumed)', 'Sacher et al. Opt. Express 27, 37400 (2019)', 'Sec. 3 p.6, Table 3',
        'PECVD Wafer 2; avg over 466-500 nm; LPCVD Wafer 3 was worse')
    add('SiN', 'Sacher 2019 PECVD (135 nm core, 340 nm wide) TM', 'bound_closed', 483, 2.8, G[('Sacher_135x340_483', 'TM')],
        'EMode, gamma_for_literature.py (n_core 1.90 assumed)', 'Sacher et al. Opt. Express 27, 37400 (2019)', 'Sec. 3 p.6, Table 3',
        'PECVD Wafer 2; avg over 466-500 nm')
    # ---- TiO2: Bradley 2011 amorphous sputtered film, prism-coupled slab, TE, 633 nm: 0.12 dB/mm; 0.25 um film -> Gamma ~1 (not computed)
    add('TiO2', 'Bradley 2012 amorphous sputtered TiO2 film (250 nm slab, TE)', 'bound_open', 633, 1.2, 1.0, 'not computed (thick slab, Gamma likely >= 0.9)',
        'Bradley et al. Opt. Express 20, 23821 (2012)', 'abstract, p.7 text', 'planar-film loss; waveguides were 26 dB/cm')
    # ---- AlN (host, reference): Liu 2018 ring at 455 nm, Gamma not computed
    add('AlN', 'Liu 2018 AlN ring (500x800 nm, SiO2 clad) -- AlN, not ScAlN', 'bound_open', 455, 3.5, 1.0, 'not computed (plotted at 1)',
        'Liu et al. arXiv:1807.10716', 'p.4', 'authors: Rayleigh + sidewall scattering')
    # ---- AlGaN
    add('AlGaN', 'Gundogdu 2023 Al0.69Ga0.31N ring, TE, 785 nm', 'bound_open', 785, 2.5, 1.0, 'not computed (plotted at 1)',
        'Gundogdu et al. arXiv:2312.03128', 'Table I', 'total loss from Qint; no absorption split')
    add('AlGaN', 'Floyd 2020 n-Al0.65Ga0.35N slab, ~280 nm (free-carrier dominated)', 'bound_open', 280, 24.0, 1.0,
        'not computed (plotted at 1)', 'Floyd et al. Phys. Status Solidi A 217:1900801', 'Sec 3.3',
        '22-26 dB/cm (midpoint); authors attribute mainly to free-carrier absorption')
    # ---- LN: Desiatov ring
    add('LN', 'Desiatov 2019 TFLN ring, 637 nm (scattering-limited)', 'bound_open', 637, 0.06, 1.0, 'not computed (plotted at 1)',
        'Desiatov et al. arXiv:1902.08217', 'p.2', 'Qint 1.1e7; authors: sidewall scattering-limited')
    # ---- ScAlN: detection limit statement, plotted as a line in the figure
    pts.append(dict(material='ScAlN', label='van Deurzen 2023 MBE Al0.89Sc0.11N: k below detection limit', kind='detection_limit',
                    wavelength_nm='193-1690', wg_loss_dB_per_cm='', gamma_used='', gamma_source='', bound_dB_per_cm='',
                    k_equiv=1e-3, source='van Deurzen et al. arXiv:2309.16551', location='p.4', note='k <= 0.001 (instrument floor)'))
    # ---- SiC: band edge only
    pts.append(dict(material='SiC', label='4H-SiC band gap 3.26-3.30 eV (~376-380 nm); no 400-500 nm k found', kind='band_edge',
                    wavelength_nm=378, wg_loss_dB_per_cm='', gamma_used='', gamma_source='', bound_dB_per_cm='', k_equiv='',
                    source='de Oliveira 2002 (via SiC pass)', location='Table 1', note='crystalline SiC is absorbing at the SH'))

    # ---------------------------------------------------------------- curves
    data = bar.precompute_dispersion_data()
    lam = data['lam_core']
    aln_m = data['aln_meas']
    sc_fits = json.load(open('materials/ScAlN_Baumler2019_sellmeier_fits.json'))['fits']
    lam_sc = np.linspace(207, 800, 500)

    fig, ax = plt.subplots(figsize=(14, 9.2))
    # ---- faded context: curves of the original overview
    ax.plot(aln_m['wavelength_nm'], aln_m['k_o'], color=COL['AlN'], lw=1.2, alpha=0.30, label='(faded) AlN k_o measured, AM187-LT6')
    ax.plot(lam, data['sinx_k'], color=COL['SiN'], lw=1.2, alpha=0.30, label='(faded) SiNx Beliaev fit  [original chart]')
    ax.plot(lam, data['tio2_k'], color=COL['TiO2'], lw=1.2, alpha=0.30, label='(faded) TiO2 Siefke fit  [original chart]')
    for key in ('0.23', '0.32', '0.41'):
        k = np.array([bar.eval_k(sc_fits[key]['emode_equation_complex'], l) for l in lam_sc])
        ax.plot(lam_sc, k, color=COL['ScAlN'], lw=1.0, alpha=0.30)
    ax.plot([], [], color=COL['ScAlN'], lw=1.0, alpha=0.30, label='(faded) ScAlN Baumler fits 23/32/41 % Sc  [original chart]')

    # ---- SiN
    c = COL['SiN']
    z = [p for p in pts if p['label'].startswith('Corato')]
    ax.plot([p['wavelength_nm'] for p in z], [p['k_equiv'] for p in z], 'v', color=c, ms=9, zorder=6,
            label='SiN  Corato-Zanarella 2023: film absorption, upper bound (ring-width series; LPCVD Si/N=0.82)')
    lam_u = np.linspace(380, 600, 100)
    k461 = z[0]['k_equiv']
    ax.plot(lam_u, k461 * np.exp(5.07 * (HC / lam_u - HC / 461.0)), '--', color=c, lw=1.6,
            label='SiN  Urbach extrapolation, slope 5.07 /eV from their band-fluctuation fit (model, not measured)')
    ch = [p for p in pts if p['label'].startswith('Chauhan')]
    ax.plot([450], [ch[0]['k_equiv']], 'v', color=c, ms=11, mec='k', mew=1.0, zorder=7,
            label='SiN  Chauhan 2020, 20 nm core: bound if TE (0.08 dB/cm / G=0.108)')
    ax.plot([450], [ch[1]['k_equiv']], 'v', mfc='white', color=c, ms=11, mew=1.6, zorder=7,
            label='SiN  ... if TM (G=0.012): polarization not stated in the paper')
    ax.annotate('TE', (450, ch[0]['k_equiv']), xytext=(-16, -3), textcoords='offset points', fontsize=8, color=c, ha='right', va='center')
    ax.annotate('TM', (450, ch[1]['k_equiv']), xytext=(-16, 3), textcoords='offset points', fontsize=8, color=c, ha='right', va='center')
    mo = [p for p in pts if p['label'].startswith('Morin')]
    ax.plot([450], [mo[0]['k_equiv']], 'v', color=c, ms=11, mec='k', mew=1.0, zorder=7,
            label='SiN  Morin 2021, 24 nm core, 2.8 um wide, TE: 0.22 dB/cm / G=0.146 (n_core assumed)')
    ax.plot([450], [mo[1]['k_equiv']], 'v', color=c, ms=8, mec='k', mew=0.6, zorder=7, label='SiN  ... 0.8 um wide (0.35 dB/cm) and 405 nm (0.93 dB/cm)')
    ax.plot([405], [mo[2]['k_equiv']], 'v', color=c, ms=8, mec='k', mew=0.6, zorder=7)
    pe = [p for p in pts if p['label'].startswith('Sacher')]
    ax.plot([483], [pe[0]['k_equiv']], 's', color=c, ms=9, mec='k', mew=0.8, zorder=7,
            label='SiN  PECVD best: Sacher 2019, 135 nm core, TE 4.1 / TM 2.8 dB/cm (466-500 nm avg), both ~6 dB/cm after /G')
    ax.plot([483], [pe[1]['k_equiv']], 's', mfc='white', color=c, ms=9, mew=1.4, zorder=7)
    for lam_e, txt in ((275, 'SiN edge, LPCVD'), (320, 'edge, PECVD-LF'), (400, 'edge, PECVD-MF/HF')):
        ax.plot([lam_e, lam_e], [1e-2, 0.3], color=c, lw=1.0, ls=':', alpha=0.8, zorder=2)
        ax.text(lam_e - 2, 0.29, txt, rotation=90, fontsize=6.5, color=c, ha='right', va='top')
    ax.plot([326, 326], [1e-2, 0.3], color=COL['LN'], lw=1.0, ls=':', alpha=0.9, zorder=2)
    ax.text(328, 0.29, 'LiNbO3 gap 3.8 eV', rotation=90, fontsize=6.5, color=COL['LN'], ha='left', va='top')
    ax.axhline(2e-3, color='#888888', lw=1.0, ls=':', zorder=1)
    ax.text(800, 2.2e-3, 'typical ellipsometry resolving limit  k ~ 1e-3 .. 2e-3 (Corato-Zanarella quote 0.002)', ha='right', va='bottom', fontsize=8, color='#666666')

    # ---- TiO2: Siefke ALD tabulated n,k (350 nm film) ; solid where resolvable, dotted below ~1e-3 (dispersion-model tail)
    raw = open(os.path.join(LIT, 'TiO2', 'RII_Siefke2016_TiO2_nk_data.txt'), encoding='utf-8').read().split('data: |')[1].splitlines()
    tab = np.array([[float(v) for v in ln.split()[:3]] for ln in raw if ln.strip() and ln.split()[0][0].isdigit()])
    lt, kt = tab[:, 0] * 1000.0, tab[:, 2]
    sel = (lt >= 200) & (lt <= 800) & (kt > 0)
    hi = sel & (kt >= 1e-3)
    ax.plot(lt[hi], kt[hi], '-', color=COL['TiO2'], lw=2.0, zorder=5, label='TiO2  Siefke 2016 ALD film, tabulated ellipsometry (350 nm)')
    lo = sel & (lt >= 360)
    ax.plot(lt[lo], kt[lo], ':', color=COL['TiO2'], lw=2.0, zorder=5, label='TiO2  ... dotted: below ~1e-3 = dispersion-model tail, unresolved by the film')
    E = HC / np.linspace(380, 700, 100)
    lam_st = np.linspace(380, 700, 100)
    alpha_cm = 1.28e5 * np.exp((E - 3.684) / 0.1672)
    ax.plot(lam_st, alpha_cm * 100 * lam_st * 1e-9 / (4 * math.pi), '--', color=COL['TiO2'], lw=1.6, alpha=0.8,
            label='TiO2  Studenyak 2018 sputtered film, Urbach law extrapolated (alpha0 1.28e5/cm, E0 3.684 eV, Eu 167 meV)')

    bd = [p for p in pts if p['label'].startswith('Bradley')][0]
    ax.plot([633], [bd['k_equiv']], 'v', mfc='white', color=COL['TiO2'], ms=10, mew=1.6, zorder=7,
            label='TiO2  Bradley 2012 amorphous sputtered film, 1.2 dB/cm @633 nm (prism-coupled slab, Gamma ~1 not computed)')
    # ---- ScAlN / AlN
    ax.plot([195, 800], [1e-3, 1e-3], '-', color=COL['ScAlN'], lw=2.2, zorder=5, alpha=0.9,
            label='ScAlN  van Deurzen 2023 (MBE, 11 % Sc): k below detection limit 1e-3, 193-1690 nm')
    p = [q for q in pts if q['material'] == 'AlN'][0]
    ax.plot([455], [p['k_equiv']], 'v', mfc='white', color=COL['AlN'], ms=10, mew=1.8, zorder=7,
            label='AlN (host, not ScAlN)  Liu 2018 ring 3.5 dB/cm @455 nm, Gamma not computed')

    # ---- SiC: band edge
    ax.axvline(378, color=COL['SiC'], lw=2.0, ls='-.', zorder=3)
    ax.axvspan(195, 378, color=COL['SiC'], alpha=0.07, lw=0)
    ax.text(381, 2.2, '4H-SiC gap 3.26 eV: crystalline SiC absorbs at all shorter lambda;\nno 400-500 nm k or loss found (only 1064/1550 nm data)',
            fontsize=8, color=COL['SiC'], va='top')

    # ---- AlGaN
    for q in [q for q in pts if q['material'] == 'AlGaN']:
        ax.plot([q['wavelength_nm']], [q['k_equiv']], 'v', mfc='white', color=COL['AlGaN'], ms=10, mew=1.8, zorder=7)
    ax.plot([], [], 'v', mfc='white', color=COL['AlGaN'], ms=10, mew=1.8,
            label='AlGaN  785 nm ring (Al0.69, 2.5 dB/cm) and ~280 nm n-doped slab (Al0.65, 22-26 dB/cm, free-carrier dominated); Gamma not computed')

    # ---- LiNbO3: WGRAS bulk absorption (undoped congruent), 390-800 nm
    for fn, ls, lab in (('oe-23-17-21690-d005.CSV', '-', 'ordinary'), ('oe-23-17-21690-d006.CSV', '--', 'extraordinary')):
        rows = [ln.split(',') for ln in open(os.path.join(LIT, 'TFLN', 'Leidinger_2015_datafiles', fn), encoding='utf-8').read().splitlines()
                if ln and ln[0].isdigit()]
        l_ = np.array([float(r[0]) for r in rows]); a_ = np.array([float(r[1]) for r in rows])
        m = (l_ <= 800)
        k_ = a_[m] * 100.0 * l_[m] * 1e-9 / (4 * math.pi)
        ax.plot(l_[m], k_, ls, color=COL['LN'], lw=2.0, zorder=5,
                label=f'LiNbO3  bulk undoped congruent, {lab} (WGRAS, Leidinger 2015): upper limit, Fe2+-impurity set' if ls == '-' else None)
        pts.extend(dict(material='LN', label=f'Leidinger 2015 WGRAS bulk, {lab}', kind='bulk_absorption', wavelength_nm=float(a),
                        wg_loss_dB_per_cm=float(b) * 10 / math.log(10), gamma_used=1.0, gamma_source='bulk',
                        bound_dB_per_cm=float(b) * 10 / math.log(10), k_equiv=float(b) * 100 * float(a) * 1e-9 / (4 * math.pi),
                        source='Leidinger et al. Opt. Express 23, 21690 (2015)', location=f'Data File {5 if ls == "-" else 6} (figshare)',
                        note='extinction = upper limit on absorption; crystal-specific') for a, b in zip(l_[m], a_[m]) if float(a) in (390, 410, 450, 490, 700))
    ax.plot([], [], '--', color=COL['LN'], lw=2.0, label='LiNbO3  ... extraordinary')
    ax.plot([637], [k_of(0.06, 637)], 'v', mfc='white', color=COL['LN'], ms=10, mew=1.8, zorder=7,
            label='LiNbO3  Desiatov 2019 TFLN ring @637 nm (0.06 dB/cm, scattering-limited, Gamma not computed)')

    # ---- what the simulation's loss model assumes (black, as in the original chart)
    lam_sh = data['lam_sh_only']
    ax.plot(lam_sh, data['sh_cal_k'], color='black', lw=3.2, solid_capstyle='round', label='SH loss USED: calibrated 100 dB/cm (assumption)')
    mech = CFG['pump_absorption_mechanisms']
    alpha0_cm = sum(m_['alpha0'] for m_ in mech) / 100.0
    kl = k_of(alpha0_cm, 450.0)
    ax.plot([430, 470], [kl, kl], color='black', lw=3.2, solid_capstyle='round',
            label=f'pump loss model: in-layer growth-interface alpha0 = {alpha0_cm:.0f} dB/cm')

    bar.shade_bands(ax)
    ax.set_yscale('log')
    ax.set_xlim(195, 800)
    ax.set_ylim(1e-9, 3.0)
    ax.set_xlabel('wavelength [nm]   (shaded: SH 215-235 nm, pump 430-470 nm)')
    ax.set_ylabel('k  (log)  -- waveguide results shown as the core k they bound (loss / Gamma)')
    for loc, lam0, lab in ((1.0, 225.0, 'dB/cm  (at 225 nm, SH)'), (1.085, 450.0, 'dB/cm  (at 450 nm, pump)')):
        cc = dB_per_cm_per_k(lam0)
        sec = ax.secondary_yaxis(loc, functions=(lambda k, cc=cc: k * cc, lambda d, cc=cc: d / cc))
        sec.set_ylabel(lab, color=MUTED)
        sec.tick_params(colors=MUTED)
    fig.text(0.5, 0.022, 'Triangles are UPPER BOUNDS on core absorption (loss / Gamma): filled = Gamma from EMode or the authors; open = Gamma not computed (plotted at 1, true bound is higher).',
             ha='center', fontsize=7.4, color=MUTED)
    fig.text(0.5, 0.006, 'Lines: solid = tabulated, dotted = unresolved, dashed = extrapolation.  Each dB/cm axis is exact only at its own wavelength.',
             ha='center', fontsize=7.4, color=MUTED)
    ax.set_title('What published data says about intrinsic absorption near the 450 nm pump and toward 215-235 nm\n'
                 'lowest credible values found per material  (black = what the simulation assumes; faded = original-chart curves)', fontsize=11, color=INK)
    bar.style_ax(ax)
    ax.legend(fontsize=6.9, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.09), ncol=1)
    fig.tight_layout(rect=(0, 0.035, 0.93, 1))
    out = os.path.join('runs', 'loss_overview_literature.png')
    fig.savefig(out, dpi=140)
    print('wrote', out)

    with open(os.path.join('materials', 'literature_loss_points.csv'), 'w', newline='', encoding='utf-8') as fh:
        cols = ['material', 'label', 'kind', 'wavelength_nm', 'wg_loss_dB_per_cm', 'gamma_used', 'gamma_source', 'bound_dB_per_cm',
                'k_equiv', 'source', 'location', 'note']
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(pts)
    print('wrote materials/literature_loss_points.csv', len(pts), 'rows')


if __name__ == '__main__':
    main()
