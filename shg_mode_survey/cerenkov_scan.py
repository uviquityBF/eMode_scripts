"""EMode-free scans of the driven Cerenkov solve for ONE exported pump (reuses the field).

  python cerenkov_scan.py <run> <comp> <label> thickness --config=<mod> [--sub-h=1000] [--heights=500,600,...]
        [--under=sapphire|none] [--aniso] [--k=0.0]
      kappa vs finite AlN-layer thickness H on a sapphire half-space (or the infinite-AlN reference
      if --under=none). The pump is solved once; since it is bound its field doesn't depend on H, so
      the exported field is shifted to the new core height (y += H - sub-h).
  python cerenkov_scan.py <run> <comp> <label> resolution --config=<mod> [--sub-h=1000] [--ds=5,7.5,10,15]
      kappa vs FDFD cell size (convergence check; the energy balance alone does not detect an
      inaccurate source).
Writes runs/<run>/scan_<comp>_<label>_<mode>.csv.
"""
import csv, importlib, json, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cerenkov_fdfd as cf  # noqa: E402
import cerenkov_run as cr  # noqa: E402
import geometry as geo  # noqa: E402


def sapphire_n_o(lam_nm):
    """Malitson/Dodge ordinary-ray Sellmeier for sapphire (lambda in um, valid >= ~0.2 um)."""
    l2 = (lam_nm / 1000.0) ** 2
    return float(np.sqrt(1 + 1.4313493 * l2 / (l2 - 0.0726631 ** 2) + 0.65054713 * l2 / (l2 - 0.1193242 ** 2)
                         + 5.3414021 * l2 / (l2 - 18.028251 ** 2)))


def pick_row(run_dir, comp, label, sub_h):
    with open(os.path.join(run_dir, 'pump_modes.csv'), newline='') as f:
        for r in csv.DictReader(f):
            p = json.loads(r['params'])
            if (r['export_path'] and r['label'].rstrip('?') == label
                    and abs(float(p['core_chi2'].split('_')[1]) - comp) < 1e-6
                    and abs(p['substrate_height'] - sub_h) < 1e-6 and cr.pump_is_bound(p, r)
                    and float(r['power_in_core']) >= 0.5):
                return r
    raise SystemExit(f'no bound pump row for comp={comp} label={label} sub_h={sub_h}')


def solve_one(row, d_tensors, d_nm, sub_h=None, supersample=1, core_complex=None, **opts):
    z = np.load(os.path.join(HERE, row['export_path']))
    params = json.loads(row['params'])
    h0 = params['substrate_height']
    if sub_h is not None:
        params['substrate_height'] = sub_h
    geom = geo.make_geometry(row['family'], params)
    if core_complex and params.get('core_eq_o') in core_complex:
        opts = {**opts, 'core_eq_complex': core_complex[params['core_eq_o']]}
    lam = float(z['wavelength_sh'])
    n_regions = json.loads(str(z['n_regions_sh']))
    pump = {'x': z['x'], 'y': z['y'] + (params['substrate_height'] - h0), **{k: z[k] for k in ('Ex', 'Ey', 'Ez')}}
    grid = cr.domain_for(geom, d_nm, finite_layer=opts.get('under_n') is not None)
    t0 = time.time()
    res = cf.cerenkov_from_pump(grid, geom.eps_fn(lam, n_regions, **opts), geom.d_fn(d_tensors), pump, lam,
                                float(z['n_eff']), supersample=supersample)
    s = res['sides_W_per_m']
    return {'kappa': res['total_W_per_m'], 'bottom': s['bottom'], 'top': s['top'],
            'lateral': s['left'] + s['right'], 'work': res['source_work_W_per_m'],
            'balance': res['total_W_per_m'] / res['source_work_W_per_m'], 'grid': f'{grid.nx}x{grid.ny}',
            'seconds': round(time.time() - t0, 1)}


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    kv = {a[2:].split('=')[0]: (a.split('=', 1)[1] if '=' in a else True) for a in sys.argv if a.startswith('--')}
    run, comp, label, mode = args[0], float(args[1]), args[2], args[3]
    cfg = importlib.import_module(kv.get('config', 'survey_config')).SETTINGS
    run_dir = os.path.join(HERE, 'runs', run)
    sub_h = float(kv.get('sub-h', 1000))
    row = pick_row(run_dir, comp, label, sub_h)
    ss = int(kv.get('ss', 1))
    core_complex = cfg.get('cerenkov_core_complex') if kv.get('core-k') else None
    opts = {'aniso_substrate': bool(kv.get('aniso')), 'substrate_k': float(kv.get('k', 0.0))}
    if 'kscale' in kv:
        opts['core_k_scale'] = float(kv['kscale'])
    out = os.path.join(run_dir, f"scan_{comp:g}_{label}_{mode}{'_corek' if kv.get('core-k') else ''}{'_ks' + kv['kscale'] if 'kscale' in kv else ''}{kv.get('tag', '')}{'_ss%d' % ss if ss > 1 else ''}.csv")
    rows = []
    if mode == 'thickness':
        heights = [float(h) for h in kv.get('heights', '500,1000,1500,2000').split(',')]
        under = sapphire_n_o(225.0) if kv.get('under', 'sapphire') == 'sapphire' else None
        for h in heights:
            r = solve_one(row, cfg['d_tensors_pm'], float(kv.get('d', 10)), sub_h=h, core_complex=core_complex,
                          **({**opts, 'under_n': under} if under else opts))
            rows.append({'H_nm': h, 'under_n': under, 'core_k': bool(core_complex), **r})
            print(f"H={h:g}: kappa={r['kappa']:.4g} bottom={r['bottom']:.3g} lateral={r['lateral']:.3g} "
                  f"balance={r['balance']:.3f} {r['seconds']}s", flush=True)
    else:
        for d in [float(x) for x in kv.get('ds', '5,7.5,10,15').split(',')]:
            r = solve_one(row, cfg['d_tensors_pm'], d, supersample=ss, core_complex=core_complex, **opts)
            rows.append({'d_nm': d, 'core_k': bool(core_complex), **r})
            print(f"d={d:g}: kappa={r['kappa']:.4g} balance={r['balance']:.3f} grid={r['grid']} {r['seconds']}s",
                  flush=True)
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print('wrote', out)
