"""Compares two pump (blue, 430-470nm) absorption-mechanism assumption sets against each other,
as a function of ridge core width at fixed h_core=350nm, using trial_grid's already-exported TM00
pump fields (no new EMode calls needed). Requested 2026-10-12: rather than resolve which set is
"right", quantify how much they actually disagree, log the comparison, and keep the current
survey_config.py assumptions if the gap isn't large.

CODE_MECHANISMS = survey_config.py's actual current pump_absorption_mechanisms.
DOC_MECHANISMS = the "Actual Inputs Used" table from the "Loss Model Summary & Results" memo
(Google Drive, internal, 2026-09-22) -- see PLAN.md for the full discrepancy writeup. Also
includes that memo's 2 nonzero sidewall mechanisms, which CODE_MECHANISMS omits entirely.

Scattering: the two sources also differ on sidewall roughness RMS (2.5nm current vs 2.0nm in the
memo). Native EMode scattering isn't cheaply recomputable from exported fields alone (it's
EMode's own internal calculation, not reproducible by post-processing) without a fresh solve, so
this script approximates the effect analytically: Payne-Lacey/VCM-type roughness scattering goes
as roughness_rms^2, so the sidewall component is scaled by (2.0/2.5)^2 = 0.64x; the unchanged
horizontal (top/bottom, 0.3nm both sources) component should NOT scale, but the stored
`scattering_dB_per_m` in pump_modes.csv is only the combined (sidewall+horizontal) value, not
split -- so the 0.64x factor is applied to the WHOLE combined number as a (slightly
over-correcting) approximation. Flagged clearly in the output; treat the scattering-side
comparison as a rougher estimate than the absorption-side one.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, '.')
import geometry as geo  # noqa: E402
import absorption_model as am  # noqa: E402

CODE_MECHANISMS = [
    {'name': 'Dislocations (growth interface)', 'localization': 'interface', 'shape': 'exp', 'alpha0': 0.2e4, 'L': 40.0},
    {'name': 'C impurities (growth interface)', 'localization': 'interface', 'shape': 'step', 'alpha0': 0.35e4, 'L': 50.0},
    {'name': 'Si impurities (growth interface)', 'localization': 'interface', 'shape': 'step', 'alpha0': 0.35e4, 'L': 50.0},
    {'name': 'O impurities (growth interface)', 'localization': 'interface', 'shape': 'step', 'alpha0': 0.5e4, 'L': 50.0},
]
CODE_SIGMA_SIDEWALL_NM = 2.5

DOC_MECHANISMS = [
    {'name': 'Dislocations (growth interface)', 'localization': 'interface', 'shape': 'exp', 'alpha0': 1.0e4 / 4, 'L': 40.0},
    {'name': 'C impurities (growth interface)', 'localization': 'interface', 'shape': 'exp', 'alpha0': 1.5e4 / 4, 'L': 20.0},
    {'name': 'Si impurities (growth interface)', 'localization': 'interface', 'shape': 'exp', 'alpha0': 1.0e4 / 4, 'L': 20.0},
    {'name': 'O impurities (growth interface)', 'localization': 'interface', 'shape': 'exp', 'alpha0': 2.0e4 / 4, 'L': 20.0},
    {'name': 'Oxidation ingress (sidewall)', 'localization': 'sidewall', 'shape': 'exp', 'alpha0': 2.0e4 / 4, 'L': 20.0},
    {'name': 'Sidewall contamination (Si)', 'localization': 'sidewall', 'shape': 'step', 'alpha0': 1.5e4 / 4, 'L': 15.0},
    {'name': 'Sidewall damage', 'localization': 'sidewall', 'shape': 'exp', 'alpha0': 0.0e4 / 4, 'L': 50.0},
]
DOC_SIGMA_SIDEWALL_NM = 2.0
SCATTER_SCALE = (DOC_SIGMA_SIDEWALL_NM / CODE_SIGMA_SIDEWALL_NM) ** 2

H_CORE = 350.0


def main():
    g = pd.read_csv('runs/trial_grid/geometries.csv')
    p = pd.read_csv('runs/trial_grid/pump_modes.csv')
    g['h_core'] = g['params'].apply(lambda s: json.loads(s)['h_core'])
    g['w_core'] = g['params'].apply(lambda s: json.loads(s)['w_core'])
    h_rows = g[g['h_core'] == H_CORE]
    m = p.merge(h_rows[['fingerprint', 'h_core', 'w_core']], on='fingerprint')
    tm00 = m[(m['label'] == 'TM00') & m['export_path'].notna()].sort_values('w_core')
    tm00 = tm00.drop_duplicates(subset='w_core', keep='last')

    rows = []
    for _, r in tm00.iterrows():
        d = np.load(os.path.join('..', r['export_path']) if not os.path.exists(r['export_path'])
                    else r['export_path'])
        x, y = d['x'], d['y']
        Sz = np.real(d['Ex'] * np.conj(d['Hy']) - d['Ey'] * np.conj(d['Hx']))
        core_mask = geo.make_geometry('ridge', {'h_core': H_CORE, 'w_core': float(r['w_core'])}).core_mask(x, y)
        dx = float(x[1] - x[0])

        abs_code = sum(am.compute_mechanism_losses(core_mask, dx, y, Sz, CODE_MECHANISMS).values())
        abs_doc = sum(am.compute_mechanism_losses(core_mask, dx, y, Sz, DOC_MECHANISMS).values())
        scat_code = float(r['scattering_dB_per_m'])
        scat_doc_approx = scat_code * SCATTER_SCALE

        rows.append({
            'w_core': r['w_core'],
            'abs_code_dB_per_cm': abs_code / 100, 'abs_doc_dB_per_cm': abs_doc / 100,
            'scat_code_dB_per_cm': scat_code / 100, 'scat_doc_approx_dB_per_cm': scat_doc_approx / 100,
            'total_code_dB_per_cm': (abs_code + scat_code) / 100,
            'total_doc_dB_per_cm': (abs_doc + scat_doc_approx) / 100,
        })

    df = pd.DataFrame(rows).sort_values('w_core')
    df['ratio_doc_over_code'] = df['total_doc_dB_per_cm'] / df['total_code_dB_per_cm']
    print(df.to_string(index=False))
    df.to_csv('runs/pump_loss_assumption_comparison.csv', index=False)
    return df


if __name__ == '__main__':
    main()
