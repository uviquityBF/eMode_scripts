"""Run the survey's own pump-loss model (EMode-native roughness scattering + the interface-absorption mechanisms from
survey_config.SETTINGS, both UNCHANGED) at the geometry of the GL04 gauge lot and compare with the measured GL04 data.

GL04 (c-plane AlN on sapphire, PECVD SiO2 top clad): core height 350 nm, sidewall ~85 deg (= 5 deg from vertical, the survey's
sidewall_angle convention and default), groups of fixed-length guides at drawn width 250 / 350 / 700 / 1200 nm, TM (vertical E) mode.
Nominal widths are used as the ridge's w_core, which geometry.Ridge treats as the BOTTOM width -- if the drawn width is the top width
the true bottom width is ~60 nm larger. This is a read-only check: nothing is recalibrated.

Measured (shared drive: LAB Studies/on Samples/GaugeLots/GL04, P2P Loss xlsx, deck 'GL04 Loss Results'; as-measured, NOT annealed assumed unknown):
    450 nm, 350 nm wide : cutback slope 29.6 +/- 3.6 dB/cm (deck: 28-31)
    450 nm, 0.3 cm straight totals (dB): 250 nm 23.35, 350 nm 22.88, 700 nm 22.22, 1200 nm 22.11  (250 vs 700: ~3.8 dB/cm spread)
    635 nm, 350 nm wide : cutback slope 7.5 +/- 5.0 dB/cm (R^2 0.24), measured 5 months after the 450 nm data
Usage: python validate_survey_loss_vs_gl04.py [case ...]      -> runs/gl04_validation.csv
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

OUT = os.path.join(HERE, 'runs', 'gl04_validation.csv')
FIELDS = ['case', 'wavelength_nm', 'width_nm', 'height_nm', 'n_eff', 'te_fraction', 'guided_note', 'power_fraction_core',
          'scattering_dB_per_cm', 'absorption_dB_per_cm', 'total_dB_per_cm', 'roughness_rms', 'correlation_length']
WIDTHS = (250.0, 350.0, 700.0, 1200.0)
WAVELENGTHS = (450.0, 532.0, 635.0)
CASES = {f'w{int(w)}_{int(l)}': dict(lam=l, w=w) for l in WAVELENGTHS for w in WIDTHS}
H, ANGLE = 350.0, 5.0
SAPPHIRE_N_APPROX = 1.78   # n_o(Al2O3) at 450 nm is ~1.78; a mode below ~this is at/below substrate cutoff (leaky)


def run_case(name, c, cfg):
    g = geo.make_geometry('ridge', {'h_core': H, 'w_core': c['w'], 'sidewall_angle': ANGLE,
                                    'substrate_height': 1500.0, 'topclad_height': 2500.0})
    em = pmh.launch_session(f'gl04_{name}', clear='all')
    try:
        g.build(em, cfg['roughness_rms'], cfg['correlation_length'])
        em.settings(boundary_condition='0A', wavelength=c['lam'], x_resolution=cfg['resolution'],
                    y_resolution=cfg['resolution'], num_modes=1)
        n, te = survey.solve(em, 'gl04', wavelength=c['lam'], num_modes=8, max_effective_index=0,
                             x_resolution=cfg['resolution'], y_resolution=cfg['resolution'])
        x, y, modes = survey.fetch_fields(em)
        order = np.argsort(-n.real)
        cand = [j for j in order if te[j] <= 0.5]
        if not cand:
            return dict(case=name, wavelength_nm=c['lam'], width_nm=c['w'], height_nm=H, guided_note='no TM-like mode found')
        i = int(cand[0])
        mask = g.core_mask(x, y)
        sz = np.clip(np.real(modes[i]['Sz']), 0, None)
        pfrac = float((sz * mask).sum() / sz.sum())
        scat = survey.native_scattering(em, i, g.scatter_shapes)
        absn = sum(am.compute_mechanism_losses(mask, x[1] - x[0], y, modes[i]['Sz'], cfg['pump_absorption_mechanisms']).values())
        note = 'guided' if n[i].real > SAPPHIRE_N_APPROX + 0.01 else 'n_eff near/below sapphire index: leaky or marginal'
        print(f"  {name}: n_eff={n[i].real:.4f} te={te[i]:.3f} Pcore={pfrac:.3f} scat={scat / 100:.3f} abs={absn / 100:.3f} dB/cm [{note}]", flush=True)
        return dict(case=name, wavelength_nm=c['lam'], width_nm=c['w'], height_nm=H, n_eff=float(n[i].real), te_fraction=float(te[i]),
                    guided_note=note, power_fraction_core=pfrac, scattering_dB_per_cm=scat / 100.0, absorption_dB_per_cm=absn / 100.0,
                    total_dB_per_cm=(scat + absn) / 100.0, roughness_rms=str(cfg['roughness_rms']),
                    correlation_length=str(cfg['correlation_length']))
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
