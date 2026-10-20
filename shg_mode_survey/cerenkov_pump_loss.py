"""Pump-loss budget for the Cerenkov pumps (row 8), EMode-free (uses the pump field exports).

The Cerenkov figure of merit is pump-loss-limited (L_eff,inf = 1/(2a)), so the pump loss model is a
first-order input. Decomposes, per bound pump of a run:
  scattering      EMode-native roughness scattering as stored in pump_modes.csv (assumed sidewall
                  roughness 2.5 nm rms / 50 nm correlation -- a generic fabrication assumption;
                  scales ~ sigma^2, so `scat_scale` = (sigma/2.5nm)^2)
  interface_<m>   the survey's growth-interface defect absorption mechanisms (Dislocations, C, Si, O --
                  generic AlN-on-sapphire baseline; applied to the ScAlN/AlN-substrate interface here,
                  which is an ASSUMPTION), one column each
  bulk_k450       ScAlN bulk absorption at the pump wavelength = Gamma_core * 8.686 * (2 pi/lam) * s * k450_fit.
                  NOT included in the survey's pump_absorption for the Ridge family (Ridge.lossy_mask is
                  None) although the guided ScAlN-strip rows DO include it -- an omission for Cerenkov
                  found 2026-10-19; the Baumler fit gives k(450) ~ 5e-5..2e-4 (a fit tail, uncertain).
`pump_loss_total(row, s, interface_scale, scat_scale, include_k450)` gives the total [dB/m] for a case.
Usage: python cerenkov_pump_loss.py <run> --config=<mod>   (prints the budget table, writes
runs/<run>/cerenkov_pump_loss.csv)
"""
import csv
import importlib
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geometry as geo  # noqa: E402
import absorption_model as am  # noqa: E402


def k450_fit(params, cfg):
    cx = (cfg.get('cerenkov_core_complex') or {}).get(params['core_eq_o'])
    return geo.eval_complex_index_equation(cx, 450.0).imag if cx else 0.0


def budget(run, config_module):
    cfg = importlib.import_module(config_module).SETTINGS
    mechs = cfg['pump_absorption_mechanisms']
    with open(os.path.join(HERE, 'runs', run, 'pump_modes.csv'), newline='') as f:
        rows = [r for r in csv.DictReader(f) if r.get('export_path')]
    out = []
    for r in rows:
        params = json.loads(r['params'])
        path = os.path.join(HERE, r['export_path'])
        if not os.path.exists(path):
            continue
        z = np.load(path)
        x, y = z['x'], z['y']
        geom = geo.make_geometry(r['family'], params)
        mask = geom.core_mask(x, y)
        Sz = 0.5 * np.real(z['Ex'] * np.conj(z['Hy']) - z['Ey'] * np.conj(z['Hx']))
        try:
            per = am.compute_mechanism_losses(mask, x[1] - x[0], y, Sz, mechs)
        except ValueError:
            continue
        gamma = float(r['power_in_core'])
        k450 = k450_fit(params, cfg)
        lam = float(r['wavelength_pump_center']) * 1e-9
        bulk = gamma * 8.686 * (2 * math.pi / lam) * k450      # [dB/m] at s = 1
        rec = {'fingerprint': r['fingerprint'], 'pump_id': r['pump_id'], 'label': r['label'],
               'comp_key': params['core_chi2'], 'h_core': params['h_core'], 'w_core': params['w_core'],
               'sub_h': params['substrate_height'], 'n_eff': float(r['n_eff_center']),
               'power_in_core': gamma, 'scattering': float(r['scattering_dB_per_m']),
               **{f"interface_{k.split(' ')[0]}": v for k, v in per.items()},
               'interface_total': sum(per.values()), 'k450_fit': k450, 'bulk_k450': bulk,
               'csv_absorption_total': float(r['absorption_dB_per_m'])}
        out.append(rec)
    return out


def pump_loss_total(rec, s=1.0, interface_scale=1.0, scat_scale=1.0, include_k450=True):
    """Total pump loss [dB/m] for a case. s scales the ScAlN fit k(450) (same multiplier as the SH loss
    case); interface_scale scales the growth-interface defect absorption; scat_scale the scattering."""
    return (scat_scale * rec['scattering'] + interface_scale * rec['interface_total']
            + (s * rec['bulk_k450'] if include_k450 else 0.0))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    kv = {a[2:].split('=')[0]: a.split('=', 1)[1] for a in sys.argv if a.startswith('--') and '=' in a}
    recs = budget(args[0], kv.get('config', 'survey_config'))
    path = os.path.join(HERE, 'runs', args[0], 'cerenkov_pump_loss.csv')
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0]))
        w.writeheader()
        w.writerows(recs)
    print(f"{'comp':>11} {'h':>4} {'w':>4} {'pump':>5} {'Gcore':>5} {'scat':>7} {'interf':>7} {'bulk450':>8} {'csvAbs':>7}  [dB/m]")
    for r in sorted(recs, key=lambda r: (r['comp_key'], r['h_core'], r['w_core'], r['label'])):
        if r['power_in_core'] >= 0.5:
            print(f"{r['comp_key']:>11} {r['h_core']:4.0f} {r['w_core']:4.0f} {r['label']:>5} {r['power_in_core']:5.2f} "
                  f"{r['scattering']:7.0f} {r['interface_total']:7.0f} {r['bulk_k450']:8.0f} {r['csv_absorption_total']:7.0f}")
    print('wrote', path)
