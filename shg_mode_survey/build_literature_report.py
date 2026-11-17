"""Rebuild runs/Literature_Loss_Report.docx from the saved 6 Nov 2026 base (materials/report_base_2026-11-06.docx) plus everything added since:
updated chart + summary, SiN (Loft, UVMedico), our own AlN cutback data (GL04/GL03), the refit and loss_model presets, TM00 vs TM10, planning
values, pending items and file locations. Idempotent: always starts from the base file.   Usage: python build_literature_report.py
"""
import copy
import csv
import os

import docx
from docx.shared import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, 'materials', 'report_base_2026-11-06.docx')
OUT = os.path.join(HERE, 'runs', 'Literature_Loss_Report.docx')
d = docx.Document(BASE)
body = d.element.body
orig = list(body)          # indices as listed when the base was inspected: 0 title ... 58 sectPr


def P(t):
    return d.add_paragraph(t)


def H(t, lvl):
    return d.add_heading(t, lvl)


def B(t, lead=None):
    p = d.add_paragraph(style='List Bullet')
    if lead:
        p.add_run(lead).bold = True
    p.add_run(t)
    return p


def table(header, rows, size=None):
    t = d.add_table(rows=1, cols=len(header))
    t.style = 'Light Grid Accent 1'
    for c, h in zip(t.rows[0].cells, header):
        c.text = h
    for r in rows:
        for c, v in zip(t.add_row().cells, r):
            c.text = str(v)
    if size:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(size)
    return t


def insert_before(ref, build):
    """Run build() (which appends content to the document) and move the new elements in front of `ref`."""
    before = set(body)
    build()
    for e in [e for e in body if e not in before]:
        ref.addprevious(e)


def set_text(el, text):
    p = docx.text.paragraph.Paragraph(el, d)
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)
    if p.runs:
        p.runs[0].text = text
    else:
        p.add_run(text)


def f3(x):
    try:
        return f'{float(x):.3g}'
    except ValueError:
        return x


# ---------------------------------------------------------------- title block, summary, chart
set_text(orig[1], 'Materials: SiN, TiO2, ScAlN, SiC, AlGaN, TFLN (LiNbO3), AlN. Written for Brent, as a read-later report of the intrinsic-loss study '
         '(updated 17 Nov 2026: our own GL04/GL03 AlN cutback data, SiN annealing and vendor data, the refit and loss-model presets, the TM00-vs-TM10 '
         'pump comparison). Not yet reviewed by anyone else. Nothing here has been run through the survey itself yet.')


def summary():
    H('Where things stand (17 Nov 2026)', 1)
    B(' 37 legend entries / 72 plotted points, now including our own GL04 and GL03 AlN cutback data, the Loft (Opt. Lett. 2026) SiN annealing paper, the '
      'UVMedico vendor SiN films, Nanxi Li\'s ScAlN k tables and AlGaN. A spreadsheet with one row per legend entry and full provenance (value, Γ, split, '
      'source, DOI/URL, local copy) is runs/loss_overview_literature.xlsx.', 'Chart and data.')
    B(' GL04 (as-grown) 350 nm-wide TM guide: 26 ± 4 dB/cm at 450 nm, 17 ± 5 at 532 nm, 8 ± 4 at 635 nm, i.e. a wavelength exponent of about 3.5 ± 1.5. '
      'Most of the 450 nm loss (about 22-25 dB/cm) is a width-independent floor; the sidewall term is small (a few dB/cm). Our own slab film (2.7 dB/cm) and '
      'Liu\'s rings (3.5 dB/cm) are about 10x lower, so the GL04 floor is not film absorption alone (interface, etch damage or cladding are the suspects).',
      'Our AlN.')
    B(' Only GL03 was annealed. Its group-5 data (4 devices, 0.2 cm baseline) cannot show the anneal effect on propagation loss: the pre-to-post change in '
      'total loss (-8 dB) does not grow with length, so it looks like the facet re-polish. "GL04 + anneal" has never been measured; the loss-model cases '
      'for it are projections.', 'Anneal.')
    B(' The survey model was too steep in width, too low in floor and flat in wavelength. Refit to GL04 (scattering x0.1, interface absorption x2.3, '
      'exponent 3.75) it reproduces the width series and the 450/532/635 nm slopes. The refit is stored as named presets in loss_model.py; the survey '
      'defaults are unchanged and the survey has not been re-run.', 'Loss model.')
    B(' Un-annealed 115 nm LPCVD Si3N4 slab: about 3.3 dB/cm at 447 nm (core bound about 4.3). Annealing above 900 C adds 11.1 dB/cm (absorption-like, '
      'exponent about 5). Seven vendor films: 4.5-19.5 dB/cm at 447 nm (median 9.5), probably annealed. Planning values: low 0.7-2.7 (best published '
      'thin-core bounds), central about 4, high about 15 dB/cm.', 'SiN.')
    B(' No TiO2 data exist at 450 nm (bracket about 1-140 dB/cm from Bradley\'s 633 nm film). ScAlN at 450 nm is unknown (about 3 dB/cm if AlN-like, up to '
      'thousands from Nanxi\'s fit tail); at 225 nm Sc >= 10-20 % is inside the absorption edge for both Nanxi and Baumler.', 'TiO2 and ScAlN.')
    B(' With the stored fields (140 of 280 refined AlN-ridge crossings), TM00 beats TM10 in all five loss cases by 1.5-2.1x (best 0.11 vs 0.053 %/W with the '
      'current model; 0.057 vs 0.036 with the as-grown refit). The SH-band loss assumption (43-300 dB/cm) matters far more than the pump mode.',
      'TM00 vs TM10 pump.')
    B(' No SH-band (225 nm) loss has been measured on any film; TFLN is out of scope; the EMode vs Payne-Lacey disagreement on the UV scattering '
      'exponent is unresolved; the ScAlN and TiO2 pump-band values rest on brackets, not data.', 'Still open.')


insert_before(orig[2], summary)
# chart picture (replace the old image) and caption
pic_par = docx.text.paragraph.Paragraph(orig[3], d)
for r in list(pic_par.runs):
    r._element.getparent().remove(r._element)
pic_par.add_run().add_picture(os.path.join(HERE, 'runs', 'loss_overview_literature_tall.png'), width=Inches(5.2))
set_text(orig[4], 'runs/loss_overview_literature_tall.png (a wide version and the per-legend-entry spreadsheet sit next to it). Symbols: filled triangle = upper '
         'bound on core absorption (waveguide loss / Γ) with Γ from EMode, an analytic slab, or the authors; open triangle = Γ not computed, plotted at '
         'Γ = 1 (the true bound is higher); square = PECVD (or the survey model, pink open square); diamond = bulk crystal or directly measured '
         'absorption; solid line = tabulated data; dotted = below instrument resolution; dashed = extrapolation or model. Pink triangles marked OUR are '
         'our own GL04/GL03 waveguides.')

# ---------------------------------------------------------------- extra key findings (before section 3)


def kf():
    B(' Loft et al. (Opt. Lett. 51, 2332, 2026; 115 nm LPCVD stoichiometric Si3N4): un-annealed slab loss about 3.3 / 1.0 / 0.4 dB/cm at 447 / 519 / 636 nm '
      '(TE); annealing above 900 C raises it (11.1 ± 1.5 dB/cm of added absorption at 447 nm after 975 C). The UVMedico slide (Photonics West 2026, not '
      'the same data) shows seven vendor SiN slab films at 4.5-19.5 dB/cm at 447 nm and 0.7-2.5 at 519 nm.', 'SiN, new data:')
    B(' GL04 as-grown cutback slopes (350 nm wide, TM): 26 / 17 / 8 dB/cm at 450 / 532 / 635 nm; GL03 post-anneal 20 ± 6 dB/cm at 450 nm (3 devices). '
      'See section 6c-6d.', 'AlN, our own waveguides:')
    B(' Gundogdu 2024 (Al0.69, ring at 785 nm 2.5 dB/cm; slab about 630 nm 2.3 dB/cm) and Floyd 2020 (n-Al0.65 slab, 280 nm, 22-26 dB/cm, free-carrier '
      'dominated) were added to the chart as open triangles; none is near 450 nm.', 'AlGaN:')


insert_before(orig[17], kf)

# ---------------------------------------------------------------- section 5 table: regenerate from the CSV (72 rows)
rows = []
for r in csv.DictReader(open(os.path.join(HERE, 'materials', 'literature_loss_points.csv'), encoding='utf-8')):
    rows.append([r['material'], r['label'][:70], r['wavelength_nm'], f3(r['wg_loss_dB_per_cm']), f3(r['gamma_used']), f3(r['bound_dB_per_cm']), f3(r['k_equiv'])])
insert_before(orig[29], lambda: table(['Material', 'Source', 'λ (nm)', 'Wg loss (dB/cm)', 'Γ', 'Bound (dB/cm)', 'k equiv'], rows, size=8))
body.remove(orig[28])
set_text(orig[27], 'From materials/literature_loss_points.csv (bound = waveguide loss / Γ; k equiv is the equivalent extinction coefficient). Every legend entry, '
         'with its source, location, DOI and local copy, is in runs/loss_overview_literature.xlsx.')

# ---------------------------------------------------------------- section 6 intro / stale paragraphs
set_text(orig[30], 'Status: the loss values below are proposals and projections. The survey itself has not been re-run; its defaults (current pump-loss model) '
         'are unchanged. The refit and its projections are available as named cases in loss_model.py (section 6f).')
t39 = docx.text.paragraph.Paragraph(orig[39], d).text
set_text(orig[39], t39.replace('Nothing in the survey has been changed.', 'At that point nothing in the survey had been changed (the loss-model wiring added later is described in 6f).'))
set_text(orig[40], 'Update: the recalibration proposed here was carried out against our own GL04 cutback data (sections 6c-6f) rather than Liu. The remaining '
         'open item from this list is a cutback or photothermal absorption measurement on our own film near 225 nm.')
txt = docx.text.paragraph.Paragraph(orig[49], d).text
cut = txt.index('Agreed next step') if 'Agreed next step' in txt else len(txt)
set_text(orig[49], txt[:cut] + 'The refit in section 6d addresses these three findings.')


# ---------------------------------------------------------------- new sections before "7. Pending"
def new_sections():
    # 6d ---------------------------------------------------------------
    H('6d. New cutback data (GL04 and GL03, 2026-11-17 workbooks) and a refit of the survey model', 1)
    P('Raw P2P Loss workbooks for GL04 (AM171 SD01: 450, 532, 635 nm and repeats) and GL03 (AM172 SD01) were read directly. Loss in dB = -10 log10(throughput) '
      '+ 4.86, with throughput = device counts / reference counts, both scaled by integration time; the reference is matched by timestamp. The slopes below are '
      'my refits (per-device means, all ten devices); Brent\'s charts, which use a best point per device, differ by up to 3 dB/cm (532 nm repeat: 17.3 vs 14.3).')
    table(['GL04 as-grown, 350 nm wide', 'Slope (dB/cm)', 'Intercept (dB)', 'Note'], [
        ('450 nm, 2026-05-26 (JD)', '29.6 ± 3.6', '15.5', 'as recorded'),
        ('450 nm, 2026-11-09', '26.0 ± 4.2', '16.2', 'chart (best point): 25.3 ± 4.2'),
        ('532 nm, 2026-11-05', '31.7 ± 6.1', '14.5', 'excluded: internally inconsistent with 11/10'),
        ('532 nm, 2026-11-10', '17.3 ± 4.6', '13.0', 'chart: 14.3 ± 3.1'),
        ('635 nm, 2026-10-30', '7.5 ± 5.0', '24.7', 'R2 0.24'),
        ('635 nm, 2026-11-10', '7.8 ± 3.7', '26.7', 'reproduces 10/30'),
    ])
    P('')
    B(' 450 nm (6 months apart) and 635 nm (two sessions) reproduce within error. The 11/5 532 nm run differs from 11/10 per device by +2.7 to +13 dB, '
      'not a constant offset (the two short devices at Tint 1000 differ by only 3 dB), so it is dropped from the exponent fit.', 'Reproducibility:')
    B(' Images of the same device differ by 1-2 dB (e.g. id5.0 at 450 nm: 35.1-37.8 dB across three images), as large as the fit residual (1.7-2.2 dB). '
      'Averaging three images per device would reduce the slope errors.', 'Repeatability limits the slopes:')
    B(' id5.0 sits about 4 dB above id5.5 (both nominally 0.7 cm) and id5.8 about 5 dB above id5.3 (0.6 cm) at every wavelength and run. Either the nominal '
      'lengths are off or those devices have defects; id5.8 has no length entry in the 635 nm sheet. To be checked against the GDS.', 'Systematic device offsets:')
    B(' Group-2 straights (0.3 cm, 350 nm wide) at 635 nm total 20.2 ± 1.1 dB (n = 11); group-5 0.3 cm devices total 26.6 dB, +6.4 dB. At 450 nm the same '
      'comparison is +1.8 dB (24.7 vs 22.9). The group-5 intercept is therefore coupling plus bend loss, with the two 180-degree bends costing about 1-2 dB at '
      '450 nm and 6-7 dB at 635 nm (a hypothesis consistent with bend radiation growing with wavelength). Implied coupling: about 14-15 dB at 450 nm, about 18 dB '
      'at 635 nm (assuming slope 7.5).', 'Intercepts are not coupling alone:')
    B(' From the three consistent sessions (26.0 / 17.3 / 7.8 dB/cm) a weighted fit gives p = 3.6 ± 1.3 (including the older 450 nm and both 635 nm '
      'sessions, 2.8 ± 0.9). This excludes a flat wavelength dependence (the survey model had a 450/635 ratio of 1.09 against about 3.8 measured).',
      'Wavelength exponent:')
    P('GL03 (annealed lot): only group 5, devices id5.1-5.4 (0.7/0.4/0.6/0.5 cm), with id5.2 an outlier, leaving three points over a 0.2 cm baseline. Replicate '
      'images differ by up to 6 dB and the slopes change sign depending on whether id5.2 is included, so GL03 gives neither a reliable slope nor an exponent. '
      'Brent\'s own charts (best point per device, excluding id5.2): 450 nm pre-anneal (3/30) 32.3 ± 7.2 dB/cm, post-anneal and re-polish (7/20) 20.0 ± 6.4, 11/9 '
      '19.8 ± 6.1; 532 nm 23.1 ± 3.5 and 28.6 ± 1.6; 635 nm 13.7 ± 6.5 and 12.6 ± 4.2 (532 nm intercepts of 3.7-7.2 dB are not trustworthy). '
      'Paired by device, the 450 nm total loss fell by 10.8 / 5.9 / 9.0 / 7.3 dB (0.4-0.7 cm) after the anneal and re-polish, a drop that does not grow with '
      'length (a propagation-loss reduction would), so most of it is length-independent (coupling or polish). The anneal\'s effect on propagation loss is not '
      'demonstrated by this data.')
    P('Refit of the survey\'s own scattering and interface-absorption terms (evaluated at the GL04 geometry, validate_survey_loss_vs_gl04.py) to seven '
      'numbers: the 450 nm straight-guide totals by width (coupling assumed 14.5 ± 1 dB) and the three 350 nm slopes. Profile ranges with delta chi2 < 1:')
    table(['Parameter', 'Best', 'Range', 'Meaning'], [
        ('Scattering scale (EMode native)', '0.1', '0 - 0.18', 'sidewall scattering is much smaller than the model had'),
        ('Interface absorption scale', '2.3', '2.1 - 2.4', 'width-independent floor of about 22-25 dB/cm'),
        ('Wavelength exponent p', '3.75', '3 - 5', 'applied to the absorption term'),
    ])
    P('')
    table(['Width (nm)', 'Measured at 450 nm', 'Survey model (old)', 'Refit'], [
        ('250', '29.5', '39.6', '30.4'), ('350', '27.9', '23.1', '27.0'), ('700', '25.7', '12.9', '24.8'), ('1200', '25.4', '11.5', '24.5')])
    P('')
    table(['350 nm wide', '450 nm', '532 nm', '635 nm'], [
        ('Measured (dB/cm)', '26.0 ± 4.2', '17.3 ± 4.6', '7.8 ± 3.7'), ('Survey model (old)', '23.1', '22.5', '21.2'), ('Refit (p = 3.75)', '27.0', '16.8', '9.8')])
    P('Caveats: seven numbers and three parameters; the 14.5 dB coupling is assumed; widths are nominal (the survey geometry uses the bottom width); the '
      'exponent matters little for the SHG survey (the pump stays near 450 nm) but matters for any multi-wavelength loss tool.')

    # 6e ---------------------------------------------------------------
    H('6e. SiN: annealing paper and vendor data', 1)
    P('Loft, Gardner, Gravesen, Tonning, Stanton, Volet, Ulsig, Opt. Lett. 51(8), 2332 (2026) (DOI as supplied by Brent, not verified; full text read). One '
      'vendor, 115 nm LPCVD stoichiometric Si3N4 on 3 um SiO2, bought un-annealed; 4 h N2 anneals at 450-1000 C; Metricon prism-coupled slab TE, with simulated '
      'roughness scattering (0.17 nm rms, Lc 107 nm) subtracted. Values read by eye from the figures except where stated.')
    table(['Quantity', '447 nm', '519 nm', '636 nm'], [
        ('Slab loss, not annealed (dB/cm)', '3.3 (TM 2.7)', '1.0', '0.4'),
        ('Simulated scattering (dB/cm)', '1.5', '1.2', '0.7'),
        ('Slab loss after 975 C (dB/cm)', '11', '4', '1.7'),
        ('Anneal-induced absorption (dB/cm)', '11.1 ± 1.5 (text)', '4.5', '2.0'),
        ('Γ of the 115 nm slab (computed, 3-layer TE0)', '0.76', '0.69', '0.57'),
        ('Core bound, not annealed (loss / Γ, dB/cm)', '4.3', '1.5', '0.7')])
    P('')
    P('Loss is unchanged within error up to about 900 C and rises sharply above, coinciding with film densification (thickness -4 nm, n +0.005). The mechanism '
      'is unresolved (impurity gettering is suggested). The anneal-induced absorption falls 5.5x from 447 to 636 nm (exponent about 5). Air-clad waveguides at '
      '445 nm (500-2000 nm wide) show 8-15 dB/cm before and 14-19 dB/cm after annealing. A relevant contrast with AlN: annealing helps GL03 AlN (or at least its '
      'facets) but hurts this Si3N4 above 900 C.')
    P('The UVMedico slide (Photonics West 2026; photo supplied by Brent, values read by eye, +-1 dB/cm) is not the same dataset. Right chart, seven vendors A-G, '
      'unpatterned slab modes (Γ = 1): 447 nm 16.5 / 11 / 4.5 / 7.5 / 9.5 / 19.5 / 6.5 dB/cm and 519 nm 1.5 / 1.5 / 0.7 / 0.8 / 1.5 / 2.5 / 1.2. The 447/519 '
      'ratio of 4-11x implies an absorption-like spectrum. Left chart: patterned high-confinement waveguides at 447 nm, loss vs width with a fit separating '
      'scattering from a width-independent absorption plateau of about 9.5 dB/cm (32 dB/cm at 530 nm, about 13 at 1-2 um). Anneal state of these films is not '
      'stated; the 4.5-19.5 dB/cm range looks like the annealed case.')
    P('Planning values for SiN core absorption at 450 nm: low 0.7-2.7 dB/cm (upper bounds from Chauhan 0.74-0.88, Morin 1.5-2.7, Corato-Zanarella 2.4; these '
      'divide 0.08-0.35 dB/cm of measured loss by Γ of about 0.1-0.15 and include scattering, so they are bounds on the best case), central about 4 (un-annealed '
      'LPCVD slab, bound 4.3), high about 15 (annealed above 900 C: 3.3 + 11).')

    # 6f ---------------------------------------------------------------
    H('6f. Shared loss-model module and named cases (loss_model.py)', 1)
    P('loss_model.py is one EMode-free module holding the post-processed loss terms, so the SHG survey and any later loss-vs-geometry/wavelength tool use the same '
      'code. Terms: native sidewall scattering (with a scale factor), interface absorption from absorption_model mechanisms (scale factor and optional wavelength '
      'exponent), and an optional volume (Rayleigh-like) scattering term C x Γ x (450/λ)^p, off by default. A self-test confirms that with no settings it '
      'reproduces the old survey total exactly. survey.py now calls it (the new loss_model key is excluded from geometry fingerprints, so existing results '
      'stay valid); the wiring has not been exercised with EMode.')
    table(['Case', 'Scattering scale', 'Absorption scale', 'Basis'], [
        ('current', '1', '1', 'the old survey model, unchanged'),
        ('gl04_asgrown', '0.1', '2.3', 'refit to GL04 (as-grown)'),
        ('gl04_asgrown_scat_hi', '0.3', '2.0', 'refit with more scattering allowed'),
        ('target_anneal_weak', '0.1', '1.84', 'projection for GL04 + anneal, floor x0.8 (sensitivity)'),
        ('target_anneal_central', '0.1', '1.15', 'projection for GL04 + anneal, floor x0.5 (sensitivity)')])
    P('')
    P('All presets act on the pump band only (SH scattering and absorption stay as in the survey). Only GL03 was annealed and GL04 is as-grown, so the two '
      'target_anneal cases are projections, not fits. The x0.5 rests on GL03 post-anneal straights (floor about 13.4 dB/cm with an assumed 13 dB coupling) against '
      'GL04 as-grown (about 25), which mixes lot and anneal effects; Brent expects GL04 + anneal to be at least as good as GL03 + anneal, which would make x0.5 '
      'the conservative end.')

    # 6g ---------------------------------------------------------------
    H('6g. TM00 versus TM10 pump (EMode-free re-evaluation of stored crossings)', 1)
    P('tm10_vs_tm00_loss_cases.py recomputes the pump loss of each refined AlN-ridge crossing (row1_ridge_v1) from its stored fields under each named case, '
      'keeps the stored SH loss but swaps the calibrated flat SH absorption for 43, 100 or 300 dB/cm, and recomputes the loss-limited peak efficiency. The '
      '"current" case reproduces the stored efficiencies to 1e-12. Only 140 of the 280 refined crossings have exports on this machine; the best TM00 and TM10 '
      'values in this subset equal the stored maxima over all 280 (0.111 and 0.053 %/W), so the winners under "current" are covered, but the other cases are '
      'only partly checked.')
    table(['Case', 'SH 43 dB/cm: TM00 / TM10', 'SH 100: TM00 / TM10', 'SH 300: TM00 / TM10'], [
        ('current', '0.387 / 0.127', '0.111 / 0.053', '0.0055 / 0.0024'),
        ('gl04_asgrown', '0.171 / 0.070', '0.057 / 0.036', '0.0047 / 0.0022'),
        ('gl04_asgrown_scat_hi', '0.196 / 0.081', '0.066 / 0.040', '0.0049 / 0.0023'),
        ('target_anneal_weak', '0.263 / 0.108', '0.078 / 0.049', '0.0053 / 0.0026'),
        ('target_anneal_central', '0.644 / 0.265', '0.143 / 0.094', '0.0065 / 0.0033')])
    P('')
    P('Best peak efficiency in %/W. TM00 wins every case; at SH 100 dB/cm the ratio is 2.1x (current) falling to 1.5x (target_anneal_central), because the '
      'refit makes pump loss largely mode-independent absorption (about 25 dB/cm for both). At SH 300 dB/cm everything collapses to about 0.005 %/W and TM01 '
      '(0.0063) edges out TM00 (0.0055) in the "current" case only. The best TM00 crossing is TM04 at 227.9 nm (NCE 4.8 %/W/cm2) and the best TM10 crossing is '
      'TM04 at 232.6 nm (NCE 2.3), so TM10 loses on overlap as well as loss. SH-mode identification at high order was uncertain in earlier runs. The SH-loss '
      'assumption spans about 40x in efficiency, far more than the choice of pump mode.')

    # 6h ---------------------------------------------------------------
    H('6h. Planning values for intrinsic / pump-band loss near 450 nm', 1)
    table(['Material', 'Low', 'Central', 'High', 'Basis and caveats'], [
        ('SiN core absorption (dB/cm)', '0.7-2.7', '~4', '~15', 'best published thin-core upper bounds / un-annealed LPCVD slab / annealed above 900 C; vendor films 4.5-19.5'),
        ('AlN waveguide, GL04 as-grown (dB/cm)', '22', '26', '30', 'cutback at 350 nm width, ±4; includes sidewall, interface and cladding; film slab 2.7 and Liu 3.5 are ~10x lower'),
        ('AlN, GL04 + anneal (dB/cm)', '~13', '~20', '~26', 'PROJECTION only (floor x0.5 / x0.8 / x1); anneal effect on propagation not demonstrated'),
        ('TiO2 (dB/cm)', '~1', '(none)', '~140', 'no data at 450 nm: Bradley 1.2 dB/cm at 633 nm scaled by 1-118x (Urbach ratio); my construction, not a measurement'),
        ('ScAlN, pump band (dB/cm)', '~3', '(none)', '3,400-7,600', 'low = AlN-like film; high = Nanxi Li 10-20 % Sc fit tail (upper bound only); Baumler fit is ~0 (forced)'),
        ('AlN, SH band 215-235 nm (dB/cm)', '43', '100', '300-870', 'assumption band (calibrated flat 100); nothing measured on our film')])
    P('')


insert_before(orig[50], new_sections)

# ---------------------------------------------------------------- 7. Pending and 8. File locations: replace
for i in (51, 52, 53, 54, 55, 57, 58):
    body.remove(orig[i])


def pending():
    B(' Decide the loss case(s) for the survey rerun (gl04_asgrown as the base; the two target_anneal cases as sensitivity), then run the loss-only study: '
      'existing geometries at 450 and 225 nm from stored fields, each result as low / central / high. Add the other wavelengths as new EMode solves '
      '(needs the wavelength list and whether TE is required).', 'Next runs:')
    B(' Slab prism-coupling measurement on a piece of the GL04 wafer itself at 450 and 635 nm; straight-guide groups at 532 and 635 nm on GL04 and GL03; three '
      'same-day repeats per device at one alignment; check the real group-5 device lengths against the GDS (the 5.0/5.5 and 5.3/5.8 offsets); a pre/post-anneal '
      'comparison with straights on the same lot; an SH-band (225 nm) absorption measurement.', 'Measurements that would most reduce uncertainty:')
    B(' The loss-model survey wiring has not been run with EMode; 140 of 280 refined crossings lack exports on this machine (re-run or find them on the other '
      'machine); the DOIs taken from PDF text and Loft\'s DOI need verifying; the UVMedico slide photo should be saved to the SiN folder; the AlGaN, TiO2 and ScAlN '
      'pump-band values remain brackets.', 'Housekeeping and verification:')
    B(' Why EMode and the Payne-Lacey slab model disagree on the UV scattering exponent (payne_lacey_explorer.ipynb, PayneLacey_Primer.md). Remaining AlN leads '
      'not in hand (Collazo 2012, Slack 2002, Irmscher 2013, Peters 2022, Hartmann 2016 full paper, Klump supplement, Dalmau 2020, Tanikawa 2026, Honda 2025) are in '
      'AlN/needs_access_*.md; the two patent PDFs are image-only and unread; Ratzsch (TiO2 ALD) is a scan with no text.', 'Open questions and unread material:')


insert_before(orig[56], pending)


def files():
    B(' loss_model.py, tm10_vs_tm00_loss_cases.py, validate_survey_loss_vs_gl04.py (+ runs/gl04_validation.csv), validate_survey_loss_vs_liu.py, '
      'plot_loss_literature.py, build_loss_chart_table.py, build_literature_report.py, gamma_for_literature.py, PayneLacey_Primer.md, payne_lacey_explorer.ipynb, '
      'survey.py and survey_config.py (loss-model wiring).', 'Repo (shg_mode_survey/) code:')
    B(' runs/loss_overview_literature.png and _tall.png, runs/loss_overview_literature.xlsx and .csv (one row per legend entry), runs/Literature_Loss_Report.docx, '
      'runs/tm10_vs_tm00_loss_cases.csv, materials/literature_loss_points.csv, materials/literature_gamma.csv, materials/loss_chart_legend.json, '
      'materials/ScAlN_NanxiLi_SPIE2026_nk.csv, materials/report_base_2026-11-06.docx (the base this report is rebuilt from).', 'Repo outputs and data:')
    B(' G:\\Shared drives\\Corp Main\\Engineering\\Design & SHG Analysis (Brent)\\eMode Modeling\\Literature_Material_Loss\\<material>\\ with sources_*.csv, '
      'needs_access_*.md, *_notes.md, considered_*.md and the PDFs (the AlN folder now also holds Shin 2021, Stegmaier 2014, Bickermann 2010, Klump 2024 and '
      'Lu 2018; SiN holds the Loft annealing paper).', 'Shared drive, literature:')
    B(' G:\\Shared drives\\Corp Main\\Engineering\\LAB Studies\\on Samples\\GaugeLots\\GL04\\AM171\\SD01\\Higher WL Loss and ...\\GL03\\AM172\\SD01\\Higher WL Loss '
      '(P2P Loss xlsx per wavelength, raw images in the subfolders).', 'Shared drive, our cutback data:')


insert_before(body[-1], files)     # before sectPr
d.save(OUT)
print('wrote', OUT)
