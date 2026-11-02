"""Run the survey's own pump-loss model (EMode-native roughness scattering + interface-absorption mechanisms from
survey_config.SETTINGS) at the geometry of Liu et al., Optica 5, 1279 (2018) and compare with their measured ring losses.

Liu: single-crystal MOCVD AlN on c-plane sapphire, 0.5 um thick, ring width 0.4 / 0.6 / 0.8 um, ~80 deg sidewall, SiO2 top clad,
ring radius 30 um (bend ignored here: straight-waveguide model). Measured (all TE00 unless noted):
    390 nm, 0.8 um wide : 8.0 dB/cm   (Qint 210 k, text)
    455 nm, 0.8 um wide : 3.5 dB/cm   (Qint 398 k, text)
    390 nm, 0.4 um wide : ~20.2 dB/cm (Qint 83 k, scaled from the 0.8 um value by Qint ratio; agent read 20.4 from Fig. 3d)
    390 nm, 0.6 um wide TM00: ~9.6 dB/cm (Qint 175 k, scaled the same way; approximate)
The model uses the survey's own settings unchanged (sigma = [2.5, 0.3] nm, Lc = [50, 10] nm, same absorption mechanisms) -- the point
is to see how far the survey's PUMP-band loss is from a published good device, not to tune it. Substrate sapphire, top clad SiO2 2.5 um.
Usage: python validate_survey_loss_vs_liu.py [case ...]      -> runs/liu_validation.csv
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geometry as geo  # noqa: E402
import emode_helpers as pmh  # noqa: E402
import absorption_model as am  # noqa: E402
import survey  # noqa: E402
import survey_config  # noqa: E402

OUT = os.path.join(HERE, 'runs', 'liu_validation.csv')
FIELDS = ['case', 'pol_wanted', 'wavelength_nm', 'width_nm', 'height_nm', 'n_eff', 'te_fraction', 'scattering_dB_per_cm',
          'absorption_dB_per_cm', 'total_dB_per_cm', 'liu_dB_per_cm', 'liu_note', 'roughness_rms', 'correlation_length']
CASES = {
    'TE_390_w800': dict(lam=390.0, w=800.0, pol='TE', liu=8.0, note='text: Qint 210k'),
    'TE_455_w800': dict(lam=455.0, w=800.0, pol='TE', liu=3.5, note='text: Qint 398k'),
    'TE_390_w400': dict(lam=390.0, w=400.0, pol='TE', liu=20.2, note='scaled from Qint 83k'),
    'TM_390_w600': dict(lam=390.0, w=600.0, pol='TM', liu=9.6, note='scaled from Qint 175k (approx.)'),
}
H, ANGLE = 500.0, 10.0   # ~80 deg slope from horizontal = 10 deg from vertical (survey's sidewall_angle convention)


def run_case(name, c, cfg):
    g = geo.make_geometry('ridge', {'h_core': H, 'w_core': c['w'], 'sidewall_angle': ANGLE,
                                    'substrate_height': 1500.0, 'topclad_height': 2500.0})
    em = pmh.launch_session(f'liu_{name}', clear='all')
    try:
        g.build(em, cfg['roughness_rms'], cfg['correlation_length'])
        em.settings(boundary_condition='0A', wavelength=c['lam'], x_resolution=cfg['resolution'],
                    y_resolution=cfg['resolution'], num_modes=1)
        n, te = survey.solve(em, 'liu', wavelength=c['lam'], num_modes=8, max_effective_index=0,
                             x_resolution=cfg['resolution'], y_resolution=cfg['resolution'])
        x, y, modes = survey.fetch_fields(em)
        order = np.argsort(-n.real)
        want = (lambda j: te[j] > 0.5) if c['pol'] == 'TE' else (lambda j: te[j] <= 0.5)
        i = next(j for j in order if want(j))
        mask = g.core_mask(x, y)
        scat = survey.native_scattering(em, int(i), g.scatter_shapes)
        absn = sum(am.compute_mechanism_losses(mask, x[1] - x[0], y, modes[i]['Sz'], cfg['pump_absorption_mechanisms']).values())
        print(f"  {name}: n_eff={n[i].real:.4f} te={te[i]:.3f} scat={scat / 100:.3f} abs={absn / 100:.3f} dB/cm", flush=True)
        return dict(case=name, pol_wanted=c['pol'], wavelength_nm=c['lam'], width_nm=c['w'], height_nm=H, n_eff=float(n[i].real),
                    te_fraction=float(te[i]), scattering_dB_per_cm=scat / 100.0, absorption_dB_per_cm=absn / 100.0,
                    total_dB_per_cm=(scat + absn) / 100.0, liu_dB_per_cm=c['liu'], liu_note=c['note'],
                    roughness_rms=str(cfg['roughness_rms']), correlation_length=str(cfg['correlation_length']))
    finally:
        try:
            em.close(save=False)
        except Exception:  # noqa: BLE001
            pass


def main(names):
    cfg = survey_config.SETTINGS
    existing = list(csv.DictReader(open(OUT, newline=''))) if os.path.exists(OUT) else []
    for name in names:
        print('===', name, flush=True)
        try:
            row = run_case(name, CASES[name], cfg)
        except Exception as e:  # noqa: BLE001
            print('  FAILED:', repr(e), flush=True)
            continue
        existing = [r for r in existing if r['case'] != name] + [{k: row.get(k, '') for k in FIELDS}]
        with open(OUT, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(existing)
    print('wrote', OUT)


if __name__ == '__main__':
    main(sys.argv[1:] or list(CASES))
