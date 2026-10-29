"""EMode-native roughness-scattering loss vs wavelength for ONE fixed reference geometry (default: ridge
h=350, w=400 nm, the survey's standard sapphire/SiO2 ridge) -- the fundamental TM mode (highest-n_eff
TM-like x-even mode) at each wavelength, with the survey's roughness settings (survey_config:
roughness_rms [2.5 (sidewall), 0.3 (top/bottom)] nm, correlation_length [50, 10] nm).

This is the scattering the simulation actually uses (survey.native_scattering -> em.scattering); it is
a function of wavelength through the mode's confinement and k0, so it is NOT the stored per-crossing
value (which belongs to whatever mode phase-matches, e.g. TM04 at the SH). Output feeds
plot_loss_overview.py.

Usage: python compute_scattering_reference.py [h] [w] [lam_min] [lam_max] [step]
Writes materials/scattering_reference_h<h>_w<w>.csv (lambda_nm, n_eff, te_fraction, scattering_dB_per_cm).
Needs EMode (one session reused; relaunched if it dies).
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geometry as geo  # noqa: E402
import emode_helpers as pmh  # noqa: E402
import survey  # noqa: E402
from survey_config import SETTINGS as CFG  # noqa: E402


def main(h=350.0, w=400.0, lam_min=200.0, lam_max=600.0, step=10.0):
    geom = geo.make_geometry('ridge', {'h_core': h, 'w_core': w})
    out = os.path.join(HERE, 'materials', f'scattering_reference_h{h:g}_w{w:g}.csv')
    done = {}
    if os.path.exists(out):
        with open(out, newline='') as f:
            done = {float(r['lambda_nm']): r for r in csv.DictReader(f)}
    em = None
    rows = list(done.values())
    for lam in np.arange(lam_min, lam_max + 1e-9, step):
        if float(lam) in done:
            continue
        for attempt in range(3):
            try:
                if em is None:
                    em = pmh.launch_session(f'scat_ref_{int(h)}_{int(w)}', clear='all')
                    geom.build(em, CFG['roughness_rms'], CFG['correlation_length'])
                em.settings(boundary_condition='0A')
                n, te = survey.solve(em, 'ref', wavelength=float(lam), num_modes=8, max_effective_index=0,
                                     x_resolution=CFG['resolution'], y_resolution=CFG['resolution'])
                order = np.argsort(-n.real)
                i = next((int(j) for j in order if te[j] < 0.5), int(order[0]))
                scat = survey.native_scattering(em, i, geom.scatter_shapes)
                rows.append({'lambda_nm': float(lam), 'n_eff': float(n[i].real), 'te_fraction': float(te[i]),
                             'scattering_dB_per_cm': scat / 100.0})
                print(f"{lam:6.1f} nm: n_eff={n[i].real:.4f} te={te[i]:.2f} scattering={scat / 100.0:.4g} dB/cm", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"{lam:6.1f} nm attempt {attempt + 1} failed: {e!r}", flush=True)
                try:
                    em.close(save=False)
                except Exception:  # noqa: BLE001
                    pass
                em = None
        rows.sort(key=lambda r: float(r['lambda_nm']))
        with open(out, 'w', newline='') as f:
            wr = csv.DictWriter(f, fieldnames=['lambda_nm', 'n_eff', 'te_fraction', 'scattering_dB_per_cm'])
            wr.writeheader()
            wr.writerows(rows)
    if em is not None:
        em.close(save=False)
    print('wrote', out)


if __name__ == '__main__':
    a = [float(x) for x in sys.argv[1:]]
    main(*a)
