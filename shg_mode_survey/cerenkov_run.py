"""Step 1b driver: Cerenkov / radiated SH rate for every exported pump mode of a survey run.
No EMode needed -- uses the pump exports (survey.py writes exports/<fp>_pump<id>.npz) and the
geometry's eps/d maps. See cerenkov_fdfd.py for the method and its validation.

Writes runs/<run>/cerenkov.csv: per pump, kappa_C [%/W/cm] (= 1/(W m): SH power radiated per
unit length per W^2 of pump), the split by side (bottom = substrate, top = top clad,
left/right = lateral), the source-work cross-check, and the Cerenkov flags from the survey.

Usage: python cerenkov_run.py <run_name> [--all] [--d=10]
   default: only pumps flagged Cerenkov-allowed; --all: every pump (allowed-or-not check);
   --d: FDFD cell size [nm].
"""

import csv
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cerenkov_fdfd as cf  # noqa: E402
import geometry as geo  # noqa: E402

FIELDS = ['fingerprint', 'family', 'params', 'pump_id', 'label', 'n_eff', 'wavelength_sh',
          'cerenkov_allowed_any', 'cerenkov_best_angle_deg', 'kappa_pct_per_W_cm',
          'to_substrate', 'to_topclad', 'to_left', 'to_right', 'source_work_pct_per_W_cm',
          'balance', 'd_nm', 'grid', 'seconds']


def domain_for(geom, d_nm, margin_nm=700.0, npml=20):
    x0, x1, y0, y1 = geom.bbox()
    pad = margin_nm + npml * d_nm
    return cf.YeeGrid(x0 - pad, x1 + pad, y0 - pad, y1 + pad, d_nm)


def run_one(row, d_tensors_pm, d_nm):
    z = np.load(os.path.join(HERE, row['export_path']))
    params = json.loads(row['params'])
    geom = geo.make_geometry(row['family'], params)
    lam = float(z['wavelength_sh'])
    n_regions = json.loads(str(z['n_regions_sh']))
    pump = {'x': z['x'], 'y': z['y'], **{k: z[k] for k in ('Ex', 'Ey', 'Ez')}}
    grid = domain_for(geom, d_nm)
    t0 = time.time()
    res = cf.cerenkov_from_pump(grid, geom.eps_fn(lam, n_regions), geom.d_fn(d_tensors_pm),
                                pump, lam, float(z['n_eff']))
    s = res['sides_W_per_m']
    return {'fingerprint': row['fingerprint'], 'family': row['family'], 'params': row['params'],
            'pump_id': row['pump_id'], 'label': row['label'], 'n_eff': float(z['n_eff']),
            'wavelength_sh': lam, 'cerenkov_allowed_any': row['cerenkov_allowed_any'],
            'cerenkov_best_angle_deg': row['cerenkov_best_angle_deg'],
            'kappa_pct_per_W_cm': res['total_W_per_m'], 'to_substrate': s['bottom'],
            'to_topclad': s['top'], 'to_left': s['left'], 'to_right': s['right'],
            'source_work_pct_per_W_cm': res['source_work_W_per_m'],
            'balance': res['total_W_per_m'] / res['source_work_W_per_m']
            if res['source_work_W_per_m'] else float('nan'),
            'd_nm': d_nm, 'grid': f"{grid.nx}x{grid.ny}", 'seconds': round(time.time() - t0, 1)}


def main(run_name, include_all=False, d_nm=10.0, config_module='survey_config'):
    import importlib
    cfg = importlib.import_module(config_module).SETTINGS
    run_dir = os.path.join(HERE, 'runs', run_name)
    with open(os.path.join(run_dir, 'pump_modes.csv'), newline='') as f:
        rows = [r for r in csv.DictReader(f) if r.get('export_path')]
    if not include_all:
        rows = [r for r in rows if r['cerenkov_allowed_any'] == 'True']
    out_path = os.path.join(run_dir, 'cerenkov.csv')
    done = set()
    if os.path.exists(out_path):
        with open(out_path, newline='') as f:
            done = {(r['fingerprint'], r['pump_id'], r['d_nm']) for r in csv.DictReader(f)}
    todo = [r for r in rows if (r['fingerprint'], r['pump_id'], f"{d_nm}") not in done]
    print(f"{len(rows)} pumps selected, {len(todo)} to compute")
    for r in todo:
        out = run_one(r, cfg['d_tensors_pm'], d_nm)
        new = not os.path.exists(out_path)
        with open(out_path, 'a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            w.writerow(out)
        pp = json.loads(r['params'])
        print(f"h={pp.get('h_core')} w={pp.get('w_core')} {r['label']}: kappa_C = {out['kappa_pct_per_W_cm']:.3g} %/W/cm "
              f"(substrate {out['to_substrate']:.2g}, top {out['to_topclad']:.2g}, "
              f"lateral {out['to_left'] + out['to_right']:.2g}; balance {out['balance']:.3f}; "
              f"{out['seconds']:.0f}s)")


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    d = next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--d=')), 10.0)
    main(args[0], include_all='--all' in sys.argv, d_nm=d)
