"""TM00 vs TM10 (and other) pump modes under alternative pump-loss models -- EMode-free.

Re-evaluates every REFINED crossing of a survey run from its stored exports: the pump-loss terms are recomputed with
loss_model.py for each named case (loss_model.CASES), the SH loss is the stored one with its calibrated flat absorption
swapped for A_abs in SH_ABS_CASES [dB/cm, confinement-weighted by sh_power_in_core as in survey.calibrated_sh_loss], and
the loss-limited peak efficiency comes from shg_physics.loss_limited_length. The 'current' case with A_abs = 100 must
reproduce the stored peak_efficiency_pct_per_W (checked and printed).

Usage:  python tm10_vs_tm00_loss_cases.py [run_dir=runs/row1_ridge_v1]   -> runs/tm10_vs_tm00_loss_cases.csv
"""
import csv
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loss_model as lm  # noqa: E402
import shg_physics as sp  # noqa: E402
import survey_config  # noqa: E402
import geometry as geo  # noqa: E402

SH_ABS_CASES = (43.0, 100.0, 300.0)       # dB/cm flat SH absorption (study band; 100 = what the survey used)
CASES = list(lm.CASES)


def main(run_dir):
    cfg = survey_config.SETTINGS
    mechs = cfg['pump_absorption_mechanisms']
    d = pd.read_csv(os.path.join(run_dir, 'crossings.csv'))
    d = d[(d.status == 'refined') & (d.family == 'ridge')]
    rows, missing = [], 0
    for _, r in d.iterrows():
        path = os.path.join(HERE, str(r.export_path).replace('\\', os.sep))
        if not os.path.exists(path):
            missing += 1
            continue
        z = np.load(path)
        x, y, mask, sz = z['x'], z['y'], z['core_mask'], z['pump_Sz']
        dx, lam_p = x[1] - x[0], 2.0 * float(r.wavelength_sh)
        orig = lm.evaluate(mask, dx, y, sz, 0.0, mechs, lam_p, None)['absorption_interface']
        bulk = float(r.pump_absorption_dB_per_m) - orig              # AlN-core / strip bulk terms, unchanged by the cases
        gam_s = float(r.sh_power_in_core)
        eta = float(r.eta_pct_per_W_cm2) * 100.0                      # 1/(W m^2)
        scat_p = float(r.pump_scattering_dB_per_m)
        for cname in CASES:
            lp = lm.evaluate(mask, dx, y, sz, scat_p, mechs, lam_p, lm.case(cname))
            a_p = lp['scattering_sidewall'] + lp['volume_scattering'] + lp['absorption_interface'] + bulk
            for A in SH_ABS_CASES:
                a_s = float(r.sh_scattering_dB_per_m) + float(r.sh_absorption_dB_per_m) \
                    - gam_s * geo.SH_ABSORPTION_CALIBRATED_DB_PER_CM * 100.0 + gam_s * A * 100.0
                L, leff, peak = sp.loss_limited_length(eta, a_p, a_s)
                rows.append(dict(params=r.params, pump=r.pump_label, sh=r.sh_label, lam_sh=float(r.wavelength_sh),
                                 nce=float(r.eta_pct_per_W_cm2), case=cname, sh_abs_dB_cm=A,
                                 pump_loss_dB_cm=a_p / 100.0, sh_loss_dB_cm=a_s / 100.0, L_opt_mm=L * 1e3,
                                 peak_pct_per_W=peak * 100.0, stored_peak=float(r.peak_efficiency_pct_per_W)))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, 'runs', 'tm10_vs_tm00_loss_cases.csv'), index=False)
    print(f'{len(d)} refined crossings, {missing} exports missing, {len(out)} rows')
    chk = out[(out.case == 'current') & (out.sh_abs_dB_cm == 100.0)]
    rel = (chk.peak_pct_per_W / chk.stored_peak.replace(0, np.nan) - 1).abs()
    print('reproduces stored peak efficiency: median |rel err| %.2e, max %.2e' % (rel.median(), rel.max()))
    return out


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join('runs', 'row1_ridge_v1'))
