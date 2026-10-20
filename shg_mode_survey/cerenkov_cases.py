"""Cerenkov kappa for every bound pump of a run under the loss-case x d33-scenario grid.
EMode-free (reads pump exports). One factorization per (pump, k-scale, d) gives the 3x3 tensor
matrices K, W (cerenkov_fdfd.cerenkov_tensor), from which kappa for each d33 scenario is exact.

  python cerenkov_cases.py <run> --config=<module> [--k-cases=lossless,fit_x0.25,fit] [--d=7.5]
        [--labels=TM00,TE00,TE01] [--sub-heights=1000] [--min-core=0.5] [--out=cerenkov_cases.csv]
        [--margin=700]
Output columns: geometry/pump identifiers, k_case, k_scale, d_nm, K_total / K_bottom / W entries
(33_33, 31_31, 15_15, 33_31, 33_15, 31_15 -- [W/m per W^2 per (m/V)^2]), and kappa_<scenario>,
work_<scenario>, escape_<scenario> for every scenario in cerenkov_scenarios.d_scenarios.
kappa in %/W/cm (= 1/(W m)); escape = kappa / source work (fraction of generated SH that leaves).
"""
import csv
import importlib
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cerenkov_fdfd as cf  # noqa: E402
import cerenkov_run as cr  # noqa: E402
import cerenkov_scenarios as sc  # noqa: E402
import geometry as geo  # noqa: E402
import validate_cerenkov_1d_periodic as vp  # noqa: E402

PAIRS = [(0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2)]
PNAMES = ['33_33', '31_31', '15_15', '33_31', '33_15', '31_15']


def solve_case(row, cfg, k_scale, d_nm, margin_nm, fdfd_extra=None):
    z = np.load(os.path.join(HERE, row['export_path']))
    params = json.loads(row['params'])
    geom = geo.make_geometry(row['family'], params)
    lam = float(z['wavelength_sh'])
    n_regions = json.loads(str(z['n_regions_sh']))
    pump = {'x': z['x'], 'y': z['y'], **{k: z[k] for k in ('Ex', 'Ey', 'Ez')}}
    opts = {'core_k_scale': k_scale, **(fdfd_extra or {})}
    cx = (cfg.get('cerenkov_core_complex') or {}).get(params['core_eq_o'])
    if cx:
        opts['core_eq_complex'] = cx
    elif k_scale != 0:
        raise ValueError('no complex core equation for this geometry')
    grid = cr.domain_for(geom, d_nm, margin_nm=margin_nm, finite_layer=opts.get('under_n') is not None)
    t0 = time.time()
    res = cf.cerenkov_tensor(grid, geom.eps_fn(lam, n_regions, **opts),
                             lambda X, Y: geom.core_mask(X[0, :], Y[:, 0]).astype(float),
                             pump, lam, float(z['n_eff']))
    return res, geom, params, float(z['n_eff']), grid, round(time.time() - t0, 1)


def main(run, config_module, k_cases, d_nm, labels, sub_heights, min_core, out_name, margin_nm):
    cfg = importlib.import_module(config_module).SETTINGS
    run_dir = os.path.join(HERE, 'runs', run)
    with open(os.path.join(run_dir, 'pump_modes.csv'), newline='') as f:
        rows = [r for r in csv.DictReader(f) if r.get('export_path')]
    rows = [r for r in rows if r['label'].rstrip('?') in labels and float(r['power_in_core']) >= min_core
            and cr.pump_is_bound(json.loads(r['params']), r)
            and (not sub_heights or json.loads(r['params']).get('substrate_height') in sub_heights)]
    out_path = os.path.join(run_dir, out_name)
    done = set()
    if os.path.exists(out_path):
        with open(out_path, newline='') as f:
            done = {(r['fingerprint'], r['pump_id'], r['k_case'], r['d_nm']) for r in csv.DictReader(f)}
    print(f"{len(rows)} bound pumps x {len(k_cases)} loss cases", flush=True)
    for r in rows:
        for kc in k_cases:
            if (r['fingerprint'], r['pump_id'], kc, str(d_nm)) in done:
                continue
            res, geom, params, n_eff, grid, secs = solve_case(r, cfg, sc.K_SCALES[kc], d_nm, margin_nm)
            frac = sc.sc_fraction_from_key(params['core_chi2'])
            rec = {'fingerprint': r['fingerprint'], 'comp_sc': frac, 'sub_h': params['substrate_height'],
                   'h_core': params['h_core'], 'w_core': params['w_core'], 'pump_id': r['pump_id'],
                   'label': r['label'], 'n_eff': n_eff, 'power_in_core': r['power_in_core'],
                   'A_eff_um2': r['A_eff_um2'], 'k_case': kc, 'k_scale': sc.K_SCALES[kc], 'd_nm': d_nm,
                   'grid': f'{grid.nx}x{grid.ny}', 'seconds': secs}
            # numerical-reliability flag: 2D(periodic, same d) / 1D reference for a slab of this film
            # index and k (validate_cerenkov_1d_periodic.py). ~1 = trustworthy; far from 1 = the
            # 2D solve is dominated by discretization/resonance sensitivity at this loss.
            try:
                lam_sh = float(r['wavelength_pump_center']) / 2.0
                n0 = geo.eval_index_equation(params['core_eq_o'], lam_sh)
                cx = (cfg.get('cerenkov_core_complex') or {}).get(params['core_eq_o'])
                kfit = geo.eval_complex_index_equation(cx, lam_sh).imag if cx else 0.0
                film = complex(n0, sc.K_SCALES[kc] * kfit)
                rec['bias_2d_over_1d'] = vp.periodic_2d(film, d_nm) / vp.one_d(film)
            except Exception as e:  # noqa: BLE001
                rec['bias_2d_over_1d'] = float('nan')
            for (i, j), nm in zip(PAIRS, PNAMES):
                rec[f'K_{nm}'] = res['K_total'][i, j]
                rec[f'Kbottom_{nm}'] = res['K_sides'][0][i, j]
                rec[f'W_{nm}'] = res['W'][i, j]
            for name, (d33, d31, d15) in sc.d_scenarios(frac).items():
                k = cf.kappa_for(res, d33, d31, d15)
                rec[f'kappa_{name}'] = k['kappa']
                rec[f'work_{name}'] = k['work']
                rec[f'escape_{name}'] = k['kappa'] / k['work'] if k['work'] else float('nan')
            new = not os.path.exists(out_path)
            with open(out_path, 'a', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(rec))
                if new:
                    w.writeheader()
                w.writerow(rec)
            print(f"{frac:.3f} sub={params['substrate_height']:g} {r['label']:5s} {kc:10s} d={d_nm:g}: "
                  f"kappa(yoshioka)={rec['kappa_yoshioka']:.4g} escape={rec['escape_yoshioka']:.4f} "
                  f"kappa(mbe_like)={rec['kappa_mbe_like']:.3g} [{secs}s]", flush=True)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    kv = {a[2:].split('=')[0]: a.split('=', 1)[1] for a in sys.argv if a.startswith('--') and '=' in a}
    main(args[0], kv.get('config', 'survey_config'),
         kv.get('k-cases', 'lossless,fit_x0.25,fit').split(','), float(kv.get('d', 7.5)),
         kv.get('labels', 'TM00,TE00,TE01').split(','),
         [float(h) for h in kv['sub-heights'].split(',')] if 'sub-heights' in kv else None,
         float(kv.get('min-core', 0.5)), kv.get('out', 'cerenkov_cases.csv'), float(kv.get('margin', 700)))
