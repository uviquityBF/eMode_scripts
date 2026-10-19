"""Artifact audit of a Cerenkov run's pump modes -- no EMode, no FDFD; reads pump_modes.csv (and
cerenkov.csv if present). Flags, per pump:
  window   -- the legacy EMode window (h_core + 2000) did not contain substrate + core + clad
              (top clad cut off; found 2026-10-19 at substrate_height = 2000)
  unbound  -- n_eff <= substrate index at the pump wavelength (box/slab mode, not a ridge mode)
  weakcore -- power_in_core < 0.30 (mostly substrate field; kappa not a ridge-pump property)
A pump with no flags is 'ok'. Usage: python cerenkov_audit.py <run_name> [--legacy-window]
(--legacy-window checks against the old fixed window; default checks the current Ridge.window_margin.)
"""
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cerenkov_run as cr  # noqa: E402

WEAK_CORE = 0.30


def audit(run_name, legacy_window=False):
    run_dir = os.path.join(HERE, 'runs', run_name)
    with open(os.path.join(run_dir, 'pump_modes.csv'), newline='') as f:
        pumps = list(csv.DictReader(f))
    kappa = {}
    kp = os.path.join(run_dir, 'cerenkov.csv')
    if os.path.exists(kp):
        with open(kp, newline='') as f:
            kappa = {(r['fingerprint'], r['pump_id']): float(r['kappa_pct_per_W_cm']) for r in csv.DictReader(f)}
    out = []
    for r in pumps:
        p = json.loads(r['params'])
        flags = []
        if p.get('substrate_height') is not None and 'topclad_height' in p:
            margin = 2000.0 if legacy_window else max(2000.0, p['substrate_height'] + p['topclad_height'] + 200.0)
            if p['substrate_height'] + p['h_core'] + p['topclad_height'] + 200.0 > p['h_core'] + margin:
                flags.append('window')
        if not cr.pump_is_bound(p, r):
            flags.append('unbound')
        if float(r['power_in_core']) < WEAK_CORE:
            flags.append('weakcore')
        out.append({'comp': p.get('core_chi2', '')[-4:], 'sub_h': p.get('substrate_height'), 'pump': r['pump_id'],
                    'label': r['label'], 'n_eff': float(r['n_eff_center']), 'core': float(r['power_in_core']),
                    'A_eff': float(r['A_eff_um2']), 'flags': ','.join(flags) or 'ok',
                    'kappa': kappa.get((r['fingerprint'], r['pump_id']))})
    return out


if __name__ == '__main__':
    rows = audit(sys.argv[1], '--legacy-window' in sys.argv)
    print(f"{'comp':>5} {'subH':>6} {'pump':>4} {'label':>6} {'n_eff':>7} {'core':>6} {'Aeff':>6} {'kappa':>10}  flags")
    for r in sorted(rows, key=lambda r: (r['comp'], r['sub_h'] or 0, int(r['pump']))):
        k = f"{r['kappa']:.3g}" if r['kappa'] is not None else '-'
        print(f"{r['comp']:>5} {r['sub_h']!s:>6} {r['pump']:>4} {r['label']:>6} {r['n_eff']:7.4f} {r['core']:6.3f} "
              f"{r['A_eff']:6.3f} {k:>10}  {r['flags']}")
    n_ok = sum(r['flags'] == 'ok' for r in rows)
    print(f"\n{n_ok}/{len(rows)} pumps unflagged; with kappa: "
          f"{sum(r['flags'] == 'ok' and r['kappa'] is not None for r in rows)} unflagged of "
          f"{sum(r['kappa'] is not None for r in rows)} computed")
