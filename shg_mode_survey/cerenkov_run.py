"""Step 1b driver: Cerenkov / radiated SH rate for every exported pump mode of a survey run.
No EMode needed -- uses the pump exports (survey.py writes exports/<fp>_pump<id>.npz) and the
geometry's eps/d maps. See cerenkov_fdfd.py for the method and its validation.

Writes runs/<run>/cerenkov.csv: per pump, kappa_C [%/W/cm] (= 1/(W m): SH power radiated per
unit length per W^2 of pump), the split by side (bottom = substrate, top = top clad,
left/right = lateral), the source-work cross-check, and the Cerenkov flags from the survey.

Usage: python cerenkov_run.py <run_name> [--all] [--d=10] [--config=<module>] [--aniso-substrate]
       [--labels=TM00,TM01] [--sub-heights=1000,2000] [--core-k] [--ss=4] [--substrate-k=<k>] [--under-n=<n>] [--out=<csv name>]
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


def domain_for(geom, d_nm, margin_nm=700.0, npml=20, finite_layer=False):
    """FDFD box around the core. finite_layer=True extends the bottom to margin_nm below y = 0 (the
    bottom of a finite substrate layer, see Ridge.eps_fn under_n) instead of below the core."""
    x0, x1, y0, y1 = geom.bbox()
    pad = margin_nm + npml * d_nm
    ybot = (min(y0 - margin_nm, -margin_nm) - npml * d_nm) if finite_layer else y0 - pad
    return cf.YeeGrid(x0 - pad, x1 + pad, ybot, y1 + pad, d_nm)


def pump_is_bound(params, row, margin=0.0):
    """True if the pump's n_eff exceeds the (ridge) substrate's index AT THE PUMP wavelength on the
    axis its polarization sees (TE -> n_o, TM -> n_e). Otherwise the pump is not bound in a bulk
    substrate -- EMode then returns a box/slab mode of the finite substrate layer (A_eff scales
    with its thickness), not a ridge mode, and its kappa is meaningless. Substrates given by a
    database name (e.g. sapphire) can't be evaluated here and are assumed bound."""
    if not params.get('substrate_eq_o'):
        return True
    lam = float(row['wavelength_pump_center'])
    n_o = geo.eval_index_equation(params['substrate_eq_o'], lam)
    n_e = geo.eval_index_equation(params.get('substrate_eq_e') or params['substrate_eq_o'], lam)
    n_axis = n_o if float(row.get('te_fraction') or 0) > 0.5 else n_e
    return float(row['n_eff_center']) > n_axis + margin


def run_one(row, d_tensors_pm, d_nm, fdfd_opts=None, core_complex=None, supersample=1):
    z = np.load(os.path.join(HERE, row['export_path']))
    params = json.loads(row['params'])
    geom = geo.make_geometry(row['family'], params)
    lam = float(z['wavelength_sh'])
    n_regions = json.loads(str(z['n_regions_sh']))
    pump = {'x': z['x'], 'y': z['y'], **{k: z[k] for k in ('Ex', 'Ey', 'Ez')}}
    fdfd_opts = dict(fdfd_opts or {})
    if core_complex and params.get('core_eq_o') in core_complex:
        fdfd_opts['core_eq_complex'] = core_complex[params['core_eq_o']]
    grid = domain_for(geom, d_nm, finite_layer=fdfd_opts.get('under_n') is not None)
    t0 = time.time()
    eps_fn = geom.eps_fn(lam, n_regions, **fdfd_opts) if fdfd_opts else geom.eps_fn(lam, n_regions)
    res = cf.cerenkov_from_pump(grid, eps_fn, geom.d_fn(d_tensors_pm), pump, lam, float(z['n_eff']),
                                supersample=supersample)
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


MIN_CORE_FRACTION = 0.05  # exclude pseudo-modes (e.g. substrate/window-edge pinned, not core-
# guided at all) found 2026-10-16/17 on an AlN-substrate ridge: a "TM00[S]" candidate there had
# 99.9% of its power pinned at the simulation window's bottom edge (power_in_core ~0.0007) and a
# n_eff essentially frozen across an entire 8-point composition sweep -- a numerical artifact of
# the high-index AlN substrate supporting its own window-edge mode, not a real ridge-guided pump.
# Real ridge-guided candidates seen so far carry power_in_core ~0.1-0.4+; 0.05 is a generous floor.


def main(run_name, include_all=False, d_nm=10.0, config_module='survey_config',
         min_core_fraction=MIN_CORE_FRACTION, fdfd_opts=None, out_name='cerenkov.csv',
         labels=None, sub_heights=None, core_complex_on=False, supersample=1):
    import importlib
    cfg = importlib.import_module(config_module).SETTINGS
    run_dir = os.path.join(HERE, 'runs', run_name)
    with open(os.path.join(run_dir, 'pump_modes.csv'), newline='') as f:
        rows = [r for r in csv.DictReader(f) if r.get('export_path')]
    if not include_all:
        rows = [r for r in rows if r['cerenkov_allowed_any'] == 'True']
    n_before = len(rows)
    rows = [r for r in rows if not r.get('power_in_core') or float(r['power_in_core']) >= min_core_fraction]
    if n_before != len(rows):
        print(f"excluded {n_before - len(rows)} pump(s) below power_in_core={min_core_fraction} "
              f"(pseudo-mode filter -- see MIN_CORE_FRACTION)")
    if labels:
        rows = [r for r in rows if r['label'].rstrip('?') in labels]
    if sub_heights:
        rows = [r for r in rows if json.loads(r['params']).get('substrate_height') in sub_heights]
    n_before = len(rows)
    rows = [r for r in rows if pump_is_bound(json.loads(r['params']), r)]
    if n_before != len(rows):
        print(f"excluded {n_before - len(rows)} pump(s) not bound in the substrate "
              f"(n_eff <= substrate index at the pump wavelength -- see pump_is_bound)")
    out_path = os.path.join(run_dir, out_name)
    done = set()
    if os.path.exists(out_path):
        with open(out_path, newline='') as f:
            done = {(r['fingerprint'], r['pump_id'], r['d_nm']) for r in csv.DictReader(f)}
    todo = [r for r in rows if (r['fingerprint'], r['pump_id'], f"{d_nm}") not in done]
    print(f"{len(rows)} pumps selected, {len(todo)} to compute")
    for r in todo:
        out = run_one(r, cfg['d_tensors_pm'], d_nm, fdfd_opts,
                      cfg.get('cerenkov_core_complex') if core_complex_on else None, supersample)
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
    config_module = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--config=')),
                         'survey_config')
    opts = {}
    if '--aniso-substrate' in sys.argv:
        opts['aniso_substrate'] = True
    for a in sys.argv:
        if a.startswith('--substrate-k='):
            opts['substrate_k'] = float(a.split('=')[1])
        if a.startswith('--under-n='):
            opts['under_n'] = float(a.split('=')[1])
    out_name = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), 'cerenkov.csv')
    main(args[0], include_all='--all' in sys.argv, d_nm=d, config_module=config_module,
         fdfd_opts=opts or None, out_name=out_name, core_complex_on='--core-k' in sys.argv,
         supersample=int(next((a.split('=')[1] for a in sys.argv if a.startswith('--ss=')), 1)),
         labels=next((a.split('=')[1].split(',') for a in sys.argv if a.startswith('--labels=')), None),
         sub_heights=next(([float(h) for h in a.split('=')[1].split(',')] for a in sys.argv
                           if a.startswith('--sub-heights=')), None))
