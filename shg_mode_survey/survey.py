"""SHG mode survey, Step 1: for each geometry, find every pump-mode / SH-mode phase match with
lambda_SH in a window and compute overlap, effective areas, NCE, losses and loss-limited
efficiency. See PLAN.md for the physics and design.

Per geometry (one fresh EMode session, so an EMode.exe crash costs only that geometry):
  1. Pump modes: solve both x-symmetry classes ('0A' = Ey-even e.g. TM00/TM01, '0S' = Ey-odd
     e.g. TM10/TE00) at a few pump wavelengths, pick the lowest N TM-like (+ optional TE-like)
     modes at the window centre, track them across wavelength by field similarity, interpolate
     n_eff(lambda). Pumps are grouped by n_eff (span <= pump_group_span).
  2. SH scan: at each lambda_SH step and for each pump group, solve class '0A' only -- by the
     x-mirror selection rule (PLAN.md) an x-odd SH mode has exactly zero overlap with ANY pump
     mode -- for the `num_sh_modes` modes nearest the group's n_eff (EMode returns the modes
     nearest max_effective_index). SH modes are tracked step-to-step by field similarity; a sign
     change of n_SH - n_pump along a track is a phase-match crossing. Every crossing is
     SCREENED on the spot (overlap/NCE from fields already in memory: SH at the nearer scan
     step, pump at the nearest pump point).
  3. The best `refine_top_n` crossings (by screened NCE, above refine_min_nce) are REFINED:
     pump and SH re-solved at the crossing wavelength, re-identified, full figures of merit +
     EMode-native scattering + post-processed absorption + loss-limited efficiency, and both
     modes' fields exported (.npz) for reprocessing / the Cerenkov module. The rest are kept in
     crossings.csv with status 'screened'.

Checkpointing: a geometry is the unit of work. geometries.csv records each geometry's
fingerprint (hash of family+params+settings+d-tensors) and status; on re-run, geometries with
an 'ok' row for the same fingerprint are skipped, everything else is (re)done. Rows in
crossings.csv / pump_modes.csv are only written once a geometry completes.

Usage:  python survey.py <run_name> [config_module] [--pumps-only]
        (default config: survey_config.py; --pumps-only = pump modes + exports only,
        e.g. as input for cerenkov_run.py)
"""

import csv
import importlib
import json
import os
import sys
import time
import traceback
from datetime import datetime

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geometry as geo  # noqa: E402  (also puts the shared folders on sys.path)
import emode_helpers as pmh  # noqa: E402
import absorption_model as am  # noqa: E402
import shg_physics as sp  # noqa: E402

FIELD_KEYS = ['Ex', 'Ey', 'Ez', 'Hx', 'Hy', 'Hz', 'Sx', 'Sy', 'Sz']
SCAN_KEYS = ['Ex', 'Ey', 'Ez', 'Hx', 'Hy']  # enough for tracking, power, overlap
TRACK_SIMILARITY_MIN = 0.5

GEOM_FIELDS = ['fingerprint', 'family', 'params', 'status', 'n_pump_modes', 'n_crossings',
               'n_refined', 'seconds', 'timestamp', 'error']
PUMP_FIELDS = ['fingerprint', 'family', 'params', 'pump_id', 'label', 'sym_class', 'te_fraction',
               'n_eff_center', 'n_eff_min', 'n_eff_max', 'wavelength_pump_center',
               'scattering_dB_per_m', 'absorption_dB_per_m', 'A_eff_um2', 'cerenkov_allowed_any',
               'cerenkov_best_angle_deg', 'cerenkov_json', 'export_path']
CROSS_FIELDS = ['fingerprint', 'family', 'params', 'status', 'pump_id', 'pump_label',
                'pump_sym_class', 'pump_te_fraction', 'sh_label', 'sh_te_fraction', 'sh_track',
                'wavelength_sh', 'wavelength_sh_corrected', 'n_eff_pump', 'n_eff_sh',
                'delta_n_residual', 'eta_pct_per_W_cm2', 'A_shg_um2', 'overlap_shape',
                'overlap_linear_emode', 'A_eff_pump_um2', 'A_eff_sh_um2',
                'pump_scattering_dB_per_m', 'pump_absorption_dB_per_m',
                'sh_scattering_dB_per_m', 'sh_absorption_dB_per_m',
                'L_opt_mm', 'L_eff_mm', 'peak_efficiency_pct_per_W', 'cerenkov_allowed_any',
                'eta_screen_pct_per_W_cm2', 'overlap_shape_screen', 'sh_label_screen',
                'export_path', 'pump_identify_similarity', 'sh_identify_similarity']


# ----------------------------------------------------------------------------------------- I/O
def append_rows(path, fieldnames, rows):
    new = not (os.path.exists(path) and os.path.getsize(path) > 0)
    with open(path, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def done_fingerprints(path):
    if not os.path.exists(path):
        return set()
    with open(path, newline='') as f:
        return {r['fingerprint'] for r in csv.DictReader(f) if r['status'] == 'ok'}


def log(run_dir, msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(run_dir, 'progress.log'), 'a') as f:
        f.write(line + '\n')


# ------------------------------------------------------------------------------- EMode access
def solve(em, label, **settings):
    res = pmh.solve_modes(em, label, **settings)
    n = np.asarray(res['n_eff_tilde'], dtype=complex)
    te = np.asarray(res.get('TE_fraction', np.full(len(n), np.nan)), dtype=float)
    return n, te


def fetch_fields(em, keys=None):
    """(x, y, list of per-mode dicts of (ny, nx) complex arrays) for the current solve. With the
    reduced SCAN_KEYS, Sz is derived as Re(Ex Hy* - Ey Hx*) (EMode's own convention)."""
    keys = keys or FIELD_KEYS
    fo = em.get_fields(key=keys)
    fo = fo if hasattr(fo, 'field') else next(iter(fo.values()))
    raw = np.asarray(fo.field)
    x, y = np.asarray(fo.grid.x, float), np.asarray(fo.grid.y, float)
    idx = {k: fo.field_names.index(k) for k in keys}
    modes = [{k: raw[idx[k], m].T for k in keys} for m in range(raw.shape[1])]
    if 'Sz' not in keys:
        for f in modes:
            f['Sz'] = np.real(f['Ex'] * np.conj(f['Hy']) - f['Ey'] * np.conj(f['Hx']))
    return x, y, modes


def native_scattering(em, mode_idx):
    """EMode-native roughness scattering [dB/m] (vertical + horizontal edges) for one mode of the
    current solve; NaN if it fails (never fatal)."""
    for kwargs in ({'mode_list': [int(mode_idx)]}, {}):
        try:
            em.scattering(shape='core', **kwargs)
            meta = em.get_shape(key='core')
            meta = meta['metadata'] if isinstance(meta, dict) else meta.metadata
            arr = np.atleast_1d(np.asarray(meta['scattering_sum'], dtype=float))
            return float(arr[0] if kwargs and len(arr) == 1 else arr[mode_idx])
        except Exception:  # noqa: BLE001
            continue
    return float('nan')


def small(f, step=2):
    """Down-sampled transverse field (for cheap tracking/identification)."""
    return {'Ex': f['Ex'][::step, ::step].astype(np.complex64),
            'Ey': f['Ey'][::step, ::step].astype(np.complex64)}


def norm_E(f, dA):
    """E components of a mode scaled to 1 W, complex64 (for screening overlaps)."""
    s = 1.0 / np.sqrt(sp.mode_power_W(f, dA))
    return {k: (f[k] * s).astype(np.complex64) for k in ('Ex', 'Ey', 'Ez')}


# ------------------------------------------------------------------------------------ tracking
def match_to_previous(prev, cur, dA_small):
    """Greedy one-to-one matching of mode lists by transverse similarity.
    prev/cur: lists of small-field dicts. Returns {cur_index: prev_index}."""
    pairs = []
    for i, fc in enumerate(cur):
        for j, fp in enumerate(prev):
            s = sp.transverse_similarity(fp, fc, dA_small)
            if s >= TRACK_SIMILARITY_MIN:
                pairs.append((s, i, j))
    pairs.sort(reverse=True)
    used_i, used_j, out = set(), set(), {}
    for s, i, j in pairs:
        if i not in used_i and j not in used_j:
            out[i] = j
            used_i.add(i)
            used_j.add(j)
    return out


class Tracker:
    """Follows modes across successive solves by field similarity. Each track:
    {'id', 'n': {step: n}, 'te': {step: te}, 'idx': {step: mode index}}."""

    def __init__(self, dA_small):
        self.dA_small = dA_small
        self.tracks = []
        self.prev_small = None
        self.k_prev = None

    def update(self, k, n, te, cur_small):
        if self.prev_small is None:
            match = {}
            by_last = {}
        else:
            match = match_to_previous(self.prev_small, cur_small, self.dA_small)
            by_last = {t['idx'][self.k_prev]: t for t in self.tracks if self.k_prev in t['idx']}
        out = []
        for i in range(len(n)):
            t = by_last.get(match.get(i, -1))
            if t is None:
                t = {'id': len(self.tracks), 'n': {}, 'te': {}, 'idx': {}}
                self.tracks.append(t)
            t['n'][k], t['te'][k], t['idx'][k] = float(n[i].real), float(te[i]), i
            out.append(t)
        self.prev_small, self.k_prev = cur_small, k
        return out


# ------------------------------------------------------------------------------- per geometry
def pump_stage(em, cfg, lam_sh, dA):
    """Solve pump modes in both symmetry classes at cfg['pump_points'] wavelengths spanning the
    window, pick the pump modes to keep, return them with n_eff(lambda_SH) interpolants and
    1 W-normalized E fields at each pump point."""
    lam_pts = np.linspace(lam_sh[0], lam_sh[-1], cfg['pump_points'])
    i_mid = len(lam_pts) // 2
    pumps = []
    dA_small = None
    for cls in ('A', 'S'):
        em.settings(boundary_condition='0' + cls)
        tracker, smalls, Es = None, {}, {}
        for k, lam in enumerate(lam_pts):
            n, te = solve(em, f'pump{cls}{k}', wavelength=2 * lam,
                          num_modes=cfg['num_pump_candidates'], max_effective_index=0,
                          x_resolution=cfg['resolution'], y_resolution=cfg['resolution'])
            x, y, modes = fetch_fields(em, SCAN_KEYS)
            if dA_small is None:
                dA_small = sp.cell_areas_m2(x[::2], y[::2])
            tracker = tracker or Tracker(dA_small)
            cur_small = [small(f) for f in modes]
            tracker.update(k, n, te, cur_small)
            smalls[k] = cur_small
            Es[k] = [norm_E(f, dA) for f in modes]
        for t in tracker.tracks:
            if len(t['n']) == len(lam_pts):  # tracked across the whole window
                t['cls'] = cls
                t['small'] = {k: smalls[k][t['idx'][k]] for k in t['idx']}
                t['E'] = {k: Es[k][t['idx'][k]] for k in t['idx']}
                pumps.append(t)
    tm = sorted([t for t in pumps if t['te'][i_mid] < 0.5], key=lambda t: -t['n'][i_mid])
    te = sorted([t for t in pumps if t['te'][i_mid] >= 0.5], key=lambda t: -t['n'][i_mid])
    chosen = tm[:cfg['num_pump_tm']] + te[:cfg['num_pump_te']]
    for pid, t in enumerate(chosen):
        t['id'] = pid
        t['n_interp'] = np.interp(lam_sh, lam_pts, [t['n'][k] for k in range(len(lam_pts))])
        t['lam_pts'] = lam_pts
    return chosen


def group_pumps(pumps, span):
    """Partition pumps (by centre n_eff) into groups whose n_eff spread is <= span."""
    def n_mid(p):
        return p['n_interp'][len(p['n_interp']) // 2]
    groups = []
    for p in sorted(pumps, key=lambda p: -n_mid(p)):
        if groups and n_mid(groups[-1][0]) - n_mid(p) <= span:
            groups[-1].append(p)
        else:
            groups.append([p])
    return groups


def characterize_pump(em, geom, cfg, t, lam_center, export_path=None):
    """Label, loss, effective area and Cerenkov flags for one chosen pump mode (window centre)."""
    em.settings(boundary_condition='0' + t['cls'])
    n, te = solve(em, 'pumpc', wavelength=2 * lam_center, num_modes=cfg['num_pump_candidates'],
                  max_effective_index=0, x_resolution=cfg['resolution'],
                  y_resolution=cfg['resolution'])
    x, y, modes = fetch_fields(em)
    i_mid = len(t['lam_pts']) // 2
    dA = sp.cell_areas_m2(x, y)
    dA_small = sp.cell_areas_m2(x[::2], y[::2])
    sims = [sp.transverse_similarity(t['small'][i_mid], small(f), dA_small) for f in modes]
    i = int(np.argmax(sims))
    mask = geom.core_mask(x, y)
    scat = native_scattering(em, i)
    absn = sum(am.compute_mechanism_losses(mask, x[1] - x[0], y, modes[i]['Sz'],
                                           cfg['pump_absorption_mechanisms']).values())
    regions = geom.cerenkov_regions(em, lam_center)
    flags = sp.cerenkov_flags(n[i].real, regions)
    allowed = [f for f in flags if f['allowed']]
    label = sp.mode_label(modes[i], te[i], mask)
    if export_path:
        fpw = sp.normalize_to_1W(modes[i], dA)
        np.savez_compressed(export_path, x=x, y=y, wavelength_sh=lam_center, n_eff=n[i].real,
                            label=label, sym_class=t['cls'],
                            n_regions_sh=json.dumps({r['name'].split(':')[0]: r['n'] for r in regions}),
                            **{k: fpw[k].astype(np.complex64) for k in ('Ex', 'Ey', 'Ez', 'Hx', 'Hy')})
    return {'label': label, 'te_fraction': te[i],
            'n_center': n[i].real, 'scattering': scat, 'absorption': absn,
            'A_eff': sp.intensity_effective_area_um2(modes[i], dA), 'cerenkov': flags,
            'cerenkov_any': bool(allowed),
            'cerenkov_best_angle': max((f['angle_deg'] for f in allowed), default=float('nan')),
            'similarity': sims[i]}


def sh_scan(em, geom, cfg, lam_sh, pumps, groups):
    """Solve SH (class A) per pump group at every lambda step, track modes, find and screen
    crossings. Returns (crossings, traces)."""
    em.settings(boundary_condition='0A')
    d_ref = cfg['d_tensors_pm'][cfg['d_ref_material']]['d33'] * 1e-12
    state = [{'tracker': None, 'prev_E': None, 'prev_small': None} for _ in groups]
    crossings, coverage_warnings = [], []
    x = y = dA = d_map = mask = None
    # Guided SH modes need n_eff above every cladding/substrate index at lambda_SH; below that
    # the metal-walled window only gives box modes of the radiation continuum (= Cerenkov
    # territory, handled by the separate driven-solve module, not here).
    n_cut = guided_cutoff(em, geom, lam_sh)
    for k, lam in enumerate(lam_sh):
        for g, (group, st) in enumerate(zip(groups, state)):
            pump_n = [p['n_interp'][k] for p in group]
            if max(pump_n) <= n_cut[k]:
                continue  # no pump in this group can phase-match a guided SH mode here
            lo_need = max(min(pump_n) - cfg['sh_window_margin'], n_cut[k])
            hi_need = max(pump_n) + cfg['sh_window_margin']
            target = 0.5 * (lo_need + hi_need)
            n, te = solve(em, f'sh{g}s{k}', wavelength=float(lam), num_modes=cfg['num_sh_modes'],
                          max_effective_index=target, x_resolution=cfg['resolution'],
                          y_resolution=cfg['resolution'])
            x, y, modes = fetch_fields(em, SCAN_KEYS)
            if dA is None:
                dA = sp.cell_areas_m2(x, y)
                d_map = geom.chi2_map(x, y, cfg['d_tensors_pm'])
                mask = geom.core_mask(x, y)
            st['tracker'] = st['tracker'] or Tracker(sp.cell_areas_m2(x[::2], y[::2]))
            lo, hi = float(np.min(n.real)), float(np.max(n.real))
            if lo > lo_need or hi < hi_need:
                coverage_warnings.append((g, float(lam), lo, hi))
            cur_small = [small(f) for f in modes]
            cur_E = [norm_E(f, dA) for f in modes]
            tracks_now = st['tracker'].update(k, n, te, cur_small)
            for i, t in enumerate(tracks_now):
                if k - 1 not in t['n'] or min(t['n'][k - 1] - n_cut[k - 1], t['n'][k] - n_cut[k]) <= 0:
                    continue  # not tracked across this step, or not a guided mode
                for p in group:
                    d0 = t['n'][k - 1] - p['n_interp'][k - 1]
                    d1 = t['n'][k] - p['n_interp'][k]
                    if np.sign(d0) == np.sign(d1):
                        continue
                    frac = d0 / (d0 - d1)
                    lam_x = float(lam_sh[k - 1] + frac * (lam_sh[k] - lam_sh[k - 1]))
                    Es = cur_E[i] if frac > 0.5 else st['prev_E'][t['idx'][k - 1]]
                    ref_small = cur_small[i] if frac > 0.5 else st['prev_small'][t['idx'][k - 1]]
                    kp = int(np.argmin(np.abs(p['lam_pts'] - lam_x)))
                    O = sp.shg_overlap(Es, p['E'][kp], d_map, dA)
                    eta = sp.eta_norm_per_W_m2(O, lam_x)
                    n_x = float(t['n'][k - 1] + frac * (t['n'][k] - t['n'][k - 1]))
                    crossings.append({
                        'pump': p, 'track': t['id'], 'lam': lam_x,
                        'slope': (d1 - d0) / (lam_sh[k] - lam_sh[k - 1]), 'ref_small': ref_small,
                        'te': t['te'][k], 'n_sh': n_x, 'n_p': n_x,
                        'eta_screen': eta, 'shape_screen': sp.overlap_shape_factor(Es, p['E'][kp], d_map, dA),
                        'label_screen': sp.mode_label(Es, t['te'][k], mask),
                        'A_shg_screen': sp.shg_effective_area_um2(eta, n_x, n_x, 2 * lam_x, d_ref)})
            st['prev_E'], st['prev_small'] = cur_E, cur_small
    all_tracks = [(g, t) for g, st in enumerate(state) if st['tracker'] for t in st['tracker'].tracks]
    traces = {'lambda_sh': np.asarray(lam_sh),
              'pump_n': np.array([p['n_interp'] for p in pumps]),
              'sh_group': np.array([g for g, _ in all_tracks]),
              'sh_n': np.array([[t['n'].get(k, np.nan) for k in range(len(lam_sh))] for _, t in all_tracks]),
              'sh_te': np.array([[t['te'].get(k, np.nan) for k in range(len(lam_sh))] for _, t in all_tracks]),
              'coverage_warnings': np.array(coverage_warnings, dtype=float).reshape(-1, 4),
              'n_guided_cutoff': n_cut}
    return crossings, traces


def guided_cutoff(em, geom, lam_sh):
    """max cladding/substrate index at each lambda_SH (interpolated from 3 lookups)."""
    pts = np.array([lam_sh[0], 0.5 * (lam_sh[0] + lam_sh[-1]), lam_sh[-1]])
    vals = [max(r['n'] for r in geom.cerenkov_regions(em, float(l))) for l in pts]
    return np.interp(lam_sh, pts, vals)


def refine_crossing(em, geom, cfg, c, export_path):
    """Re-solve pump and SH at the crossing, identify them, compute all figures of merit."""
    p = c['pump']
    lam = c['lam']
    kp = int(np.argmin(np.abs(p['lam_pts'] - lam)))
    em.settings(boundary_condition='0' + p['cls'])
    n_p, te_p = solve(em, 'pumpx', wavelength=2 * lam, num_modes=cfg['num_pump_candidates'],
                      max_effective_index=0, x_resolution=cfg['resolution'],
                      y_resolution=cfg['resolution'])
    x, y, pm = fetch_fields(em)
    dA = sp.cell_areas_m2(x, y)
    dA_small = sp.cell_areas_m2(x[::2], y[::2])
    sims_p = [sp.transverse_similarity(p['small'][kp], small(f), dA_small) for f in pm]
    ip = int(np.argmax(sims_p))
    scat_p = native_scattering(em, ip)

    em.settings(boundary_condition='0A')
    n_s, te_s = solve(em, 'shx', wavelength=lam, num_modes=cfg['num_sh_refine_modes'],
                      max_effective_index=float(n_p[ip].real), x_resolution=cfg['resolution'],
                      y_resolution=cfg['resolution'])
    _, _, sm = fetch_fields(em)
    sims_s = [sp.transverse_similarity(c['ref_small'], small(f), dA_small) for f in sm]
    i_s = int(np.argmax(sims_s))
    scat_s = native_scattering(em, i_s)
    try:
        lin = float(abs(em.overlap(label_a='pumpx', mode_a=ip, label_b='shx', mode_b=i_s)))
    except Exception:  # noqa: BLE001
        lin = float('nan')

    mask = geom.core_mask(x, y)
    d = geom.chi2_map(x, y, cfg['d_tensors_pm'])
    fp = sp.normalize_to_1W(pm[ip], dA)
    fs = sp.normalize_to_1W(sm[i_s], dA)
    eta = sp.eta_norm_per_W_m2(sp.shg_overlap(fs, fp, d, dA), lam)
    d_ref = cfg['d_tensors_pm'][cfg['d_ref_material']]['d33'] * 1e-12
    np_, ns_ = float(n_p[ip].real), float(n_s[i_s].real)
    dx = x[1] - x[0]
    abs_p = sum(am.compute_mechanism_losses(mask, dx, y, pm[ip]['Sz'],
                                            cfg['pump_absorption_mechanisms']).values())
    abs_s = sum(am.compute_mechanism_losses(mask, dx, y, sm[i_s]['Sz'],
                                            cfg['sh_absorption_mechanisms']).values())
    L_opt, L_eff, peak = sp.loss_limited_length(eta, np.nan_to_num(scat_p) + abs_p,
                                                np.nan_to_num(scat_s) + abs_s)
    cer = sp.cerenkov_flags(np_, geom.cerenkov_regions(em, lam))
    np.savez_compressed(export_path, x=x, y=y, core_mask=mask, wavelength_sh=lam,
                        n_eff_pump=np_, n_eff_sh=ns_,
                        **{f'pump_{k}': fp[k].astype(np.complex64) for k in ('Ex', 'Ey', 'Ez', 'Hx', 'Hy')},
                        **{f'sh_{k}': fs[k].astype(np.complex64) for k in ('Ex', 'Ey', 'Ez', 'Hx', 'Hy')},
                        pump_Sz=np.real(pm[ip]['Sz']).astype(np.float32),
                        sh_Sz=np.real(sm[i_s]['Sz']).astype(np.float32))
    return {
        'status': 'refined', 'pump_te_fraction': float(te_p[ip]),
        'sh_label': sp.mode_label(sm[i_s], te_s[i_s], mask), 'sh_te_fraction': float(te_s[i_s]),
        'wavelength_sh': lam, 'wavelength_sh_corrected': lam - (ns_ - np_) / c['slope'],
        'n_eff_pump': np_, 'n_eff_sh': ns_, 'delta_n_residual': np_ - ns_,
        'eta_pct_per_W_cm2': sp.eta_to_pct_per_W_cm2(eta),
        'A_shg_um2': sp.shg_effective_area_um2(eta, np_, ns_, 2 * lam, d_ref),
        'overlap_shape': sp.overlap_shape_factor(fs, fp, d, dA), 'overlap_linear_emode': lin,
        'A_eff_pump_um2': sp.intensity_effective_area_um2(pm[ip], dA),
        'A_eff_sh_um2': sp.intensity_effective_area_um2(sm[i_s], dA),
        'pump_scattering_dB_per_m': scat_p, 'pump_absorption_dB_per_m': abs_p,
        'sh_scattering_dB_per_m': scat_s, 'sh_absorption_dB_per_m': abs_s,
        'L_opt_mm': L_opt * 1e3, 'L_eff_mm': L_eff * 1e3,
        'peak_efficiency_pct_per_W': peak * 100.0,
        'cerenkov_allowed_any': any(f['allowed'] for f in cer),
        'export_path': os.path.relpath(export_path, HERE),
        'pump_identify_similarity': sims_p[ip], 'sh_identify_similarity': sims_s[i_s],
    }


def screened_row(c):
    p = c['pump']
    return {'status': 'screened', 'pump_id': p['id'], 'pump_label': p['label'],
            'pump_sym_class': p['cls'], 'sh_label': c['label_screen'], 'sh_te_fraction': c['te'],
            'sh_track': c['track'], 'wavelength_sh': c['lam'], 'n_eff_pump': c['n_p'],
            'n_eff_sh': c['n_sh'], 'eta_pct_per_W_cm2': sp.eta_to_pct_per_W_cm2(c['eta_screen']),
            'A_shg_um2': c['A_shg_screen'], 'overlap_shape': c['shape_screen'],
            'eta_screen_pct_per_W_cm2': sp.eta_to_pct_per_W_cm2(c['eta_screen']),
            'overlap_shape_screen': c['shape_screen'], 'sh_label_screen': c['label_screen']}


def run_geometry(geom, cfg, run_dir, fp, pumps_only=False):
    lam_sh = np.arange(cfg['lambda_sh_min'], cfg['lambda_sh_max'] + 1e-9, cfg['lambda_step'])
    lam_center = 0.5 * (lam_sh[0] + lam_sh[-1])
    em = pmh.launch_session(f'shg_{fp}', clear='all')
    try:
        geom.build(em, cfg['roughness_rms'], cfg['correlation_length'])
        t0 = time.time()
        em.settings(boundary_condition='0A', wavelength=2 * lam_center,
                    x_resolution=cfg['resolution'], y_resolution=cfg['resolution'], num_modes=1)
        em.FDM()
        x, y, _ = fetch_fields(em)
        dA = sp.cell_areas_m2(x, y)
        pumps = pump_stage(em, cfg, lam_sh, dA)
        for p in pumps:
            p['export'] = os.path.join(run_dir, 'exports', f"{fp}_pump{p['id']}.npz")
            p['info'] = characterize_pump(em, geom, cfg, p, lam_center, p['export'])
            p['label'] = p['info']['label']
        groups = group_pumps(pumps, cfg['pump_group_span'])
        log(run_dir, f"  pumps ({time.time() - t0:.0f}s): " +
            ' | '.join(', '.join(f"{p['label']}[{p['cls']}] {p['info']['n_center']:.4f}" for p in g)
                       for g in groups))
        if pumps_only:
            return pumps, []
        t0 = time.time()
        crossings, traces = sh_scan(em, geom, cfg, lam_sh, pumps, groups)
        cw = traces['coverage_warnings']
        log(run_dir, f"  SH scan ({time.time() - t0:.0f}s): {traces['sh_n'].shape[0]} SH tracks, "
                     f"{len(crossings)} crossings" +
            (f"; WARNING SH n_eff window too narrow at {len(cw)} group-steps "
             f"(raise num_sh_modes)" if len(cw) else ''))
        np.savez_compressed(os.path.join(run_dir, 'traces', f'{fp}.npz'), **traces,
                            pump_labels=np.array([p['label'] for p in pumps]))
        t0 = time.time()
        crossings.sort(key=lambda c: -c['eta_screen'])
        min_eta = cfg['refine_min_nce_pct'] * 1e2  # %/W/cm^2 -> 1/(W m^2)
        rows = []
        for j, c in enumerate(crossings):
            base = {'pump_id': c['pump']['id'], 'pump_label': c['pump']['label'],
                    'pump_sym_class': c['pump']['cls'], 'sh_track': c['track'],
                    'eta_screen_pct_per_W_cm2': sp.eta_to_pct_per_W_cm2(c['eta_screen']),
                    'overlap_shape_screen': c['shape_screen'], 'sh_label_screen': c['label_screen']}
            if j < cfg['refine_top_n'] and c['eta_screen'] >= min_eta:
                path = os.path.join(run_dir, 'exports', f'{fp}_x{j:02d}.npz')
                try:
                    rows.append({**base, **refine_crossing(em, geom, cfg, c, path)})
                    continue
                except Exception as e:  # noqa: BLE001 -- one bad crossing shouldn't lose the rest
                    log(run_dir, f"  crossing {j} refine failed ({e!r}); keeping screened values")
            rows.append({**screened_row(c), **base})
        n_ref = sum(r['status'] == 'refined' for r in rows)
        log(run_dir, f"  refine ({time.time() - t0:.0f}s): {n_ref} refined, "
                     f"{len(rows) - n_ref} screened-only")
    finally:
        em.close(save=False)
    return pumps, rows


def main(run_name, config_module='survey_config', pumps_only=False):
    cfg_mod = importlib.import_module(config_module)
    cfg, geometries = cfg_mod.SETTINGS, cfg_mod.GEOMETRIES
    run_dir = os.path.join(HERE, 'runs', run_name)
    for sub in ('', 'traces', 'exports'):
        os.makedirs(os.path.join(run_dir, sub), exist_ok=True)
    gpath = os.path.join(run_dir, 'geometries.csv')
    done = done_fingerprints(gpath)
    fp_settings = {k: v for k, v in cfg.items() if k not in ('pump_absorption_mechanisms',
                                                            'sh_absorption_mechanisms')}
    todo = []
    for family, params in geometries:
        g = geo.make_geometry(family, params)
        fp = geo.fingerprint(g, fp_settings, cfg['d_tensors_pm'])
        if fp not in done:
            todo.append((g, fp))
    log(run_dir, f"run '{run_name}' ({config_module}): {len(geometries)} geometries, "
                 f"{len(geometries) - len(todo)} already done, {len(todo)} to do")
    t_run = time.time()
    for n, (g, fp) in enumerate(todo, 1):
        log(run_dir, f"[{n}/{len(todo)}] {g.describe()}  ({fp})")
        t0 = time.time()
        base = {'fingerprint': fp, 'family': g.family, 'params': json.dumps(g.params, default=str)}
        try:
            for attempt in (1, 2):
                try:
                    pumps, rows = run_geometry(g, cfg, run_dir, fp, pumps_only)
                    break
                except Exception as e:  # noqa: BLE001
                    log(run_dir, f"  attempt {attempt} failed: {e!r}")
                    if attempt == 2:
                        raise
            append_rows(os.path.join(run_dir, 'pump_modes.csv'), PUMP_FIELDS, [{
                **base, 'pump_id': p['id'], 'label': p['label'], 'sym_class': p['cls'],
                'te_fraction': p['info']['te_fraction'], 'n_eff_center': p['info']['n_center'],
                'n_eff_min': float(np.min(p['n_interp'])), 'n_eff_max': float(np.max(p['n_interp'])),
                'wavelength_pump_center': 2 * float(np.mean(p['lam_pts'])),
                'scattering_dB_per_m': p['info']['scattering'],
                'absorption_dB_per_m': p['info']['absorption'], 'A_eff_um2': p['info']['A_eff'],
                'cerenkov_allowed_any': p['info']['cerenkov_any'],
                'cerenkov_best_angle_deg': p['info']['cerenkov_best_angle'],
                'cerenkov_json': json.dumps(p['info']['cerenkov']),
                'export_path': os.path.relpath(p['export'], HERE)} for p in pumps])
            append_rows(os.path.join(run_dir, 'crossings.csv'), CROSS_FIELDS,
                        [{**base, **r} for r in rows])
            n_ref = sum(r['status'] == 'refined' for r in rows)
            append_rows(gpath, GEOM_FIELDS, [{**base, 'status': 'ok', 'n_pump_modes': len(pumps),
                                              'n_crossings': len(rows), 'n_refined': n_ref,
                                              'seconds': round(time.time() - t0, 1),
                                              'timestamp': datetime.now().isoformat(timespec='seconds')}])
            best = max(rows, key=lambda r: r['eta_pct_per_W_cm2'], default=None)
            log(run_dir, f"  done in {time.time() - t0:.0f}s; " + (
                f"best: {best['pump_label']}->{best['sh_label']} @ {best['wavelength_sh']:.2f} nm, "
                f"NCE {best['eta_pct_per_W_cm2']:.3g} %/W/cm^2 ({best['status']})" if best
                else "no phase matches"))
        except Exception as e:  # noqa: BLE001
            append_rows(gpath, GEOM_FIELDS, [{**base, 'status': 'failed',
                                              'seconds': round(time.time() - t0, 1),
                                              'timestamp': datetime.now().isoformat(timespec='seconds'),
                                              'error': repr(e)[:300]}])
            log(run_dir, f"  FAILED: {e!r}\n{traceback.format_exc()}")
        el = time.time() - t_run
        log(run_dir, f"  elapsed {el / 60:.1f} min, est. remaining "
                     f"{el / n * (len(todo) - n) / 60:.1f} min")


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0] if args else 'trial', args[1] if len(args) > 1 else 'survey_config',
         pumps_only='--pumps-only' in sys.argv)
