"""Fit and report scattering_model.py's calibration_factor(s) against EMode's native scattering
loss, using every point in the completed sweep -- no EMode calls, just the exported mode
profiles already sitting in field_exports/. Vertical (sidewall) and horizontal (top/bottom) are
fit independently, since EMode reports them separately and there's no reason to expect the same
constant applies to both edge orientations.

Run standalone (`python calibrate_scattering.py`) or call fit_and_report() from the notebook,
right after a sweep run. Persists the fit to CALIBRATION_JSON so a later python-only workflow
(exploring roughness assumptions via scattering_model.py alone, without re-running EMode) can
load known-good calibration factors instead of re-deriving them each time -- see
load_calibration().
"""

import json

import numpy as np

import plot_loss_vs_dimensions as plv
import scattering_model as scm
import sweep_loss_vs_dimensions as sw

CALIBRATION_JSON = 'scattering_calibration.json'
N_CLAD = 1.47  # typical fused-silica TopClad index near the pump wavelength -- override if you
# have a better sidewall-cladding index estimate
N_SUBSTRATE = scm.N_SUBSTRATE_DEFAULT  # sapphire (Al2O3) -- see scattering_model.py's comment

sellmeier_n = scm.sellmeier_n  # re-exported for callers already using cs.sellmeier_n(...)


def _least_squares_fit(model_uncal, emode_values):
    """calibration_factor minimizing sum((emode - factor*model)^2), plus R^2 -- the model is
    linear in the factor, so this is a one-line closed-form scalar regression through the origin.
    """
    model_uncal = np.array(model_uncal)
    emode_values = np.array(emode_values)
    factor = float(np.sum(emode_values * model_uncal) / np.sum(model_uncal ** 2))
    calibrated = model_uncal * factor
    ss_res = float(np.sum((emode_values - calibrated) ** 2))
    ss_tot = float(np.sum((emode_values - emode_values.mean()) ** 2))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return factor, r_squared, calibrated


def fit_calibration_factor(rows, n_core, n_clad):
    """Least-squares calibration_factor for SIDEWALL (vertical) scattering, using each row's own
    roughness_rms[0]/correlation_length[0]. Returns (calibration_factor, r_squared, details).
    """
    model_uncal, emode_vertical, details = [], [], []
    for r in rows:
        data = np.load(r['export_path'])
        sigma = json.loads(r['roughness_rms'])[0]
        Lc = json.loads(r['correlation_length'])[0]
        m = scm.compute_scattering_loss(data, n_core, n_clad, sigma, Lc, calibration_factor=1.0)
        model_uncal.append(m)
        emode_vertical.append(r['scattering_vertical_dB_per_m'])
        details.append({'h_core': r['h_core'], 'w_core': r['w_core'],
                         'emode_dB_per_m': r['scattering_vertical_dB_per_m'],
                         'model_uncalibrated_dB_per_m': m})

    factor, r_squared, calibrated = _least_squares_fit(model_uncal, emode_vertical)
    for d, m in zip(details, calibrated):
        d['model_calibrated_dB_per_m'] = float(m)
    return factor, r_squared, details


def fit_horizontal_calibration_factor(rows, n_core, n_clad, n_substrate):
    """Least-squares calibration_factor for TOP+BOTTOM (horizontal) scattering, using each row's
    own roughness_rms[1]/correlation_length[1] (EMode's 'horizontal' element). Returns
    (calibration_factor, r_squared, details).
    """
    model_uncal, emode_horizontal, details = [], [], []
    for r in rows:
        data = np.load(r['export_path'])
        sigma = json.loads(r['roughness_rms'])[1]
        Lc = json.loads(r['correlation_length'])[1]
        m = scm.payne_lacey_top_bottom_scattering_loss_dB_per_m(
            data['x'], data['y'], data['core_mask'], data['Ex'], data['Ey'], data['Ez'],
            data['Sz'], float(data['n_eff']), float(data['wavelength_pump']),
            n_core, n_clad, n_substrate, sigma, Lc, calibration_factor=1.0)
        model_uncal.append(m)
        emode_horizontal.append(r['scattering_horizontal_dB_per_m'])
        details.append({'h_core': r['h_core'], 'w_core': r['w_core'],
                         'emode_dB_per_m': r['scattering_horizontal_dB_per_m'],
                         'model_uncalibrated_dB_per_m': m})

    factor, r_squared, calibrated = _least_squares_fit(model_uncal, emode_horizontal)
    for d, m in zip(details, calibrated):
        d['model_calibrated_dB_per_m'] = float(m)
    return factor, r_squared, details


def _print_report(label, n_core, n_clad, extra, factor, r_squared, details, n_points):
    print(f"Fitted {label} calibration_factor = {factor:.6g} (R^2={r_squared:.4f}, "
          f"n_core={n_core:.4f}, n_clad={n_clad:.4f}{extra}, {n_points} point(s))\n")
    print(f"{'h':>6} {'w':>6} {'EMode':>12} {'PL uncal.':>12} {'PL cal.':>10} {'ratio':>8}")
    for d in details:
        ratio = (d['model_calibrated_dB_per_m'] / d['emode_dB_per_m']
                  if d['emode_dB_per_m'] else float('nan'))
        print(f"{d['h_core']:>6.0f} {d['w_core']:>6.0f} {d['emode_dB_per_m']:>12.4g} "
              f"{d['model_uncalibrated_dB_per_m']:>12.4g} {d['model_calibrated_dB_per_m']:>10.4g} "
              f"{ratio:>8.3f}")
    print()


def fit_and_report(results_csv=None, n_core=None, n_clad=N_CLAD, n_substrate=N_SUBSTRATE,
                    save=True):
    """Load the sweep's results, fit vertical and horizontal calibration_factors independently,
    print per-point reports for both, and persist the fits to CALIBRATION_JSON (unless
    save=False).
    """
    results_csv = results_csv or sw.RESULTS_CSV
    n_core = n_core if n_core is not None else sellmeier_n(sw.EQ_O, sw.WAVELENGTH_PUMP)

    rows = plv.load_results(results_csv)
    if not rows:
        print(f"No completed points in {results_csv} -- nothing to calibrate against.")
        return None

    calibration_factor, r_squared, details = fit_calibration_factor(rows, n_core, n_clad)
    _print_report('sidewall (vertical)', n_core, n_clad, '', calibration_factor, r_squared,
                   details, len(rows))

    cal_h, r2_h, details_h = fit_horizontal_calibration_factor(rows, n_core, n_clad, n_substrate)
    _print_report('top/bottom (horizontal)', n_core, n_clad, f', n_substrate={n_substrate:.4f}',
                   cal_h, r2_h, details_h, len(rows))

    record = {'calibration_factor': calibration_factor, 'r_squared': r_squared,
              'calibration_factor_horizontal': cal_h, 'r_squared_horizontal': r2_h,
              'n_core': n_core, 'n_clad': n_clad, 'n_substrate': n_substrate,
              'n_points': len(rows), 'results_csv': results_csv}
    if save:
        with open(CALIBRATION_JSON, 'w') as f:
            json.dump(record, f, indent=2)
        print(f"Saved {CALIBRATION_JSON}")
    return record


def load_calibration(path=CALIBRATION_JSON):
    """Reload a previously-saved fit -- e.g. record['calibration_factor'] for use with
    scattering_model.py without needing EMode data or re-fitting.
    """
    with open(path) as f:
        return json.load(f)


if __name__ == '__main__':
    fit_and_report()
