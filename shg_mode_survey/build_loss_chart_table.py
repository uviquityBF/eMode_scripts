"""Spreadsheet companion to runs/loss_overview_literature.png: one row per legend entry, with provenance.

Reads materials/loss_chart_legend.json (written by plot_loss_literature.py, so the rows track the chart's legend exactly),
materials/literature_loss_points.csv (every plotted point: loss, Gamma, bound, k), and the per-material sources_*.csv files on the
shared drive (DOI/URL, PDF name, location in paper). Writes runs/loss_overview_literature.xlsx (sheets: Legend, Points, Annotations,
How to read) and runs/loss_overview_literature.csv (the Legend sheet as plain CSV).

Rerun plot_loss_literature.py first, then:  python build_loss_chart_table.py
Conventions: dB/cm values are as published/measured; 'bound' = loss / Gamma (upper bound on core absorption); k_equiv = bound converted
with k = alpha*lambda/(4 pi), alpha = bound/4.3429. A legend entry with no metadata here is written with a NO METADATA flag, never skipped.
"""
import csv
import json
import math
import os
import re
import subprocess

import xlsxwriter

HERE = os.path.dirname(os.path.abspath(__file__))
LIT = r'G:\Shared drives\Corp Main\Engineering\Design & SHG Analysis (Brent)\eMode Modeling\Literature_Material_Loss'
GAUGE = r'G:\Shared drives\Corp Main\Engineering\LAB Studies\on Samples\GaugeLots'
OUT = os.path.join(HERE, 'runs', 'loss_overview_literature')


SLIDE_PATH = os.path.join(LIT, 'SiN', 'UVMedico_PW2026_HighConfinementBlue_slide.png')
SLIDE_LOCAL = SLIDE_PATH if os.path.exists(SLIDE_PATH) else '(not saved yet - save the slide photo as ' + SLIDE_PATH + ')'


def k_of(dB_cm, lam_nm):
    return dB_cm / (10 / math.log(10) * 4 * math.pi / (lam_nm * 1e-9) / 100.0)


_src_cache = {}


def sources(folder):
    if folder not in _src_cache:
        rows = {}
        for f in os.listdir(os.path.join(LIT, folder)):
            if f.startswith('sources_') and f.endswith('.csv'):
                for r in csv.DictReader(open(os.path.join(LIT, folder, f), encoding='utf-8-sig', newline='')):
                    rows[r['id']] = dict(r, _file=f)
        _src_cache[folder] = rows
    return _src_cache[folder]


def pdf_doi(path):
    try:
        t = subprocess.run(['pdftotext', '-l', '2', path, '-'], capture_output=True, timeout=30).stdout.decode('utf-8', 'ignore')
    except Exception:  # noqa: BLE001
        return ''
    m = re.search(r'10\.\d{4,9}/[^\s"<>,;)]+', t)
    return ('https://doi.org/' + m.group(0).rstrip('.')) if m else ''


def S(folder, *ids, pdf=None, url=None):
    """Source info from sources_*.csv ids (and an explicit local pdf name); returns dict(cite, url, local, location)."""
    rows = [sources(folder)[i] for i in ids if i in sources(folder)]
    cite = ' | '.join(dict.fromkeys(r['citation'][:230] for r in rows))
    urls = list(dict.fromkeys(r.get('doi_or_url', '') for r in rows if r.get('doi_or_url') and not r['doi_or_url'].lower().startswith('same')))
    pdfs = [pdf] if pdf else list(dict.fromkeys((r.get('pdf_file') or r.get('source_file') or '') for r in rows))
    local = []
    for p in pdfs:
        p = p.split(';')[0].strip()
        full = os.path.join(LIT, folder, p)
        if p and os.path.exists(full):
            local.append(full)
            if not urls and not url:
                d = pdf_doi(full)
                if d:
                    urls.append(d + '  (DOI found in the PDF text)')
    if not local:
        lib = [r.get('source_file', '') for r in rows if r.get('source_file')]
        if lib:
            local.append('(in the technical-papers library, not the Literature_Material_Loss tree) ' + ' ; '.join(dict.fromkeys(lib)))
    if url:
        urls.append(url)
    loc = ' | '.join(dict.fromkeys(r.get('location_in_paper', '') for r in rows if r.get('location_in_paper')))[:300]
    return dict(cite=cite, url=' ; '.join(urls), local=' ; '.join(local), location=loc)


def load_points():
    return list(csv.DictReader(open(os.path.join(HERE, 'materials', 'literature_loss_points.csv'), encoding='utf-8')))


PTS = load_points()


def agg(pred):
    sel = [p for p in PTS if pred(p['label'], p)]
    if not sel:
        return dict(n=0)

    def rng(key, fmt='{:.3g}'):
        raw = [p[key] for p in sel if p[key] not in ('', 'nan')]
        try:
            v = [float(x) for x in raw]
        except ValueError:
            return '; '.join(dict.fromkeys(raw))
        if not v:
            return ''
        lo, hi = min(v), max(v)
        return fmt.format(lo) if abs(lo - hi) < 1e-12 * max(1, abs(lo)) else f'{fmt.format(lo)} - {fmt.format(hi)}'
    return dict(n=len(sel), wl=rng('wavelength_nm', '{:g}'), loss=rng('wg_loss_dB_per_cm'), gamma=rng('gamma_used', '{:.3f}'),
                bound=rng('bound_dB_per_cm'), k=rng('k_equiv', '{:.2e}'),
                gsrc=' | '.join(dict.fromkeys(p['gamma_source'] for p in sel))[:300],
                note=' | '.join(dict.fromkeys(p['note'] for p in sel if p['note']))[:400],
                where=' | '.join(dict.fromkeys(p['location'] for p in sel))[:200],
                kind=' / '.join(dict.fromkeys(p['kind'] for p in sel)))


def curve_k(fn, lams=(225, 450)):
    """Fill wavelength/k/bound columns for a line from a k(lambda) callable (nm -> k, or None if undefined)."""
    out = [(l, fn(l)) for l in lams]
    out = [(l, k) for l, k in out if k is not None]
    dbc = lambda l, k: k * (10 / math.log(10) * 4 * math.pi / (l * 1e-9) / 100.0)
    return dict(wl=', '.join(f'{l:g}' for l, _ in out), k='; '.join(f'{l:g} nm: {k:.2e}' for l, k in out),
                bound='; '.join(f'{l:g} nm: {dbc(l, k):.3g}' for l, k in out), loss='(material k, not a loss)', gamma='n/a')


def _interp(xs, ys):
    import numpy as np
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    return lambda l: (float(np.interp(l, xs, ys)) if xs.min() <= l <= xs.max() else None)


def curve_data():
    import numpy as np
    import build_assumptions_report as bar
    d = bar.precompute_dispersion_data()
    lam = d['lam_core']
    c = {}
    m = d['aln_meas']
    c['aln'] = curve_k(_interp(m['wavelength_nm'], m['k_o']), (225, 250))
    c['sin'] = curve_k(_interp(lam, d['sinx_k']))
    c['tio2'] = curve_k(_interp(lam, d['tio2_k']))
    sc = json.load(open(os.path.join(HERE, 'materials', 'ScAlN_Baumler2019_sellmeier_fits.json')))['fits']
    c['bau'] = {k: curve_k(lambda l, k=k: bar.eval_k(sc[k]['emode_equation_complex'], l)) for k in ('0.23', '0.32', '0.41')}
    raw = open(os.path.join(LIT, 'TiO2', 'RII_Siefke2016_TiO2_nk_data.txt'), encoding='utf-8').read().split('data: |')[1].splitlines()
    tab = np.array([[float(v) for v in ln.split()[:3]] for ln in raw if ln.strip() and ln.split()[0][0].isdigit()])
    c['siefke'] = curve_k(_interp(tab[:, 0] * 1000.0, tab[:, 2]), (350, 400, 450))
    c['stud'] = curve_k(lambda l: 1.28e5 * math.exp((1239.842 / l - 3.684) / 0.1672) * 100 * l * 1e-9 / (4 * math.pi), (400, 450, 633))
    nk = list(csv.DictReader(open(os.path.join(HERE, 'materials', 'ScAlN_NanxiLi_SPIE2026_nk.csv'), newline='')))
    c['nanxi'] = {pct: curve_k(_interp([float(r['wavelength_nm']) for r in nk if int(r['sc_percent']) == pct],
                                       [float(r['k']) for r in nk if int(r['sc_percent']) == pct]), (225, 450, 635)) for pct in (0, 10, 20, 30)}
    z = [p for p in PTS if p['label'].startswith('Corato')][0]
    k461 = float(z['k_equiv'])
    c['urbach'] = curve_k(lambda l: k461 * math.exp(5.07 * (1239.842 / l - 1239.842 / 461.0)), (400, 450, 461, 532))
    return c


def has(*words):
    return lambda lab, p: all(w in lab for w in words)


# --------------------------------------------------------------------------------------------------------------------------
# One entry per legend row, keyed by a snippet found in the legend text. Fields: material, element, quantity, how, split, interp,
# caveat, pts (predicate -> filled from the points CSV), src (S(...)), repo, plus optional overrides (wl, loss, gamma, bound, k, gsrc).
SCI = dict(zip(('SiN', 'TiO2', 'ScAlN', 'AlN', 'AlGaN', 'TFLN'), ('SiN', 'TiO2', 'ScAlN', 'AlN', 'AlGaN', 'TFLN')))
E = []


def add(key, **kw):
    E.append(dict(key=key, **kw))


add('(faded) AlN k_o', material='AlN', element='thin faded line', quantity='k_o, our AlN film AM187-LT6 (ellipsometry)',
    how='Measured ordinary-axis k of our own AlN film from spectroscopic ellipsometry; part of the ORIGINAL overview chart, kept faded for context.',
    split='n/a (material k)', interp='Material absorption of our film; k floor of the ellipsometry fit near 1e-6 is a fit limit.',
    caveat='Internal measurement; the raw ellipsometry file is not in the literature folders.',
    src=dict(cite='Uviquity internal ellipsometry, sample AM187-LT6', url='', local='', location=''),
    repo='build_assumptions_report.precompute_dispersion_data()["aln_meas"]; materials/ (AlN dispersion)')
add('(faded) SiNx Beliaev', material='SiN', element='thin faded line', quantity='k of SiNx (Beliaev fit), original chart',
    how='Ellipsometric k(lambda) from the Beliaev SiNx fit used in the original chart; context only.', split='n/a (material k)',
    interp='Ellipsometry; k below ~1e-3 is a model tail.', caveat='From the original chart, not re-derived.',
    src=S('SiN', 'SiN01a', pdf='Beliaev -- Silicon_nitride_thin_films_1_.pdf'),
    repo='build_assumptions_report.precompute_dispersion_data()["sinx_k"]')
add('(faded) TiO2 Siefke', material='TiO2', element='thin faded line', quantity='k of ALD TiO2 (Siefke fit), original chart',
    how='Ellipsometric k from the Siefke 2016 ALD TiO2 fit, as in the original chart; context only.', split='n/a (material k)',
    interp='Ellipsometry; tail below ~1e-3 unresolved.', caveat='Original-chart curve; the new tabulated Siefke curve is the solid TiO2 line.',
    src=S('TiO2', 'T07'), repo='build_assumptions_report.precompute_dispersion_data()["tio2_k"]')
add('(faded) ScAlN Baumler', material='ScAlN', element='thin faded lines (3)', quantity='k of Al(1-x)Sc(x)N, Baumler 2019 fits for x = 0.23, 0.32, 0.41',
    how='Digitized k(E) from Baumler et al. J. Appl. Phys. 126, 045715 Fig. (k resolution ~0.008), then fitted with a damped Sellmeier model; k set to 0 below the transparency limit.',
    split='n/a (material k)', interp='Ellipsometric; sub-gap k is a forced fit tail (zero), not a measurement.',
    caveat='Used by the survey for the three ScAlN loss cases. The 0.23/0.32/0.41 compositions are not identical to Nanxi Li\'s 20/30 %.',
    src=S('ScAlN', 'N01', pdf='Optical constants and band gap of wurtzite Al1−xScxNAl2O3prepared by magnetron sputter epitaxy for scandiumconcentrations up to x = 0.41.pdf'),
    repo='materials/digitize_baumler.py -> ScAlN_Baumler2019_nk_digitized.csv; materials/fit_baumler_sellmeier.py -> ScAlN_Baumler2019_sellmeier_fits.json')
add('SiN  Corato-Zanarella', material='SiN', element='filled triangles (5 wavelengths)', quantity='film absorption of LPCVD SiN (their extracted bulk value), TE 4 um ring',
    how='Authors extracted bulk film absorption from a ring-width series (total loss vs width, intercept = absorption); values 2.4/1.2/0.20/0.060/0.0362 dB/cm at 461-780 nm; Gamma = 1 because the authors already de-rate by eta_abs = 1.0025.',
    pts=has('Corato'), split='Absorption (their width-series fit) vs scattering (width-dependent part); value is the width-independent part.',
    interp='UPPER bound on core absorption (top/bottom-wall scattering assumed zero).',
    caveat='Optica Open preprint numbers vs published Opt. Express 32, 5718 differ slightly (780 nm: 0.0362 published vs 0.02 preprint).',
    src=S('SiN', 'SiN01a', 'SiN01b', pdf='Corato-Zanarella -- oe-32-4-5718.pdf'), repo='plot_loss_literature.py (cz list); materials/literature_gamma.csv')
add('SiN  Urbach extrapolation', material='SiN', element='dashed line', quantity='model: Urbach tail from their 461 nm value, slope 5.07 /eV',
    how='k(lambda) = k_461 * exp(5.07 * (E - E_461)) with the band-fluctuation slope from Corato-Zanarella\'s fit; k_461 from the 461 nm point.',
    split='n/a (model of absorption)', interp='Model extrapolation, NOT a measurement.', caveat='Single-parameter extrapolation outside the fitted range.',
    src=S('SiN', 'SiN01b', pdf='CoratoZanarella_2023_AbsorptionScatteringLimitsVisible_OpticaOpenPreprint.pdf'), repo='plot_loss_literature.py (lam_u, k461)')
add('SiN  Chauhan 2020/22', material='SiN', element='filled triangles (450 nm spiral, 461 nm ring)', quantity='total waveguide loss / Gamma, TE, 20 nm LPCVD core',
    how='Measured total loss 0.08 dB/cm (450 nm, 2 m spiral) and 0.09 dB/cm (461 nm ring, Qi 9.5e6) divided by Gamma = 0.108 / 0.103 from our EMode run (n_core 2.10 assumed).',
    pts=lambda lab, p: lab.startswith('Chauhan') and 'photothermal' not in lab, split='Not separated: total loss includes scattering (upper bound).',
    interp='UPPER bound on core absorption; the thin core puts ~90 % of the power in the oxide, so dividing by Gamma ~0.1 inflates the bound 10x.',
    caveat='Gamma depends on the assumed core index; the authors quote 0.065 (power-type) which would raise the bound ~1.6x.',
    src=S('SiN', 'SiN02', 'SiN11', pdf='Chauhan 2022__oe-30-5-6960.pdf', url='https://doi.org/10.1364/OE.448938'), repo='gamma_for_literature.py; materials/literature_gamma.csv')
add('SiN  Chauhan 2022: photothermal', material='SiN', element='filled diamond', quantity='measured ABSORPTION (photothermal) at 674 nm',
    how='Authors\' direct photothermal absorption 0.17 dB/m, divided by Gamma = 0.044 from our EMode run (n_core 2.05 assumed).', pts=has('photothermal'),
    split='Absorption only (photothermal measures absorption directly).', interp='Close to an actual absorption number, not just an upper bound.',
    caveat='Only at 674 nm; no photothermal data at 450 nm.', src=S('SiN', 'SiN11', pdf='Chauhan 2022__oe-30-5-6960.pdf', url='https://doi.org/10.1364/OE.448938'),
    repo='gamma_for_literature.py')
add('SiN  Morin 2021, 24 nm core, 2.8', material='SiN', element='large filled triangle', quantity='total loss / Gamma, TE, 24 nm core, 2.8 um wide, 450 nm',
    how='Cutback loss 0.22 dB/cm divided by Gamma = 0.146 (our EMode, n_core 2.05 assumed).', pts=has('Morin', '2.8 um'),
    split='Not separated (sidewall scattering still included).', interp='UPPER bound.', caveat='Morin et al. is filed locally as "Chang2021"; Gamma assumed-index dependent.',
    src=S('SiN', 'SiN12', pdf='Chang2021 -- optica-8-5-755.pdf'), repo='gamma_for_literature.py')
add('SiN  ... 0.8 um wide', material='SiN', element='small filled triangles (450 nm 0.8 um; 405 nm)', quantity='total loss / Gamma, TE, Morin 24 nm core',
    how='0.35 dB/cm (0.8 um wide, 450 nm) and 0.93 dB/cm (405 nm) divided by EMode Gamma.', pts=lambda lab, p: lab.startswith('Morin') and '2.8 um' not in lab,
    split='Not separated.', interp='UPPER bound; narrower guide has more sidewall scattering.', caveat='Same as above.',
    src=S('SiN', 'SiN12', pdf='Chang2021 -- optica-8-5-755.pdf'), repo='gamma_for_literature.py')
add('SiN  PECVD best: Sacher', material='SiN', element='square markers (TE filled, TM open)', quantity='total loss / Gamma, PECVD SiN 135 nm core, 483 nm (466-500 nm average)',
    how='Wafer 2 (PECVD): TE <= 4.1, TM <= 2.8 dB/cm band averages, divided by EMode Gamma (0.69 TE / 0.47 TM, n_core 1.90 assumed): both ~6 dB/cm.', pts=has('Sacher'),
    split='Not separated.', interp='UPPER bound.', caveat='PECVD stack; LPCVD wafer in the same paper was worse.',
    src=S('SiN', 'SiN08', pdf='Sacher et al -- oe-27-26-37400.pdf'), repo='gamma_for_literature.py')
add('SiN  UVMedico slide (PW 2026): 7 vendor', material='SiN', element='triangles (14: 7 vendors x 2 wavelengths)', quantity='total slab-mode loss of 7 vendors\' SiN films, 447 and 519 nm',
    how='Read by eye from the right-hand bar chart of a slide photographed at Photonics West 2026; user states these are unpatterned slab modes, so Gamma = 1.', pts=has('UVMedico slide vendor'),
    split='Not separated (slab: no sidewalls, so loss = film absorption + volume scattering).', interp='Tight upper bound on film absorption (Gamma = 1).',
    caveat='Read from a photo (+-1 dB/cm); vendor identity and anneal state unknown; the 447/519 loss ratio of 4-11x implies an absorption-like spectrum. NOT data from Loft et al.',
    src=dict(cite='UVMedico/UVL slide "High confinement waveguides in the blue", Photonics West 2026 (photo supplied by user 2026-11-17)', url='',
             local=SLIDE_LOCAL, location='right chart, vendors A-G'), repo='plot_loss_literature.py (UVMedico block)')
add('SiN  Loft 2026 (Opt. Lett.): 115 nm', material='SiN', element='light-green triangles (447/519/636 nm)', quantity='measured slab loss, 115 nm LPCVD Si3N4, NOT annealed, TE (Metricon prism coupling)',
    how='Dashed un-annealed reference lines of Fig. 2 read by eye (3.3/1.0/0.4 dB/cm); divided by Gamma = 0.76/0.69/0.57, our analytic 3-layer slab calculation (n 2.045/2.025/2.005 from their Fig. 3, SiO2, air).',
    pts=has('Loft 2026 115'), split='Total includes simulated roughness scattering of ~1.5 / 1.2 / 0.7 dB/cm (their Fig. 4a); the rest is absorption-like.',
    interp='UPPER bound on core absorption.', caveat='Eye-reading of Fig. 2 (2-sigma bands about +-0.5-1 dB/cm); one vendor, one stack.',
    src=S('SiN', pdf='UVMedico_Annealing_Stoichiometric_Si3N4.pdf', url='https://doi.org/10.1364/OL.596082 (DOI as given by the user, not verified)').copy() | dict(
        cite='Loft, Gardner, Gravesen, Tonning, Stanton, Volet, Ulsig, Opt. Lett. 51(8), 2332 (2026) - annealing of LPCVD Si3N4 in the visible', location='Fig. 2, Fig. 4'),
    repo='plot_loss_literature.py (LOFT block); SiN_notes.md on the shared drive')
add('SiN  Loft 2026: anneal-induced', material='SiN', element='light diamonds (447/519/636 nm)', quantity='ANNEAL-INDUCED absorption change after 975 C (scattering subtracted, confinement-scaled)',
    how='Authors\' text value 11.1 +- 1.48 dB/cm at 447 nm; 519 (4.5) and 636 nm (2.0) read by eye from Fig. 4b. Gamma = 1 because the authors already scaled by the modal confinement.',
    pts=has('Loft 2026 anneal'), split='Absorption only (modelled scattering already removed).', interp='Increase in film absorption caused by annealing, NOT total loss; lambda exponent ~5.',
    caveat='Delta, not an absolute loss. Mechanism unresolved per the authors.',
    src=S('SiN', pdf='UVMedico_Annealing_Stoichiometric_Si3N4.pdf', url='https://doi.org/10.1364/OL.596082 (DOI as given by the user, not verified)').copy() | dict(
        cite='Loft et al., Opt. Lett. 51(8), 2332 (2026)', location='Sec. 3C text; Fig. 4b'), repo='plot_loss_literature.py (LOFT block)')
add('AlN  OUR GL04 as-grown', material='AlN', element='large filled triangles (3)', quantity='cutback propagation-loss SLOPES of our own c-plane AlN-on-sapphire waveguides, 350 nm wide, TM, PECVD SiO2 clad, as-grown',
    how='Per-device-mean linear fit of P2P insertion loss vs length (group 5, 0.3-0.7 cm, two 180-degree bends), 10 devices; loss = -10 log10(throughput) + 4.86 dB. 450 nm 11/9: 26.0 +- 4.2; 532 nm 11/10: 17.3 +- 4.6; 635 nm 11/10: 7.8 +- 3.7 dB/cm. Gamma = 0.94/0.90/0.84 core power fraction from our EMode run at 350 nm width.',
    pts=has('OUR GL04'), split='Not separated in the measurement; refit of the survey model attributes ~22-25 dB/cm to a width-independent floor and ~1-4 dB/cm to sidewall scattering.',
    interp='UPPER bound on core absorption (includes sidewall scattering, interface and cladding contributions).',
    caveat='Slopes have +-4 dB/cm error; 532 nm 11/5 session excluded (internally inconsistent); the nominal group-5 lengths are assumed.',
    src=dict(cite='Uviquity GL04 AM171 SD01 gauge-lot cutback, sessions 2026-10-30 .. 2026-11-10', url='', location='sheets "P2P Loss - All" / "Cutback Analysis"',
             local=os.path.join(GAUGE, r'GL04\AM171\SD01\Higher WL Loss') + r'\GL04 AM171 SD01 P2P Loss WL=450nm.xlsx ; ...WL=532nm (rpt).xlsx ; ...WL=635nm (rpt).xlsx (+ raw images in the subfolders)'),
    repo='validate_survey_loss_vs_gl04.py; runs/gl04_validation.csv; loss_model.CASES')
add('AlN  OUR GL03 post-anneal', material='AlN', element='large open triangle', quantity='cutback slope of our GL03 (annealed) AlN waveguide, 450 nm, post-anneal + re-polish',
    how='11/9 session slope 19.8 +- 6.1 dB/cm from 3 usable devices (id5.1, 5.3, 5.4 over 0.5-0.7 cm; id5.2 excluded); Gamma assumed equal to GL04 (not computed).', pts=has('OUR GL03'),
    split='Not separated.', interp='Weak upper bound (open marker: Gamma not computed).',
    caveat='Only a 0.2 cm baseline; replicate images differ by up to 6 dB; paired pre->post change (-8 dB) is length-independent, so the anneal effect on propagation is NOT demonstrated.',
    src=dict(cite='Uviquity GL03 AM172 SD01 gauge-lot cutback (pre-anneal 2026-03-30; post-anneal/polish 2026-07-20, 2026-11-09)', url='', location='P2P Loss xlsx',
             local=os.path.join(GAUGE, r'GL03\AM172\SD01\Higher WL Loss') + r'\GL03 AM172 SD01 P2P Loss WL=450nm.xlsx'), repo='plot_loss_literature.py (OUR block)')
add('SiN  UVMedico slide: patterned', material='SiN', element='open cross', quantity='absorption floor (width-independent alpha_a) of a width fit, patterned high-confinement SiN waveguides, 447 nm',
    how='Plateau of the alpha_s + alpha_a fit at 2-2.5 um width read from the left chart (about 9.5 dB/cm); alpha_s alone falls to ~1 dB/cm at 2.5 um. Gamma assumed ~1 from the "high confinement" title (not computed).',
    pts=has('UVMedico slide: width-independent') or (lambda lab, p: 'floor' in lab and 'UVMedico' in lab), split='Fit separates scattering alpha_s (width dependent) from absorption alpha_a (the plateau).',
    interp='Upper bound on core absorption; open marker (Gamma not computed).', caveat='Read from a photo; wavelength confirmed 447 nm by the user; not data from Loft et al.',
    src=dict(cite='UVMedico/UVL slide "High confinement waveguides in the blue", Photonics West 2026 (photo)', url='', local=SLIDE_LOCAL, location='left chart "First iteration loss breakdown"'),
    repo='plot_loss_literature.py (UVMedico block)')
add('TiO2  Siefke 2016 ALD film, tabulated', material='TiO2', element='solid line', quantity='k of ALD TiO2 from tabulated ellipsometry (solid where k >= 1e-3)',
    how='Tabulated n,k (Siefke et al. 2016, refractiveindex.info entry) at 350 nm film; plotted solid where k >= 1e-3.', split='n/a (material k)', interp='Ellipsometry; resolvable absorption.',
    caveat='Strong absorption edge near 3.2 eV; blue tail below ~1e-3 is not resolved.', src=S('TiO2', 'T07'), repo='plot_loss_literature.py (TiO2 block)')
add('TiO2  ... dotted', material='TiO2', element='dotted line', quantity='k of ALD TiO2 below ~1e-3 (dispersion-model tail)', how='Same tabulated data; part below 1e-3 shown dotted.',
    split='n/a', interp='NOT a measurement: tail of the dispersion model, unresolved by the film.', caveat='Do not use as an absorption value.', src=S('TiO2', 'T07'), repo='plot_loss_literature.py')
add('TiO2  Studenyak 2018', material='TiO2', element='dashed line', quantity='model: Urbach absorption edge of sputtered TiO2, extrapolated',
    how='alpha = alpha0 exp((E - E0)/Eu) with alpha0 = 1.28e5 /cm, E0 = 3.684 eV, Eu = 167 meV; converted to k.', split='n/a (model of absorption)',
    interp='Extrapolation of an edge fit to ~2 eV below the gap; overshoots Bradley\'s measured 633 nm slab loss by ~15x.', caveat='Not a measurement at 450 nm.',
    src=S('TiO2', 'T08'), repo='plot_loss_literature.py (TiO2 Urbach block)')
add('TiO2  Bradley 2012', material='TiO2', element='open triangle', quantity='measured planar-film loss, amorphous sputtered TiO2, 633 nm, TE (prism coupled)',
    how='Film propagation loss 0.12 dB/mm = 1.2 dB/cm; Gamma ~1 assumed for the 250 nm slab (not computed).', pts=has('Bradley'), split='Not separated (film loss incl. scattering).',
    interp='Upper bound (open marker).', caveat='633 nm only; no TiO2 value exists in the 450 nm band; the paper\'s waveguides were 26 dB/cm.',
    src=S('TiO2', pdf='J Bradley -- oe-20-21-23821.pdf'), repo='plot_loss_literature.py')
add('ScAlN  van Deurzen', material='ScAlN', element='horizontal blue line', quantity='ellipsometry k "below detection limit", Al0.89Sc0.11N (MBE) on GaN, 193-1690 nm',
    how='Authors report no measurable absorption; the line sits at the 1e-3 detection limit.', pts=has('van Deurzen'), split='n/a',
    interp='Limit of the technique (k < 1e-3 = ~1200 dB/cm), not an absorption value.', caveat='Uninformative as a bound.', src=S('ScAlN', 'S09'), repo='plot_loss_literature.py')
add('ScAlN  Li (A*STAR/IME)', material='ScAlN', element='four blue curves (0/10/20/30 % Sc)', quantity='k(lambda) from tabulated ellipsometry, sputtered polycrystalline ScAlN on fused silica',
    how='Tabulated n,k (Fig. 1c,d of the SPIE 2026 paper, supplied as xlsx) 145-1700 nm; solid where k >= 1e-3, dotted below. k(225 nm) = 0.084/0.154/0.222/0.721; k(450 nm) = 2.3e-3/2.8e-3/6.1e-3/1.21e-2; edge (k < 0.1) at 221/237/256/283 nm.',
    split='n/a (material k)', interp='Edge position and Sc trend are usable; sub-gap k is an UPPER bound (ellipsometry fit tail).',
    caveat='Polycrystalline sputtered film; 450 nm k would be thousands of dB/cm, far above any waveguide measurement.',
    src=S('ScAlN', 'S07', 'S08', pdf='NanxiLi_SPIE2026_S08_Fig1c,d --- nk of IME ScAlN films on FS sub.xlsx'), repo='materials/ScAlN_NanxiLi_SPIE2026_nk.csv; plot_loss_literature.py')
add('AlN  Liu 2018 single-crystal', material='AlN', element='filled triangles (+ small ones, no own legend row)', quantity='intrinsic loss of single-crystal MOCVD AlN rings, TE00, 500x800 nm, SiO2 clad',
    how='Qint-derived 3.5 dB/cm (455 nm, Qint 398k) and 8.0 dB/cm (390 nm, Qint 210k); Gamma = 1.01 from our EMode run (isotropic n_o, substrate approximated as SiO2). Small triangles = 0.4 um TE00 and 0.6 um TM00 rings at 390 nm scaled from Qint (approximate).',
    pts=lambda lab, p: lab.startswith('Liu 2018 AlN ring') and p['material'] == 'AlN', split='Authors: scattering-limited (not separated).', interp='UPPER bound on core absorption.',
    caveat='Different (e-beam) process from ours; the small triangles are approximate.', src=S('AlN', 'W01', 'W02', 'W03', 'W04'), repo='gamma_for_literature.py; materials/literature_gamma.csv')
add('AlN  SURVEY pump-loss model', material='AlN', element='open squares (model) joined to Liu triangles', quantity='survey pump-loss model evaluated at Liu\'s geometries (current model)',
    how='EMode-native roughness scattering (sigma 2.5/0.3 nm, Lc 50/10 nm) + interface absorption (140 dB/cm in-layer); xN = model / Liu.', pts=lambda lab, p: p['kind'] == 'model',
    split='Scattering and absorption listed separately in the note column of the Points sheet.', interp='MODEL, not data: over-predicts Liu\'s TE rings by 2-5x.',
    caveat='Superseded by the GL04 refit (loss_model.CASES).', src=dict(cite='Survey model (this repo)', url='', local='', location=''),
    repo='validate_survey_loss_vs_liu.py; runs/liu_validation.csv')
add('AlN  Uviquity SPIE 2026', material='AlN', element='open triangle', quantity='measured film loss, our MOCVD AlN film, 447 nm (prism coupling)',
    how='2.7 dB/cm slab loss including surface scattering (0.5 nm rms), single wafer, short fit domain; Gamma ~1 assumed (not computed).', pts=has('Uviquity SPIE'),
    split='Not separated (includes surface scattering).', interp='Upper bound (open marker); the value itself is "in doubt" per the author (single wafer, small fit domain).',
    caveat='Our own paper; 2.7 dB/cm vs the ~26 dB/cm GL04 waveguide slope is the unexplained gap.', src=S('AlN', 'W05'), repo='plot_loss_literature.py')
add('AlN  Crystal IS patent', material='AlN', element='open diamonds (2)', quantity='CLAIMED absorption coefficient of bulk PVT AlN: alpha < 10 /cm @230 nm, < 15 /cm @220 nm',
    how='Summary-level claims in patent US 11,555,256 converted to dB/cm (x4.343); Gamma = 1 (bulk).', pts=lambda lab, p: p['kind'] == 'claim_bound', split='n/a (bulk absorption)',
    interp='A claimed limit, not a measured value; not peer reviewed.', caveat='No example data readable.', src=S('AlN', 'A6'), repo='plot_loss_literature.py')
add('AlN  typical films in the UV', material='AlN', element='open triangles (2)', quantity='measured waveguide loss of typical AlN films in the UV: Shin 2021 ring 60.4 dB/cm @369.5 nm; Stegmaier 2014 polycrystalline 650 dB/cm @400 nm',
    how='Published loss values; Gamma not computed (plotted at 1, true bound higher).', pts=lambda lab, p: p['kind'] == 'bound_open' and p['material'] == 'AlN' and ('Shin' in lab or 'Stegmaier' in lab),
    split='Not separated.', interp='Open markers = optimistic upper bounds.', caveat='Library papers; Stegmaier is polycrystalline.',
    src=S('AlN', 'AL05', 'AL07'), repo='plot_loss_literature.py')
add('AlN  Bickermann 2010', material='AlN', element='dashed line (two end points)', quantity='measured absorption coefficient of bulk PVT AlN, alpha <= 18 /cm over 220-380 nm',
    how='Measured alpha 12-18 /cm; the best value 18 /cm used across 220-380 nm, converted to dB/cm (x4.343 = 78 dB/cm); Gamma = 1.', pts=lambda lab, p: p['kind'] == 'bulk_measured' and 'Bickermann' in lab,
    split='n/a (bulk absorption)', interp='Measured bulk absorption of the best crystal found; not a waveguide.', caveat='Unreliable below ~220 nm.', src=S('AlN', 'AL20', 'L05'), repo='plot_loss_literature.py')
add('AlN  Klump 2024', material='AlN', element='filled diamond', quantity='measured alpha(230 nm) = 35 /cm, best of 37 PVT AlN samples (typical 50-150 /cm)',
    how='35 /cm x 4.343 = 152 dB/cm; Gamma = 1 (bulk).', pts=lambda lab, p: p['kind'] == 'bulk_measured' and 'Klump' in lab, split='n/a (bulk absorption)',
    interp='Measured bulk absorption.', caveat='Best sample of 37.', src=S('AlN', 'AL21', 'L01'), repo='plot_loss_literature.py')
add('AlN  Tillner 2020', material='AlN', element='dotted line', quantity='absorption of MOCVD AlN/sapphire films, flat 150-200 /cm over 245-400 nm (175 used)',
    how='175 /cm x 4.343 = 760 dB/cm; Gamma = 1.', pts=lambda lab, p: p['kind'] == 'film_floor', split='n/a (film absorption)',
    interp='Probably a measurement floor of the technique, not a true absorption.', caveat='Upper bound only.', src=S('AlN', 'A3'), repo='plot_loss_literature.py')
add('AlGaN  Al0.69 ring', material='AlGaN', element='open gold triangles (3)', quantity='measured losses of AlGaN: Al0.69 ring at 785 nm (2.5 dB/cm TE); Al0.69 planar slab ~630 nm (2.3 dB/cm TE0 minimum); n-doped Al0.65 slab ~280 nm (22-26 dB/cm)',
    how='Published loss values (Gundogdu: ring from Qint, slab by prism coupling; Floyd: LED attenuation 5-6 /cm x 4.343, 24 dB/cm plotted). Gamma not computed (plotted at 1; the ring paper quotes 90 % of power above the AlN-sapphire interface, which is not the AlGaN-core fraction).',
    pts=lambda lab, p: p['material'] == 'AlGaN', split='Not separable (ring: interface + sidewall + absorption); the 280 nm slab is free-carrier dominated by the authors own model.',
    interp='Open markers = weak upper bounds on core absorption; far from 450 nm (785/630/280 nm).', caveat='Slab loss at ~630 nm rises toward the blue (value at 450 nm not read); added to the chart 2026-11-17 (it was a legend row with no markers before).',
    src=S('AlGaN', 'AG01', 'AG02', 'AG03'), repo='plot_loss_literature.py (AlGaN block)')
add('LiNbO3  bulk undoped congruent, ordinary', material='TFLN/LN', element='solid brown line', quantity='bulk absorption of undoped congruent LiNbO3 (WGRAS), ordinary, 390-800 nm',
    how='Leidinger 2015 data file (figshare Data File 5), alpha converted to k; Gamma = 1 (bulk).', pts=lambda lab, p: lab.endswith('ordinary') and 'extra' not in lab and p['kind'] == 'bulk_absorption',
    split='n/a (bulk)', interp='Upper limit (Fe2+-impurity set).', caveat='Bulk crystal, not a waveguide.', src=S('TFLN', 'T01', 'T02', 'T03', 'T04'), repo='plot_loss_literature.py (LiNbO3 block)')
add('LiNbO3  ... extraordinary', material='TFLN/LN', element='dashed brown line', quantity='same, extraordinary', how='Same data file, extraordinary polarization.',
    pts=lambda lab, p: 'extraordinary' in lab and p['kind'] == 'bulk_absorption', split='n/a (bulk)', interp='Upper limit.', caveat='Bulk crystal.',
    src=S('TFLN', 'T01', 'T02', 'T03', 'T04'), repo='plot_loss_literature.py')
add('LiNbO3  Desiatov 2019', material='TFLN/LN', element='open triangle', quantity='measured TFLN ring loss at 637 nm, 0.06 dB/cm (scattering-limited)',
    how='Reported loss 0.06 dB/cm; Gamma not computed (plotted at 1).', pts=None, wl='637', loss='0.06', gamma='1 (assumed)', bound='0.06', k='%.2e' % k_of(0.06, 637),
    split='Authors: scattering-limited.', interp='Upper bound (open marker).', caveat='TFLN is out of scope for the survey; reference only.',
    src=S('TFLN', 'T06'), repo='plot_loss_literature.py')
add('SH loss USED', material='(survey assumption)', element='black bar at 215-235 nm', quantity='calibrated flat SH-band absorption used by the survey: 100 dB/cm',
    how='geometry.SH_ABSORPTION_CALIBRATED_DB_PER_CM = 100 (flat, confinement-weighted), chosen to calibrate against device output; shown as the k-equivalent of 100 dB/cm.',
    pts=None, wl='215-235', loss='100', gamma='1 (as k-equivalent)', bound='100', k='%.2e-%.2e' % (k_of(100, 215), k_of(100, 235)),
    split='Absorption assumption; SH scattering is added separately (EMode native).', interp='ASSUMPTION, not measured. Study band 43 / 100 / 300 / 870 dB/cm.',
    caveat='Never measured on our film at 225 nm.', src=dict(cite='Survey assumption (PLAN.md 2026-10-12)', url='', local='', location=''),
    repo='geometry.py (SH_ABSORPTION_CALIBRATED_DB_PER_CM); PLAN.md')
add('pump loss model', material='(survey model)', element='black bar at 430-470 nm', quantity='survey pump-loss model: in-layer growth-interface absorption alpha0 = 140 dB/cm',
    how='Sum of four interface mechanisms in survey_config (dislocations 20, C 35, Si 35, O 50 dB/cm in-layer alpha0); shown at 450 nm as k-equivalent.',
    pts=None, wl='430-470', loss='140 (in-layer alpha0)', gamma='1 (as k-equivalent)', bound='140', k='%.2e' % k_of(140, 450),
    split='Absorption part of the model; scattering added separately.', interp='MODEL INPUT (current model), superseded for pump loss by loss_model case gl04_asgrown.',
    caveat='The in-layer value is not the modal loss (the mode only overlaps the first ~50 nm).', src=dict(cite='Survey model (this repo)', url='', local='', location=''),
    repo='survey_config.py (pump_absorption_mechanisms); loss_model.py')

ANNOT = [
    ('4H-SiC gap 3.26 eV note', 'SiC', 'vertical purple line at 376-380 nm', 'No 400-500 nm k found for SiC; only 1064/1550 nm data. Gap from de Oliveira 2002 Table 1.',
     S('SiC', 'S11')),
    ('SiN absorption edges (LPCVD 275 nm, PECVD-LF 320 nm, PECVD-MF/HF 400 nm)', 'SiN', 'green dotted vertical lines',
     'Band-edge positions carried over from the original chart (not re-derived).', dict(cite='original overview chart', url='', local='', location='')),
    ('LiNbO3 gap 3.8 eV', 'TFLN/LN', 'brown dotted line at 326 nm', 'Optical band gap of LiNbO3 (Zanatta 2022; also Schwesyg).',
     S('TFLN', pdf='Zanatta -- The optical bandgap of lithium niobate (LiNbO3) and its dependence with temperature  ResPhys2022_LiNbO3.pdf')),
    ('Typical ellipsometry resolving limit k ~ 1e-3 .. 2e-3', 'all', 'grey dotted horizontal line at 2e-3', 'Quoted by Corato-Zanarella (0.002); below this, ellipsometric k is a fit tail.',
     S('SiN', 'SiN01a')),
    ('Shaded bands: SH 215-235 nm, pump 430-470 nm', 'all', 'orange / blue vertical bands', 'Survey SH window and pump band.', dict(cite='survey_config.py', url='', local='', location='')),
]

COLS = ['#', 'Legend text (as on chart)', 'Material', 'Plot element', 'What the number is', 'Wavelength(s) nm', 'Reported value(s) dB/cm',
        'Gamma used', 'Gamma source / method', 'Final bound dB/cm (loss/Gamma)', 'k equivalent', 'Scatter vs absorption split', 'How it was arrived at',
        'Interpretation', 'Caveats', 'Source citation', 'Location in source', 'Source URL / DOI', 'Local copy of source', 'Repo file(s) / script', 'n points']


def build():
    legend = json.load(open(os.path.join(HERE, 'materials', 'loss_chart_legend.json'), encoding='utf-8'))
    cv = curve_data()

    def combo(d, tag):
        return dict(wl=next(iter(d.values()))['wl'], loss='(material k, not a loss)', gamma='n/a',
                    k=' | '.join(f'{tag} {kk}: ' + v['k'] for kk, v in d.items()), bound=' | '.join(f'{tag} {kk}: ' + v['bound'] for kk, v in d.items()))
    curves = {'(faded) AlN k_o': cv['aln'], '(faded) SiNx Beliaev': cv['sin'], '(faded) TiO2 Siefke': cv['tio2'],
              '(faded) ScAlN Baumler': combo(cv['bau'], 'x='), 'SiN  Urbach extrapolation': cv['urbach'],
              'TiO2  Siefke 2016 ALD film, tabulated': cv['siefke'], 'TiO2  ... dotted': cv['siefke'], 'TiO2  Studenyak 2018': cv['stud'],
              'ScAlN  Li (A*STAR/IME)': combo(cv['nanxi'], '% Sc =')}
    rows = []
    for i, text in enumerate(legend, 1):
        e = next((x for x in E if x['key'] in text), None)
        if e is None:
            rows.append([i, text, '?', '', 'NO METADATA - add an entry in build_loss_chart_table.py'] + [''] * (len(COLS) - 5))
            continue
        a = agg(e['pts']) if e.get('pts') else dict(n=0)
        a = {**a, **curves.get(e['key'], {})}
        src = e['src']
        rows.append([i, text, e['material'], e['element'], e['quantity'], e.get('wl', a.get('wl', '')), e.get('loss', a.get('loss', '')),
                     e.get('gamma', a.get('gamma', '')), e.get('gsrc', a.get('gsrc', '')), e.get('bound', a.get('bound', '')), e.get('k', a.get('k', '')),
                     e['split'], e['how'], e['interp'], e['caveat'] + (' | points note: ' + a['note'] if a.get('note') else ''),
                     src['cite'], src.get('location') or a.get('where', ''), src['url'], src['local'], e['repo'], a.get('n', '')])
    return legend, rows


def main():
    legend, rows = build()
    wb = xlsxwriter.Workbook(OUT + '.xlsx')
    hdr = wb.add_format({'bold': True, 'bg_color': '#DDE6F3', 'text_wrap': True, 'valign': 'top', 'border': 1})
    wrap = wb.add_format({'text_wrap': True, 'valign': 'top'})
    flag = wb.add_format({'text_wrap': True, 'valign': 'top', 'bg_color': '#FDE9E7'})
    widths = [4, 46, 10, 22, 38, 14, 18, 12, 30, 16, 16, 34, 60, 34, 46, 44, 30, 40, 50, 36, 8]

    def sheet(name, cols, data, w, link_cols=()):
        ws = wb.add_worksheet(name)
        for j, c in enumerate(cols):
            ws.write(0, j, c, hdr)
            ws.set_column(j, j, w[j] if j < len(w) else 20)
        for r, row in enumerate(data, 1):
            bad = any('NO METADATA' in str(c) or 'NO MARKER' in str(c) for c in row)
            for j, v in enumerate(row):
                f = flag if bad else wrap
                s = str(v) if v is not None else ''
                if j in link_cols and s.startswith('http'):
                    ws.write_url(r, j, s.split(' ')[0], string=s, cell_format=f)
                else:
                    ws.write(r, j, s, f)
        ws.freeze_panes(1, 2)
        ws.autofilter(0, 0, len(data), len(cols) - 1)
        return ws
    sheet('Legend', COLS, rows, widths, link_cols=(17,))
    pcols = ['material', 'label', 'kind', 'wavelength_nm', 'wg_loss_dB_per_cm', 'gamma_used', 'gamma_source', 'bound_dB_per_cm', 'k_equiv', 'source', 'location', 'note']
    sheet('Points', pcols, [[p[c] for c in pcols] for p in PTS], [10, 56, 14, 10, 12, 8, 40, 14, 12, 40, 30, 60])
    ann = [[a[0], a[1], a[2], a[3], a[4]['cite'], a[4]['url'], a[4]['local']] for a in ANNOT]
    sheet('Annotations', ['Item', 'Material', 'Chart element', 'What it is', 'Source', 'URL / DOI', 'Local copy'], ann, [44, 10, 26, 60, 40, 40, 50])
    notes = [
        ['Triangles (v)', 'Measured waveguide/film loss divided by Gamma (core power fraction): UPPER BOUND on core absorption. Scattering is NOT subtracted unless stated (Loft anneal-induced row).'],
        ['Filled vs open', 'Filled = Gamma computed by EMode / analytic slab / the authors. Open = Gamma not computed, plotted at 1, so the true bound is higher.'],
        ['Squares', 'Open pink squares = survey MODEL at Liu geometries (not data). Sacher squares = data (TE filled, TM open).'],
        ['Diamonds', 'Bulk-crystal absorption (Bickermann, Klump, patent claim) or directly measured absorption (Chauhan photothermal, Loft anneal-induced).'],
        ['Lines', 'Solid = tabulated; dotted = unresolved tail (below ~1e-3); dashed = extrapolation/model.'],
        ['Material-k rows (lines)', 'For rows that are k(lambda) curves, "Final bound dB/cm" is the k value converted to dB/cm at the listed wavelengths (k * 1.2128e6 * 450/lambda), i.e. what a core of that k would absorb; there is no Gamma or waveguide loss behind them.'],
        ['Conversions', 'dB/cm = 4.3429 * alpha[1/cm]; k = alpha*lambda/(4 pi). Right-hand axes show dB/cm at 225 nm (SH) and 450 nm (pump); each is exact only at its own wavelength.'],
        ['Where the numbers live', 'runs/loss_overview_literature.png (+ _tall.png); materials/literature_loss_points.csv (every plotted point); this workbook.'],
        ['Shared-drive sources', LIT],
        ['Regenerate', 'python plot_loss_literature.py ; python build_loss_chart_table.py'],
    ]
    sheet('How to read', ['Topic', 'Explanation'], notes, [22, 120])
    wb.close()
    with open(OUT + '.csv', 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows)
    bad = [r for r in rows if 'NO METADATA' in str(r[4])]
    print('wrote', OUT + '.xlsx and .csv;', len(rows), 'legend rows;', len(bad), 'without metadata')
    for r in rows:
        print(r[0], '|', r[2], '|', r[5], '|', r[6], '|', r[7], '|', r[9], '|', str(r[17])[:55], '|', 'LOCAL' if r[18] else '-', '|', r[20])


if __name__ == '__main__':
    main()
