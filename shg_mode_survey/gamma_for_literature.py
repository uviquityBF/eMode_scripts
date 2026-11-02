"""Core-absorption weight Gamma for published waveguide geometries, from EMode.

A published waveguide loss L_wg [dB/cm] only bounds the *material* absorption through
    L_wg >= Gamma * L_core    ->    L_core <= L_wg / Gamma
where Gamma = (modal power loss) / (core material power loss). Two definitions are computed from the exported fields:
  gamma_abs_pert  = c eps0 n_core Int_core |E|^2 dA / Int Sz dA   (first-order perturbation: the weight that multiplies the core's
                    absorption coefficient to give modal absorption -- the one to use for bounds; ~1 for a uniform wave)
  gamma_power_frac = fraction of the Poynting flux Sz inside the core (the repo's sp.power_fraction_in; what 'confinement' papers
                    usually quote; differs from the above for weakly guided modes)
(EMode's own shape loss is deliberately not used: the repo found re-solving with loss set unreliable.)

Cases are straight-waveguide approximations of the published structures (ring bend ignored), with constant core/clad
indices. Gamma depends only weakly on the exact index, but see CASES for the values used and change them to taste.
Usage (from shg_mode_survey/): python gamma_for_literature.py [case_name ...]   (default: all)
Writes materials/literature_gamma.csv (appends/replaces per (case, pol)).
"""
import csv
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'phase_matching_pipeline'))
import emode_helpers as pmh  # noqa: E402
sys.path.insert(0, HERE)
import survey  # noqa: E402

OUT = os.path.join(HERE, 'materials', 'literature_gamma.csv')
L_TEST_DB_PER_M = 1e4            # small core loss used as the probe [dB/m] (k ~ 1e-4)
FIELDS = ['case', 'pol', 'wavelength_nm', 'h_nm', 'w_nm', 'n_core', 'n_clad', 'n_eff', 'te_fraction',
          'gamma_abs_pert', 'gamma_power_frac', 'x_res', 'y_res', 'window_w', 'window_h', 'note']

# name: dict(wavelength, h, w, n_core, n_clad, sub_h, top_h, window_w, x_res, y_res, note)
CASES = {
    # Corato-Zanarella et al. (Optica Open preprint 2023): LPCVD SiN 275 nm x 4 um ring, SiO2 above/below; paper's Table S21 reports Gamma_core = 0.947 (TE)
    'CZ_275x4000_461': dict(wavelength=461.0, h=275.0, w=4000.0, n_core=2.10, n_clad=1.465, sub_h=2000.0, top_h=1500.0,
                            window_w=9000.0, x_res=25.0, y_res=10.0, note='paper Gamma=0.947 (Table S21), TE'),
    # Chauhan et al. CLEO 2020: 20 nm x 1.3 um SiN core, SiO2 clad; polarization not stated at 450 nm -> report TE and TM
    'Chauhan_20x1300_450': dict(wavelength=450.0, h=20.0, w=1300.0, n_core=2.10, n_clad=1.465, sub_h=3500.0, top_h=3500.0,
                                window_w=8000.0, x_res=40.0, y_res=5.0, note='Gamma not reported in paper; pol unknown'),
    'Chauhan_20x1300_450_fine': dict(wavelength=450.0, h=20.0, w=1300.0, n_core=2.10, n_clad=1.465, sub_h=3500.0, top_h=3500.0,
                                     window_w=8000.0, x_res=25.0, y_res=2.5, note='convergence check, finer grid'),
    # Chauhan CLEO 2020 second structure: 90 nm x 0.3 um
    'Chauhan_90x300_450': dict(wavelength=450.0, h=90.0, w=300.0, n_core=2.10, n_clad=1.465, sub_h=4000.0, top_h=4000.0,
                               window_w=9000.0, x_res=20.0, y_res=5.0, note='scattering-dominated 5 dB/cm structure'),
    # Smith et al. 2023 (LIGENTEC AN150): 150 nm x 800 nm SiN, TE
    'Smith_150x800_450': dict(wavelength=450.0, h=150.0, w=800.0, n_core=2.05, n_clad=1.465, sub_h=3000.0, top_h=3000.0,
                              window_w=8000.0, x_res=20.0, y_res=5.0, note='LIGENTEC-like; n_core assumed 2.05'),
    # Morin/Chang et al. Optica 8, 755 (2021): 24 nm Si3N4, 6 um / 2 um SiO2 clads, TE-only 0.8 um guide; core index not stated -> 2.05 assumed
    'Morin_24x2800_450': dict(wavelength=450.0, h=24.0, w=2800.0, n_core=2.05, n_clad=1.465, sub_h=3500.0, top_h=3500.0,
                              window_w=9000.0, x_res=40.0, y_res=5.0, note='cutback 0.22 dB/cm; n_core assumed'),
    'Morin_24x800_450': dict(wavelength=450.0, h=24.0, w=800.0, n_core=2.05, n_clad=1.465, sub_h=3500.0, top_h=3500.0,
                             window_w=8000.0, x_res=40.0, y_res=5.0, note='cutback 0.35 dB/cm; n_core assumed'),
    'Morin_24x800_405': dict(wavelength=405.0, h=24.0, w=800.0, n_core=2.07, n_clad=1.470, sub_h=3500.0, top_h=3500.0,
                             window_w=8000.0, x_res=40.0, y_res=5.0, note='cutback 0.93 dB/cm at 405 nm; n_core assumed'),
    # Sacher et al. Opt. Express 27, 37400 (2019), Wafer 2: PECVD SiN 135 nm, 340 nm wide, SiO2 clads; n_core not stated -> 1.90 assumed (PECVD)
    'Sacher_135x340_483': dict(wavelength=483.0, h=135.0, w=340.0, n_core=1.90, n_clad=1.465, sub_h=3500.0, top_h=3500.0,
                               window_w=8000.0, x_res=20.0, y_res=5.0, note='PECVD Wafer 2; avg loss 466-500 nm TE<=4.1 TM<=2.8 dB/cm; n_core assumed'),
    # Chauhan et al. Opt. Express 30, 6960 (2022): 20 nm LPCVD Si3N4, 6 um top / 15 um bottom SiO2, single TE mode; core index not stated -> 2.10 assumed.
    # paper's own confinement factors: 0.065 (461 nm, 1.3 um), 0.031 (674 nm, 2.3 um)
    'Chauhan22_20x1300_461': dict(wavelength=461.0, h=20.0, w=1300.0, n_core=2.10, n_clad=1.465, sub_h=3500.0, top_h=3500.0,
                                  window_w=8000.0, x_res=40.0, y_res=5.0, note='paper confinement 0.065; TE; n_core assumed'),
    'Chauhan22_20x2300_674': dict(wavelength=674.0, h=20.0, w=2300.0, n_core=2.05, n_clad=1.457, sub_h=4500.0, top_h=4500.0,
                                  window_w=10000.0, x_res=50.0, y_res=5.0, note='paper confinement 0.031; TE; n_core assumed'),
    # Liu et al. Optica 5, 1279 (2018): single-crystal MOCVD AlN on sapphire, 500 nm film, 800 nm wide ring, SiO2 clad. Isotropic n_o approximation
    # (AlN is uniaxial; TE00 mostly sees n_o). n_core ~ ordinary AlN index (2.17 at 455 nm, 2.21 at 390 nm); SiO2 clad. Substrate approximated as SiO2.
    'Liu18_AlN_500x800_455': dict(wavelength=455.0, h=500.0, w=800.0, n_core=2.17, n_clad=1.466, sub_h=2500.0, top_h=2500.0,
                                  window_w=6000.0, x_res=20.0, y_res=10.0, note='Liu 2018 3.5 dB/cm TE00; substrate approximated as SiO2'),
    'Liu18_AlN_500x800_390': dict(wavelength=390.0, h=500.0, w=800.0, n_core=2.21, n_clad=1.474, sub_h=2500.0, top_h=2500.0,
                                  window_w=6000.0, x_res=20.0, y_res=10.0, note='Liu 2018 8.0 dB/cm TE00; substrate approximated as SiO2'),
    # sanity: very large core -> Gamma should approach 1
    'sanity_big_core': dict(wavelength=450.0, h=3000.0, w=3000.0, n_core=2.10, n_clad=1.465, sub_h=2000.0, top_h=2000.0,
                            window_w=8000.0, x_res=40.0, y_res=40.0, note='Gamma -> 1 expected'),
}


def k0_per_m(lam_nm):
    return 2 * math.pi / (lam_nm * 1e-9)


def run_case(name, c):
    rows = []
    em = pmh.launch_session(f'gamma_{name}', clear='all')
    try:
        em.add_material(name='litcore', refractive_index_equation=f"{c['n_core']}+0*x", wavelength_unit='um')
        em.add_material(name='litclad', refractive_index_equation=f"{c['n_clad']}+0*x", wavelength_unit='um')
        em.settings(window_width=c['window_w'], window_height=c['h'] + c['sub_h'] + c['top_h'],
                    wavelength=c['wavelength'], x_resolution=c['x_res'], y_resolution=c['y_res'],
                    num_modes=8, max_effective_index=c['n_core'] + 0.01, boundary_condition='00')
        em.shape(name='Substrate', material='litclad', height=c['sub_h'])
        em.shape(name='core', material='litcore', height=c['h'], mask=c['w'], etch_depth=c['h'], sidewall_angle=0)
        em.shape(name='TopClad', material='litclad', height=c['top_h'], shape_type='conformal')
        fdm = em.FDM()
        n_eff = np.asarray(fdm['n_eff_tilde'])
        te = np.asarray(fdm['TE_fraction'], dtype=float)
        x, y, modes = survey.fetch_fields(em, ['Ex', 'Ey', 'Ez', 'Hx', 'Hy'])
        order = np.argsort(-n_eff.real)
        dx, dy = float(x[1] - x[0]), float(y[1] - y[0])
        for pol, sel in (('TE', lambda j: te[j] > 0.5), ('TM', lambda j: te[j] <= 0.5)):
            cand = [j for j in order if sel(j) and n_eff[j].real > c['n_clad'] + 1e-4]
            if not cand:
                rows.append(dict(case=name, pol=pol, note='no guided mode of this polarization'))
                continue
            j = cand[0]
            f = modes[j]
            I = np.abs(f['Ex']) ** 2 + np.abs(f['Ey']) ** 2 + np.abs(f['Ez']) ** 2
            X, Y = np.meshgrid(x, y)
            x0 = float((I * X).sum() / I.sum())
            y_mid = c['sub_h'] + c['h'] / 2.0
            mask = ((np.abs(X - x0) <= c['w'] / 2.0) & (np.abs(Y - y_mid) <= c['h'] / 2.0)).astype(float)
            sz = np.real(f['Ex'] * np.conj(f['Hy']) - f['Ey'] * np.conj(f['Hx']))
            g_S = float((sz * mask).sum() / sz.sum())
            # first-order absorption weight: alpha_mod / alpha_core = c eps0 n_core Int_core|E|^2 dA / Int Sz dA  (Sz as Re(ExHy*-EyHx*), SI)
            g_pert = float(299792458.0 * 8.8541878128e-12 * c['n_core'] * (I * mask).sum() / sz.sum())
            yc = float((I * Y).sum() / I.sum())
            print(f"     [{pol}] n_eff={n_eff[j].real:.5f} mask px={int(mask.sum())} (expect {c['w']*c['h']/dx/dy:.0f}) "
                  f"x0={x0:.0f} nm, y_centroid={yc:.0f} nm (core mid {y_mid:.0f})", flush=True)
            rows.append(dict(case=name, pol=pol, wavelength_nm=c['wavelength'], h_nm=c['h'], w_nm=c['w'],
                             n_core=c['n_core'], n_clad=c['n_clad'], n_eff=float(n_eff[j].real),
                             te_fraction=float(te[j]), gamma_abs_pert=g_pert, gamma_power_frac=g_S,
                             x_res=c['x_res'], y_res=c['y_res'], window_w=c['window_w'],
                             window_h=c['h'] + c['sub_h'] + c['top_h'], note=c['note']))
    finally:
        try:
            em.close(save=False)
        except Exception:  # noqa: BLE001
            pass
    return rows


def main(names):
    existing = list(csv.DictReader(open(OUT, newline=''))) if os.path.exists(OUT) else []
    for name in names:
        print(f'=== {name}', flush=True)
        try:
            rows = run_case(name, CASES[name])
        except Exception as e:  # noqa: BLE001
            print('  FAILED:', repr(e), flush=True)
            continue
        for r in rows:
            print('  ', {k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items() if k in ('pol', 'n_eff', 'te_fraction', 'gamma_abs_pert', 'gamma_power_frac', 'note')}, flush=True)
        existing = [e for e in existing if e['case'] != name] + [{k: r.get(k, '') for k in FIELDS} for r in rows]
        with open(OUT, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(existing)
    print('wrote', OUT)


if __name__ == '__main__':
    main(sys.argv[1:] or list(CASES))
