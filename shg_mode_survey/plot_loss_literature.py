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
    # ---- SiN: Chauhan (LPCVD 20 nm core, single TE mode -- polarization confirmed by Chauhan 2022, Opt. Express 30, 6960)
    add('SiN', 'Chauhan 2020/2022 LPCVD 20 nm core, TE: 450 nm spiral', 'bound_closed', 450, 0.08, G[('Chauhan_20x1300_450', 'TE')],
        'EMode, gamma_for_literature.py (n_core 2.10 assumed)', 'Chauhan et al. Opt. Express 30, 6960 (2022)', 'p.5-6 (2 m coil, Fig. 3d)',
        'single TE mode; authors quote confinement factor 0.065 at 461 nm (power-type), my absorption weight 0.103-0.108')
    add('SiN', 'Chauhan 2022 LPCVD 20 nm core, TE: 461 nm ring (Qi 9.5e6)', 'bound_closed', 461, 0.09, G[('Chauhan22_20x1300_461', 'TE')],
        'EMode, gamma_for_literature.py (n_core 2.10 assumed)', 'Chauhan et al. Opt. Express 30, 6960 (2022)', 'p.5-6',
        'ring loss 0.09 dB/cm; matches 450 nm spiral; scattering + absorption')
    add('SiN', 'Chauhan 2022 LPCVD 20 nm core, TE: 674 nm photothermal ABSORPTION', 'bound_closed', 674, 0.0017, G[('Chauhan22_20x2300_674', 'TE')],
        'EMode, gamma_for_literature.py (n_core 2.05 assumed)', 'Chauhan et al. Opt. Express 30, 6960 (2022)', 'p.6, Fig. 5',
        'measured absorption 0.17 dB/m (<15% of total loss); authors confinement 0.031 would give k ~7e-8; direct absorption, not scattering')
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
    # ---- SiN: UVMedico / UVL (Aarhus, EMode Photonix) slide, Photonics West 2026 (photographed; values read from the photo, ~+-1 dB/cm).
    # Loft et al. is the annealing paper (ONE vendor); the slide's vendor bars A-G and BBO/SiN series are NOT in it. User-stated: RIGHT chart (vendor bars) = unpatterned thin-film slab modes, Gamma = 1; LEFT chart = patterned high-confinement waveguides (Gamma large, not computed). Likely Loft et al., Opt. Lett. 51(8), 2332 (2026) (not verified).
    SLIDE = 'UVMedico/UVL slide, Photonics West 2026 (photo); related to, but not the same data as, Loft et al. Opt. Lett. 51, 2332 (2026)'
    add('SiN', 'UVMedico slide: width-independent absorption floor of fit (alpha_a), 447 nm', 'bound_open', 447, 9.5, 1.0,
        'assumed ~1: slide says high-confinement waveguides; not computed', SLIDE, 'left chart, alpha_s + alpha_a plateau at 2-2.5 um',
        'patterned waveguides; fit plateau ~9.5 dB/cm; alpha_s alone ~1 dB/cm at 2.5 um; 447 nm confirmed by user')
    # ---- SiN: Loft et al., Opt. Lett. 51(8), 2332 (2026): 115 nm LPCVD stoichiometric Si3N4 on 3 um SiO2 (one vendor), Metricon prism-coupled
    # slab TE modes; values read by eye from Fig. 2 / Fig. 4 of the PDF. Gamma: analytic 3-layer slab (n_f 2.045/2.025/2.005 from Fig. 3 Cauchy, SiO2, air).
    LOFT = 'Loft et al., Opt. Lett. 51(8), 2332 (2026)'
    for lam, a, g in ((447, 3.3, 0.762), (519, 1.0, 0.689), (636, 0.4, 0.573)):
        add('SiN', f'Loft 2026 115 nm LPCVD Si3N4 slab TE, NOT annealed, {lam} nm', 'bound_closed', lam, a, g,
            'analytic 3-layer slab TE0 (115 nm film, n from Loft Fig. 3)', LOFT, 'Fig. 2 dashed reference lines (by eye)',
            'total slab loss incl. ~1.5/1.2/0.7 dB/cm simulated roughness scattering (their Fig. 4a); 2 sigma bands ~+-0.5-1')
    for lam, a in ((447, 11.1), (519, 4.5), (636, 2.0)):
        add('SiN', f'Loft 2026 anneal-induced absorption change after 975 C, {lam} nm', 'bound_closed', lam, a, 1.0,
            'authors: scattering subtracted and scaled by modal confinement', LOFT, 'text (447: 11.1 +- 1.48) and Fig. 4b (519, 636 by eye)',
            'DELTA absorption of the film caused by 975 C anneal (not total loss); 447->636 ratio ~5.5, lambda exponent ~5')
    # ---- AlGaN (open markers, Gamma not computed -> plotted at 1): Gundogdu et al. arXiv:2312.03128 (ring, prism-coupled slab) and Floyd et al. 2020 (n-doped slab)
    GUN = 'Gundogdu et al., AlGaN/AlN heterostructures (arXiv:2312.03128)'
    add('AlGaN', 'Gundogdu 2024 Al0.69Ga0.31N ring, 785 nm, TE0 (250 nm AlGaN on 400 nm AlN)', 'bound_open', 785, 2.5, 1.0,
        'not computed (authors: 90 % of power above the AlN-sapphire interface, NOT the AlGaN-core fraction)', GUN, 'Sec. II.D, Table I',
        'total ring loss from Qint 1.5e5 (TM 7.1 dB/cm); includes interface, sidewall and AlGaN absorption - not separable')
    add('AlGaN', 'Gundogdu 2024 Al0.69Ga0.31N planar slab, ~630 nm, TE0 minimum (prism coupling)', 'bound_open', 630, 2.3, 1.0,
        'not computed (planar, 250 nm film)', GUN, 'Sec. II.B, Fig. 2(d)',
        'TE0 minimum 2.3 dB/cm "above 600 nm" (exact wavelength not digitised; loss RISES toward the blue); no sidewalls, includes AlN/sapphire interface scatter')
    add('AlGaN', 'Floyd 2020 n-Al0.65Ga0.35N planar slab, ~280 nm (LED light)', 'bound_open', 280, 24.0, 1.0,
        'not applicable (planar; effective-thickness treatment)', 'Floyd et al., Phys. Status Solidi A (2020), doi 10.1002/pssa.201900801', 'Abstract; Sec. 3.2-3.3, Fig. 4b',
        'attenuation 5-6 /cm = 22-26 dB/cm (24 plotted); Si-doped n~1-2e18, free-carrier absorption dominates by the authors own model; weak upper bound only')
    # ---- OUR OWN AlN: GL04 (as-grown) and GL03 (post-anneal) cutback slopes, 350 nm wide TM, 450/532/635 nm (xlsx of 2026-11-17).
    # Gamma = core power fraction at 350 nm from validate_survey_loss_vs_gl04 (EMode): 0.94 / 0.90 / 0.84. Slopes = per-device means, all ten devices
    # (GL04, 11/9 and 11/10 sessions); +-4 dB/cm. GL03 Gamma assumed equal to GL04's (geometry not checked) -> open marker.
    OWN = 'GL04 AM171 SD01 / GL03 AM172 SD01 cutback, xlsx 2026-11-17'
    for lam, a, g in ((450, 26.0, 0.94), (532, 17.3, 0.90), (635, 7.8, 0.84)):
        add('AlN', f'OUR GL04 as-grown cutback slope, {lam} nm (350 nm wide, TM)', 'bound_closed', lam, a, g,
            'EMode core power fraction, validate_survey_loss_vs_gl04.py', OWN, 'P2P Loss xlsx, per-device-mean fit',
            'includes sidewall scattering; +-4 dB/cm; 11/9 (450) and 11/10 (532, 635) sessions; sapphire/AlN/PECVD SiO2')
    add('AlN', 'OUR GL03 post-anneal cutback slope, 450 nm (3 devices)', 'bound_open', 450, 20.0, 0.94,
        'assumed = GL04 (not computed)', OWN, '11/9 session: 19.8 +- 6.1 dB/cm', 'only 3 usable devices over 0.2 cm; pre-anneal was 32.3 +- 7.2 (3/30)')
    for v, b, g in (('A', 16.5, 1.5), ('B', 11, 1.5), ('C', 4.5, 0.7), ('D', 7.5, 0.8), ('E', 9.5, 1.5), ('F', 19.5, 2.5), ('G', 6.5, 1.2)):
        add('SiN', f'UVMedico slide vendor {v} SiN film, 447 nm', 'bound_closed', 447, b, 1.0, 'user: slab / unpatterned thin film, Gamma = 1',
            SLIDE, 'right chart (bar chart, values read by eye)', 'vendor-supplied SiN films; anneal state unknown')
        add('SiN', f'UVMedico slide vendor {v} SiN film, 519 nm', 'bound_closed', 519, g, 1.0, 'user: slab / unpatterned thin film, Gamma = 1',
            SLIDE, 'right chart (bar chart, values read by eye)', 'vendor-supplied SiN films; anneal state unknown')
    # ---- TiO2: Bradley 2011 amorphous sputtered film, prism-coupled slab, TE, 633 nm: 0.12 dB/mm; 0.25 um film -> Gamma ~1 (not computed)
    add('TiO2', 'Bradley 2012 amorphous sputtered TiO2 film (250 nm slab, TE)', 'bound_open', 633, 1.2, 1.0, 'not computed (thick slab, Gamma likely >= 0.9)',
        'Bradley et al. Opt. Express 20, 23821 (2012)', 'abstract, p.7 text', 'planar-film loss; waveguides were 26 dB/cm')
    # ---- AlN: Liu 2018 single-crystal MOCVD AlN rings (500 nm film, 800 nm wide, SiO2 clad), TE00; Gamma ~1 (EMode, isotropic n_o approx.)
    add('AlN', 'Liu 2018 AlN ring TE00 455 nm (500x800 nm, SiO2 clad)', 'bound_closed', 455, 3.5, G[('Liu18_AlN_500x800_455', 'TE')],
        'EMode, gamma_for_literature.py (isotropic n_o 2.17, substrate approximated as SiO2)', 'Liu et al. Optica 5, 1279 (2018)', 'p.2-4, Fig. 4',
        'Qint 398k; authors: scattering-limited; wider (1.4 um) ring 1.6 dB/cm in visible (wavelength not given)')
    add('AlN', 'Liu 2018 AlN ring TE00 390 nm (500x800 nm, SiO2 clad)', 'bound_closed', 390, 8.0, G[('Liu18_AlN_500x800_390', 'TE')],
        'EMode, gamma_for_literature.py (isotropic n_o 2.21, substrate approximated as SiO2)', 'Liu et al. Optica 5, 1279 (2018)', 'abstract, Fig. 2-3',
        'Qint 210k; 0.4 um wide ring 20.4 dB/cm (TE00)')
    # ---- Liu 2018 narrower-ring points (losses scaled from Qint relative to the 0.8 um TE00 ring at 390 nm; approximate) and the
    #      survey's own pump-loss model evaluated at the same geometries (validate_survey_loss_vs_liu.py -> runs/liu_validation.csv)
    vrows = list(csv.DictReader(open(os.path.join(HERE, 'runs', 'liu_validation.csv'), newline='')))
    g_liu = G[('Liu18_AlN_500x800_390', 'TE')]
    for r in vrows:
        lam, wd, pol = float(r['wavelength_nm']), float(r['width_nm']), r['pol_wanted']
        if not (lam == 390.0 and wd == 800.0) and not (lam == 455.0 and wd == 800.0):
            add('AlN', f'Liu 2018 AlN ring {pol}00 {lam:g} nm {wd / 1000:g} um wide (from Qint, approx.)', 'bound_closed', lam,
                float(r['liu_dB_per_cm']), g_liu, 'EMode Gamma ~1.01 (0.8 um case applied)', 'Liu et al. Optica 5, 1279 (2018)', 'Fig. 3 / text',
                r['liu_note'])
        add('AlN', f"SURVEY MODEL at Liu geometry {pol}00 {lam:g} nm {wd / 1000:g} um wide", 'model', lam, float(r['total_dB_per_cm']), g_liu,
            'survey pump-loss model: native roughness scattering (sigma 2.5 nm, Lc 50 nm) + interface absorption (140 dB/cm)',
            'validate_survey_loss_vs_liu.py', 'runs/liu_validation.csv',
            f"scattering {float(r['scattering_dB_per_cm']):.2f} + absorption {float(r['absorption_dB_per_cm']):.2f} dB/cm; Liu {r['liu_dB_per_cm']} dB/cm; "
            f"ratio {float(r['total_dB_per_cm']) / float(r['liu_dB_per_cm']):.2f}")
    # ---- AlN film: our own SPIE 2026 paper (prism coupling, film not waveguide): 2.7 dB/cm at 447 nm; Gamma ~1 not computed
    add('AlN', 'Uviquity SPIE 2026 MOCVD AlN film, 447 nm (prism coupling)', 'bound_open', 447, 2.7, 1.0, 'not computed (500 nm film slab, Gamma likely ~1)',
        'Fisher et al. SPIE 2026 (Uviquity)', 'Sec. 2', 'film loss incl. surface scattering; 0.5 nm RMS')
    # ---- AlN bulk crystal near the SH: Crystal IS patent US 11,555,256 -- summary-level CLAIMS ("less than"), not measured example data I could read
    for lam, a_cm in ((230, 10.0), (220, 15.0)):
        add('AlN', f'Crystal IS patent US11555256 bulk PVT AlN, claimed alpha < {a_cm:g} cm-1 at {lam} nm', 'claim_bound', lam, 4.3429 * a_cm, 1.0,
            'bulk absorption (Gamma = 1)', 'US 11,555,256 (Crystal IS)', 'Summary embodiments (Google Patents text)',
            'patent claim, not peer reviewed; examples section not read; lower bound of claims ~5 cm-1')
    # ---- AlN films in the UV (waveguide/ring losses, Gamma not computed -> plotted at 1): what typical AlN-on-sapphire films give near 370-400 nm
    add('AlN', 'Shin 2021 AlN-on-sapphire ring, 369.5 nm', 'bound_open', 369.5, 60.4, 1.0, 'not computed (plotted at 1)',
        'Shin et al. Appl. Phys. Lett. 118, 211103 (2021)', 'abstract; Fig. 4 / Table I', 'Qint 25.5k; 7.3 dB/cm at 532 nm (Qint 147k)')
    add('AlN', 'Stegmaier 2014 polycrystalline AlN waveguide, 400 nm', 'bound_open', 400, 650.0, 1.0, 'not computed (plotted at 1)',
        'Stegmaier et al. Appl. Phys. Lett. 104, 091108 (2014)', 'text near Fig. 4a (65 dB/mm)', 'polycrystalline 140-200 nm film; loss rises steeply below 500 nm; scattering + defect absorption')
    # ---- AlN bulk crystals, peer-reviewed measured alpha (read in the PDFs): Bickermann 2010 PVT, 12-18 cm-1 over 220-380 nm (data above
    #      5.6 eV, i.e. below ~220 nm, unreliable); Klump 2024 PVT, best of 37 samples alpha(230 nm) = 35 cm-1 (typical 50-150, read from figure)
    for lam in (220, 380):
        add('AlN', f'Bickermann 2010 PVT bulk AlN, alpha <= 18 cm-1 (12-18 measured), {lam} nm', 'bulk_measured', lam, 4.3429 * 18.0, 1.0,
            'bulk absorption (Gamma = 1)', 'Bickermann et al. Phys. Status Solidi C 7, 1743 (2010)', 'Sec. 3 / Fig. 2a',
            '500 um multiply re-sublimated PVT crystal; no reflection correction; above 5.6 eV unreliable')
    add('AlN', 'Klump 2024 PVT bulk AlN, best of 37 samples, alpha(230 nm) = 35 cm-1', 'bulk_measured', 230, 4.3429 * 35.0, 1.0,
        'bulk absorption (Gamma = 1)', 'Klump et al. CrystEngComm (2024)', 'p.4 and p.6', 'typical samples 50-150 cm-1 (read from figure), carbon-rich up to 130-260')
    # ---- AlN MOCVD film absorption floor: Tillner 2020 flat 150-200 cm-1 over 245-400 nm (probably measurement floor)
    for lam in (245, 400):
        add('AlN', f'Tillner 2020 MOCVD AlN/sapphire, flat 150-200 cm-1 (175 used), {lam} nm', 'film_floor', lam, 4.3429 * 175.0, 1.0,
            'bulk absorption (Gamma = 1)', 'Tillner et al. pss(b) 257, 2000278 (2020)', 'abs. spectra (read from text/figures)',
            'likely a measurement floor (2-3% net absorption in a 1.4 um film) -- upper bound for good films')

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

    TALL = os.environ.get('LOSS_CHART_TALL') == '1'
    fig, ax = plt.subplots(figsize=(11, 15) if TALL else (14, 9.2))
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
            label='SiN  Chauhan 2020/22, LPCVD 20 nm core, TE: 0.08 dB/cm (450 nm spiral) / G=0.108; 0.09 dB/cm ring @461')
    ax.plot([461], [ch[1]['k_equiv']], 'v', color=c, ms=8, mec='k', mew=0.6, zorder=7)
    ax.plot([674], [ch[2]['k_equiv']], 'D', color=c, ms=9, mec='k', mew=1.0, zorder=8,
            label='SiN  Chauhan 2022: photothermal ABSORPTION at 674 nm, 0.17 dB/m / G=0.044 (measured absorption, not total loss)')
    mo = [p for p in pts if p['label'].startswith('Morin')]
    ax.plot([450], [mo[0]['k_equiv']], 'v', color=c, ms=11, mec='k', mew=1.0, zorder=7,
            label='SiN  Morin 2021, 24 nm core, 2.8 um wide, TE: 0.22 dB/cm / G=0.146 (n_core assumed)')
    ax.plot([450], [mo[1]['k_equiv']], 'v', color=c, ms=8, mec='k', mew=0.6, zorder=7, label='SiN  ... 0.8 um wide (0.35 dB/cm) and 405 nm (0.93 dB/cm)')
    ax.plot([405], [mo[2]['k_equiv']], 'v', color=c, ms=8, mec='k', mew=0.6, zorder=7)
    pe = [p for p in pts if p['label'].startswith('Sacher')]
    ax.plot([483], [pe[0]['k_equiv']], 's', color=c, ms=9, mec='k', mew=0.8, zorder=7,
            label='SiN  PECVD best: Sacher 2019, 135 nm core, TE 4.1 / TM 2.8 dB/cm (466-500 nm avg), both ~6 dB/cm after /G')
    ax.plot([483], [pe[1]['k_equiv']], 's', mfc='white', color=c, ms=9, mew=1.4, zorder=7)
    uv = [p for p in pts if p['label'].startswith('UVMedico')]
    vb = [p for p in uv if 'vendor' in p['label'] and p['wavelength_nm'] == 447]
    vg = [p for p in uv if 'vendor' in p['label'] and p['wavelength_nm'] == 519]
    ax.plot([p['wavelength_nm'] for p in vb], [p['k_equiv'] for p in vb], 'v', color=c, ms=8, mec='k', mew=0.9, zorder=7,
            label='SiN  UVMedico slide (PW 2026): 7 vendor SiN slab (unpatterned) films, 447 nm 4.5-19.5 and 519 nm 0.7-2.5 dB/cm, G=1 (read from photo)')
    ax.plot([p['wavelength_nm'] for p in vg], [p['k_equiv'] for p in vg], 'v', color=c, ms=8, mec='k', mew=0.9, zorder=7)
    lo = [p for p in pts if p['label'].startswith('Loft 2026 115')]
    ax.plot([p['wavelength_nm'] for p in lo], [p['k_equiv'] for p in lo], 'v', mfc='#b5e5d3', color=c, ms=8, mec='k', mew=0.9, zorder=7,
            label='SiN  Loft 2026 (Opt. Lett.): 115 nm LPCVD Si3N4 slab, NOT annealed, TE 3.3 / 1.0 / 0.4 dB/cm at 447/519/636 nm, G = 0.76/0.69/0.57 (computed)')
    la_ = [p for p in pts if p['label'].startswith('Loft 2026 anneal')]
    ax.plot([p['wavelength_nm'] for p in la_], [p['k_equiv'] for p in la_], 'D', mfc='#e6f5ef', color=c, ms=8, mec='k', mew=0.9, zorder=8,
            label='SiN  Loft 2026: anneal-induced film absorption after 975 C, 11.1 / 4.5 / 2.0 dB/cm at 447/519/636 nm (authors, scattering removed)')
    og = [p for p in pts if p['label'].startswith('OUR GL04')]
    ax.plot([p['wavelength_nm'] for p in og], [p['k_equiv'] for p in og], 'v', color=COL['AlN'], ms=11, mec='k', mew=1.3, zorder=9,
            label='AlN  OUR GL04 as-grown cutback slopes 26.0 / 17.3 / 7.8 dB/cm at 450 / 532 / 635 nm, G = 0.94 / 0.90 / 0.84 (+-4 dB/cm)')
    o3 = [p for p in pts if p['label'].startswith('OUR GL03')][0]
    ax.plot([450], [o3['k_equiv']], 'v', mfc='white', color=COL['AlN'], ms=11, mew=2.0, zorder=9,
            label='AlN  OUR GL03 post-anneal cutback slope 450 nm, 20 +- 6 dB/cm (3 devices; G assumed)')
    fl = [p for p in uv if 'floor' in p['label']][0]
    ax.plot([447], [fl['k_equiv']], 'P', mfc='white', color=c, ms=11, mew=1.8, zorder=8,
            label='SiN  UVMedico slide: patterned high-confinement waveguides, absorption floor of width fit 9.5 dB/cm @447 nm (open cross, G~1 assumed)')
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
    # Nanxi Li / A*STAR / IME SPIE 2026 Fig. 1c,d tabulated ellipsometry: sputtered polycrystalline ScAlN on fused silica, 0/10/20/30 % Sc.
    # Solid where k >= 1e-3 (resolvable), dotted below (model tail, upper bound only). Shades of the ScAlN blue, darker = more Sc.
    nk = list(csv.DictReader(open(os.path.join('materials', 'ScAlN_NanxiLi_SPIE2026_nk.csv'), newline='')))
    for pct, shade in ((0, '#9ecae1'), (10, '#6baed6'), (20, '#3182bd'), (30, '#08306b')):
        rr = np.array([[float(r['wavelength_nm']), float(r['k'])] for r in nk if int(r['sc_percent']) == pct and float(r['k']) > 0])
        rr = rr[(rr[:, 0] >= 200) & (rr[:, 0] <= 800)]
        hi = rr[:, 1] >= 1e-3
        ax.plot(rr[hi, 0], rr[hi, 1], '-', color=shade, lw=1.8, zorder=5,
                label=('ScAlN  Li (A*STAR/IME) SPIE 2026 sputtered films on fused silica, tabulated ellipsometry k: 0/10/20/30 % Sc (light to dark), '
                       'dotted below 1e-3 = fit tail') if pct == 0 else None)
        ax.plot(rr[:, 0], rr[:, 1], ':', color=shade, lw=1.3, zorder=4)
    la = [q for q in pts if q['label'].startswith('Liu 2018 AlN')]
    ax.plot([455], [la[0]['k_equiv']], 'v', color=COL['AlN'], ms=10, mec='k', mew=0.8, zorder=7,
            label='AlN  Liu 2018 single-crystal rings, TE00: 3.5 dB/cm @455 nm and 8.0 dB/cm @390 nm (Gamma ~1.01, EMode)')
    ax.plot([390], [la[1]['k_equiv']], 'v', color=COL['AlN'], ms=10, mec='k', mew=0.8, zorder=7)
    liu_all = {(q['wavelength_nm'], q['label'].split(' nm ')[1].split(' (')[0]): q for q in pts if q['label'].startswith('Liu 2018 AlN ring')}
    liu_all[(455.0, '0.8 um wide')] = [q for q in pts if q['label'].startswith('Liu 2018 AlN ring TE00 455')][0]
    liu_all[(390.0, '0.8 um wide')] = [q for q in pts if q['label'].startswith('Liu 2018 AlN ring TE00 390 nm (500')][0]
    mod = [q for q in pts if q['label'].startswith('SURVEY MODEL')]
    for m in mod:
        key = (m['wavelength_nm'], m['label'].split(' nm ')[1])
        lq = liu_all.get(key)
        if lq is None:
            continue
        ax.plot([m['wavelength_nm']] * 2, [lq['k_equiv'], m['k_equiv']], '-', color=COL['AlN'], lw=0.9, alpha=0.7, zorder=4)
        ratio = m['bound_dB_per_cm'] / lq['bound_dB_per_cm']
        ax.annotate(f"x{ratio:.1f}", (m['wavelength_nm'], m['k_equiv']), xytext=(5, 0), textcoords='offset points', fontsize=7.5, color=COL['AlN'], va='center')
        if lq['label'] not in ('Liu 2018 AlN ring TE00 455 nm (500x800 nm, SiO2 clad)', 'Liu 2018 AlN ring TE00 390 nm (500x800 nm, SiO2 clad)'):
            ax.plot([lq['wavelength_nm']], [lq['k_equiv']], 'v', color=COL['AlN'], ms=6, mec='k', mew=0.5, zorder=7)
    ax.plot([m['wavelength_nm'] for m in mod], [m['k_equiv'] for m in mod], 's', mfc='white', color=COL['AlN'], ms=8, mew=1.6, zorder=8,
            label="AlN  SURVEY pump-loss model at Liu's geometry (open square) vs Liu measured (triangle); xN = model/Liu")
    uv = [q for q in pts if q['label'].startswith('Uviquity')][0]
    ax.plot([447], [uv['k_equiv']], 'v', mfc='white', color=COL['AlN'], ms=9, mew=1.6, zorder=7,
            label='AlN  Uviquity SPIE 2026 MOCVD film 2.7 dB/cm @447 nm (prism coupling; Gamma ~1 not computed)')
    pa = [q for q in pts if q['label'].startswith('Crystal IS')]
    ax.plot([q['wavelength_nm'] for q in pa], [q['k_equiv'] for q in pa], 'D', mfc='white', color=COL['AlN'], ms=8, mew=1.6, zorder=7,
            label='AlN  Crystal IS patent: bulk PVT crystal, CLAIMED alpha < 10 cm-1 @230, < 15 @220 nm (claim, not peer reviewed)')
    uvf = [q for q in pts if q['label'].startswith(('Shin 2021', 'Stegmaier 2014'))]
    ax.plot([q['wavelength_nm'] for q in uvf], [q['k_equiv'] for q in uvf], 'v', mfc='white', color=COL['AlN'], ms=9, mew=1.6, zorder=7,
            label='AlN  typical films in the UV: Shin 2021 ring 60.4 dB/cm @369.5 nm; Stegmaier 2014 poly-AlN 650 dB/cm @400 nm (Gamma not computed)')
    bk = [q for q in pts if q['label'].startswith('Bickermann')]
    ax.plot([q['wavelength_nm'] for q in bk], [q['k_equiv'] for q in bk], '--', color=COL['AlN'], lw=2.0, zorder=5,
            label='AlN  Bickermann 2010 bulk PVT crystal, measured alpha <= 18 cm-1 over 220-380 nm (best material found; bulk, not a waveguide)')
    kl = [q for q in pts if q['label'].startswith('Klump')][0]
    ax.plot([230], [kl['k_equiv']], 'D', color=COL['AlN'], ms=8, mec='k', mew=0.8, zorder=7,
            label='AlN  Klump 2024 bulk PVT: lowest alpha(230 nm) = 35 cm-1 of 37 samples (typical 50-150)')
    tl = [q for q in pts if q['label'].startswith('Tillner')]
    ax.plot([q['wavelength_nm'] for q in tl], [q['k_equiv'] for q in tl], ':', color=COL['AlN'], lw=2.0, zorder=5,
            label='AlN  Tillner 2020 MOCVD film: flat 150-200 cm-1 over 245-400 nm (probably a measurement floor)')

    # ---- SiC: band edge
    ax.axvline(378, color=COL['SiC'], lw=2.0, ls='-.', zorder=3)
    ax.axvspan(195, 378, color=COL['SiC'], alpha=0.07, lw=0)
    ax.text(381, 2.2, '4H-SiC gap 3.26 eV: crystalline SiC absorbs at all shorter lambda;\nno 400-500 nm k or loss found (only 1064/1550 nm data)',
            fontsize=8, color=COL['SiC'], va='top')

    # ---- AlGaN
    for q in [q for q in pts if q['material'] == 'AlGaN']:
        ax.plot([q['wavelength_nm']], [q['k_equiv']], 'v', mfc='white', color=COL['AlGaN'], ms=10, mew=1.8, zorder=7)
    ax.plot([], [], 'v', mfc='white', color=COL['AlGaN'], ms=10, mew=1.8,
            label='AlGaN  Al0.69 ring 785 nm 2.5 dB/cm; Al0.69 slab ~630 nm 2.3 dB/cm; n-doped Al0.65 slab ~280 nm 22-26 dB/cm (free-carrier dominated); Gamma not computed')

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
    leg = ax.legend(fontsize=6.9, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.07 if TALL else -0.09), ncol=1)
    json.dump([t.get_text() for t in leg.get_texts()], open(os.path.join('materials', 'loss_chart_legend.json'), 'w', encoding='utf-8'), indent=1)
    fig.tight_layout(rect=(0, 0.03 if TALL else 0.035, 0.93, 1))
    out = os.path.join('runs', 'loss_overview_literature_tall.png' if TALL else 'loss_overview_literature.png')
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
