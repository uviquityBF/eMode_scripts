"""EMode-native vs Payne-Lacey-adapted sidewall scattering vs wavelength, for the TM00 and TM04 modes of
ridge h=350, w=400 at several sidewall correlation lengths (constant sidewall rms). Feeds
plot_scattering_models.py. Payne-Lacey = loss_vs_dimensions/scattering_model.py (uncalibrated adaptation,
SiO2 sidewall cladding, AlN n_o). EMode value = em.scattering() summed over the ridge shape (sidewall +
top/bottom with the survey's 0.3 nm top/bottom roughness); PL value = sidewall only.

TM00 = highest-n_eff TM-like x-even mode at each wavelength (220..600 nm, 20 nm steps).
TM04 = the survey's phase-matched SH mode: anchored at 230 nm (label 'TM04' from shg_physics.mode_label, n_eff
nearest 2.04), then FOLLOWED up (to 450 nm) and down (to 220 nm) in 10 nm steps by transverse field
similarity (shg_physics.transverse_similarity, the survey tracker's metric; stops when similarity < MIN_SIM).
`bound` = n_eff above the largest bulk cladding/substrate index (guided); unbound points are leaky, so their
scattering is not meaningful and the plot marks them separately.
Usage: python compute_scattering_models_vs_lambda.py [Lc ...]   (default 2 10 50)
Writes materials/scattering_models_vs_lambda.csv (resumes by (Lc, lambda, mode)).
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'loss_vs_dimensions'))
import geometry as geo  # noqa: E402
import emode_helpers as pmh  # noqa: E402
import survey  # noqa: E402
import shg_physics as sp  # noqa: E402
import scattering_model as pl  # noqa: E402
from survey_config import SETTINGS as CFG  # noqa: E402

OUT = os.path.join(HERE, 'materials', 'scattering_models_vs_lambda.csv')
FIELDS = ['Lc_nm', 'lambda_nm', 'mode', 'n_eff', 'emode_dB_per_cm', 'payne_lacey_dB_per_cm', 'bound', 'similarity']
TM00_LAMS = list(range(220, 601, 20))
TM04_ANCHOR = 230
TM04_UP = list(range(240, 451, 10))
TM04_DOWN = [220]
MIN_SIM = 0.5
STEP = 2


def n_sio2(l):  # Malitson
    x = l / 1000.0
    return float(np.sqrt(1 + .6961663 * x**2 / (x**2 - .0684043**2) + .4079426 * x**2 / (x**2 - .1162414**2)
                         + .8974794 * x**2 / (x**2 - 9.896161**2)))


class Session:
    def __init__(self, geom, lc):
        self.geom, self.lc, self.em = geom, lc, None

    def open(self):
        if self.em is None:
            self.em = pmh.launch_session(f'scat_models_{int(self.lc)}', clear='all')
            self.geom.build(self.em, CFG['roughness_rms'], [float(self.lc), CFG['correlation_length'][1]])
            self.em.settings(boundary_condition='0A')

    def drop(self):
        try:
            self.em.close(save=False)
        except Exception:  # noqa: BLE001
            pass
        self.em = None

    def solve(self, lam):
        self.open()
        n, te = survey.solve(self.em, 'ref', wavelength=float(lam), num_modes=40, max_effective_index=0,
                             x_resolution=CFG['resolution'], y_resolution=CFG['resolution'])
        x, y, modes = survey.fetch_fields(self.em, survey.SCAN_KEYS)
        return n, te, x, y, modes

    def measure(self, lam, i, n, x, y, modes):
        f = modes[i]
        mask = self.geom.core_mask(x, y)
        a_pl = pl.payne_lacey_sidewall_scattering_loss_dB_per_m(
            x, y, mask, f['Ex'], f['Ey'], f['Ez'], f['Sz'], float(n[i].real), lam,
            geo.eval_index_equation(geo.AlN_EQ_O, lam), n_sio2(lam),
            CFG['roughness_rms'][0], float(self.lc)) / 100.0
        a_em = survey.native_scattering(self.em, i, self.geom.scatter_shapes) / 100.0
        cut = max(r['n'] for r in self.geom.cerenkov_regions(self.em, float(lam)) if r['extent'] == 'bulk')
        return a_em, a_pl, bool(n[i].real > cut)


def with_retry(sess, fn):
    for attempt in range(3):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            print(f"  attempt {attempt + 1} failed: {e!r}", flush=True)
            sess.drop()
    return None


def main(lcs):
    geom = geo.make_geometry('ridge', {'h_core': 350.0, 'w_core': 400.0})
    rows = list(csv.DictReader(open(OUT, newline=''))) if os.path.exists(OUT) else []
    done = {(float(r['Lc_nm']), float(r['lambda_nm']), r['mode']) for r in rows}

    def save():
        with open(OUT, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction='ignore', restval='')
            w.writeheader()
            w.writerows(rows)

    def record(lc, lam, mode, n_eff, a_em, a_pl, bound, sim):
        rows.append({'Lc_nm': lc, 'lambda_nm': lam, 'mode': mode, 'n_eff': n_eff, 'emode_dB_per_cm': a_em,
                     'payne_lacey_dB_per_cm': a_pl, 'bound': int(bound), 'similarity': sim})
        print(f"Lc={lc:g} {lam} {mode} n={n_eff:.3f} EMode={a_em:.4g} PL={a_pl:.4g} bound={bound} sim={sim:.2f}", flush=True)
        save()

    for lc in lcs:
        sess = Session(geom, lc)
        # ---- TM00
        for lam in TM00_LAMS:
            if (float(lc), float(lam), 'TM00') in done:
                continue

            def job():
                n, te, x, y, modes = sess.solve(lam)
                i = next(int(j) for j in np.argsort(-n.real) if te[j] < 0.5)
                return (float(n[i].real),) + sess.measure(lam, i, n, x, y, modes)
            r = with_retry(sess, job)
            if r:
                record(lc, lam, 'TM00', r[0], r[1], r[2], r[3], 1.0)
        # ---- TM04: anchor, then follow by similarity
        if (float(lc), float(TM04_ANCHOR), 'TM04') in done and all(
                (float(lc), float(l), 'TM04') in done for l in TM04_UP + TM04_DOWN):
            continue
        prev, dA = None, None
        walk = [('anchor', TM04_ANCHOR)] + [('up', l) for l in TM04_UP]
        for direction, lam in walk:
            def job():
                n, te, x, y, modes = sess.solve(lam)
                mask = sess.geom.core_mask(x, y)
                dA_s = (x[1] - x[0]) * 1e-9 * (y[1] - y[0]) * 1e-9 * STEP * STEP
                if direction == 'anchor':
                    cand = [j for j in range(len(n)) if te[j] < 0.5 and sp.mode_label(modes[j], te[j], mask) == 'TM04']
                    i = min(cand, key=lambda j: abs(n[j].real - 2.04)); sim = 1.0
                else:
                    sims = {j: sp.transverse_similarity(prev, survey.small(modes[j], STEP), dA_s)
                            for j in range(len(n)) if te[j] < 0.5}
                    i = max(sims, key=sims.get); sim = sims[i]
                    if sim < MIN_SIM:
                        return ('lost', sim)
                return ('ok', i, sim, survey.small(modes[i], STEP), dA_s) + (float(n[i].real),) + sess.measure(lam, i, n, x, y, modes)
            r = with_retry(sess, job)
            if r is None or r[0] == 'lost':
                print(f"Lc={lc:g} {lam}: TM04 track lost ({r})", flush=True)
                break
            _, i, sim, prev, dA, n_eff, a_em, a_pl, bound = r
            if direction == 'anchor':
                anchor_small = prev
            if (float(lc), float(lam), 'TM04') not in done:
                record(lc, lam, 'TM04', n_eff, a_em, a_pl, bound, sim)
        prev = anchor_small if 'anchor_small' in dir() else None
        for lam in TM04_DOWN:
            def job():
                n, te, x, y, modes = sess.solve(lam)
                dA_s = (x[1] - x[0]) * 1e-9 * (y[1] - y[0]) * 1e-9 * STEP * STEP
                sims = {j: sp.transverse_similarity(prev, survey.small(modes[j], STEP), dA_s)
                        for j in range(len(n)) if te[j] < 0.5}
                i = max(sims, key=sims.get)
                if sims[i] < MIN_SIM:
                    return ('lost', sims[i])
                return ('ok', i, sims[i], float(n[i].real)) + sess.measure(lam, i, n, x, y, modes)
            r = with_retry(sess, job)
            if r and r[0] == 'ok' and (float(lc), float(lam), 'TM04') not in done:
                record(lc, lam, 'TM04', r[3], r[4], r[5], r[6], r[2])
            else:
                print(f"Lc={lc:g} {lam}: TM04 track lost ({r})", flush=True)
        if sess.em is not None:
            sess.drop()
    print('wrote', OUT)


if __name__ == '__main__':
    main([float(a) for a in sys.argv[1:]] or [2.0, 10.0, 50.0])
