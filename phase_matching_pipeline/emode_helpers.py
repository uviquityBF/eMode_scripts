"""Reusable EMode session/geometry/mode-tracking helpers, factored out of AlN_2D_4_sweep.ipynb.

See EMode_Troubleshooting_Log.md and EMode_Function_Reference.md for the backend quirks these
helpers work around.
"""

import csv
import os
from datetime import datetime

import numpy as np
import emodeconnection as emc


def log_failed_point(step, mode_name, h, w, reason, detail='', csv_path='failed_points.csv'):
    """Append one row to a shared, cross-step log of failed/untrustworthy geometry points, so this
    history survives a re-run instead of only appearing in that run's live notebook output (which
    scrolls away and isn't checked automatically on resume).

    `step` is a free-form label for which pipeline stage this came from (e.g. 'walk',
    'crossing_gradient', 'overlap'); `reason` a short machine-friendly tag (e.g. 'exception',
    'no_crossing', 'low_overlap', 'saturated'); `detail` any extra free-text (exception repr, etc).
    """
    fieldnames = ['timestamp', 'step', 'target_mode_name', 'h_core', 'w_core', 'reason', 'detail']
    write_header = not (os.path.exists(csv_path) and os.path.getsize(csv_path) > 0)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({'timestamp': datetime.now().isoformat(timespec='seconds'),
                          'step': step, 'target_mode_name': mode_name,
                          'h_core': h, 'w_core': w, 'reason': reason, 'detail': detail})


def launch_session(simulation_name, clear='all', verbose=False):
    """Launch a fresh EMode session.

    clear='all' clears orphaned license checkouts left by crashed prior sessions, but it also
    kills any OTHER EMode session currently open on this machine -- don't use this if you have
    other notebooks with live EMode sessions you want to keep.

    verbose=True, combined with the EMODE_LOG_SECRET environment variable (see EMode support's
    debug instructions in EMode_Troubleshooting_Log.md), captures extra diagnostic output --
    useful for reproducing the EMode.exe crash-under-sustained-load issue for their review.
    """
    return emc.EMode(simulation_name=simulation_name, clear=clear, verbose=verbose)


def em_save(em, **kwargs):
    """em.save(...) is shadowed by the `save: bool` instance attribute EMode.__init__ sets on
    self, so it never reaches the real EM_save backend call. call() bypasses that shadowing.
    """
    return em.call("EM_save", **kwargs)


def set_core_width(em, h_core, w_core, material_name='custom_AlN', sidewall_angle=5):
    em.shape(name='core', material=material_name, height=h_core, mask=w_core,
             etch_depth=h_core, sidewall_angle=sidewall_angle)


def setup_waveguide(em, anisotropic_equation, h_core, w_core, *,
                     window_width=2000, window_margin=2000, boundary_condition='TM',
                     material_name='custom_AlN',
                     substrate_material='Al2O3', substrate_height=1000,
                     topclad_material='SiO2', topclad_height=800,
                     sidewall_angle=5):
    """Add the custom material and define the Substrate/core/TopClad shapes for a fresh session."""
    em.add_material(name=material_name, refractive_index_equation=anisotropic_equation,
                     wavelength_unit='um')
    em.settings(window_width=window_width, window_height=h_core + window_margin,
                boundary_condition=boundary_condition)
    em.shape(name='Substrate', material=substrate_material, height=substrate_height)
    set_core_width(em, h_core, w_core, material_name=material_name, sidewall_angle=sidewall_angle)
    em.shape(name='TopClad', material=topclad_material, height=topclad_height, shape_type='conformal')


def solve_modes(em, label, **settings_kwargs):
    """Apply settings_kwargs via em.settings(), solve FDM, and label the resulting profile.

    Returns FDM()'s own return dict, which includes `n_eff_tilde` (per-mode effective index) --
    reading it directly from here avoids a separate get()/sweep() call for a single-point value.
    """
    em.settings(**settings_kwargs)
    result = em.FDM()
    em.label_profile(name=label)
    return result


def track_mode(em, ref_label, ref_mode_idx, cur_label, num_modes, window=5):
    """Identify which mode in cur_label is the continuation of mode ref_mode_idx in ref_label,
    by spatial overlap rather than raw index number.

    Mode index alone is not reliable: it can shift even between two separate FDM solves at the
    identical width/wavelength/settings (observed empirically -- a marginal mode near the
    max_effective_index cutoff flickering in/out of the returned set shifts everything after it).
    Only searches indices within +/-window of ref_mode_idx, not the full 0..num_modes-1 range, to
    limit the number of overlap() calls -- repeated large batches of overlap() calls have been
    observed to crash EMode.exe on this machine.

    Returns (best_idx, best_overlap, overlaps_dict).
    """
    candidates = range(max(0, ref_mode_idx - window), min(num_modes, ref_mode_idx + window + 1))
    overlaps = {m: abs(em.overlap(label_a=ref_label, mode_a=ref_mode_idx, label_b=cur_label, mode_b=m))
                for m in candidates}
    best_idx = max(overlaps, key=overlaps.get)
    return best_idx, overlaps[best_idx], overlaps


def solve_and_identify(anisotropic_equation, anchor, anchor_mode_idx, target, num_modes,
                        window=5, x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                        sidewall_angle=5, simulation_name='solve_and_identify', verbose=False):
    """Re-identify a mode at `target` = (h_core, w_core, wavelength) via overlap against a known
    mode at `anchor` = (h_core, w_core, wavelength).

    Launches its own fresh session and re-solves the anchor point too (a labeled profile doesn't
    survive a session relaunch), keeping each evaluation isolated -- EMode.exe has been observed
    to become unstable under sustained/repeated computation within one long-lived session, so this
    trades some redundant re-solving for resilience (a crash here only costs this one evaluation).

    Returns {'mode_idx', 'overlap', 'n_eff'} for the target point.
    """
    h_a, w_a, wl_a = anchor
    h_t, w_t, wl_t = target

    em = launch_session(simulation_name, verbose=verbose)
    try:
        setup_waveguide(em, anisotropic_equation, h_a, w_a, sidewall_angle=sidewall_angle)
        solve_modes(em, 'anchor', wavelength=wl_a, num_modes=num_modes,
                    x_resolution=x_resolution, y_resolution=y_resolution,
                    max_effective_index=max_effective_index)

        set_core_width(em, h_t, w_t, sidewall_angle=sidewall_angle)
        target_fdm = solve_modes(em, 'target', wavelength=wl_t, num_modes=num_modes,
                                  x_resolution=x_resolution, y_resolution=y_resolution,
                                  max_effective_index=max_effective_index)

        mode_idx, overlap, _ = track_mode(em, 'anchor', anchor_mode_idx, 'target', num_modes, window=window)
        # n_eff_tilde is complex-typed (can carry gain/loss); .real since nothing in this model has loss
        n_eff = target_fdm['n_eff_tilde'][mode_idx].real
    finally:
        em.close(save=False)

    return {'mode_idx': mode_idx, 'overlap': overlap, 'n_eff': n_eff}


def find_crossing(anisotropic_equation, h_core, w_core, wavelengths_shg,
                   fund_mode_idx=0, target_mode_idx=30,
                   num_modes_fund=2, num_modes_target=35,
                   x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                   simulation_name='find_crossing', verbose=False):
    """Find where n_eff(fundamental, at 2x wavelength) crosses n_eff(target mode, at wavelength)
    over the `wavelengths_shg` grid, plus the local dn/dWL slope for each mode at the crossing --
    read from the same sweep data via np.gradient + interpolation, no extra EMode calls needed.

    Assumes fund_mode_idx/target_mode_idx are already correct AT THIS (h_core, w_core) -- use
    solve_and_identify/track_mode first if they aren't already known for this exact point. Uses
    sweep()'s built-in step-to-step continuity for the wavelength axis (already validated to hold
    up across a single sweep call), unlike width/height where mode index has been shown to shift.

    Returns None if no crossing exists in this window, else a dict with the crossing
    wavelength/n_eff and dn_dWL for both modes.
    """
    wavelengths_shg = np.asarray(wavelengths_shg)
    em = launch_session(simulation_name, verbose=verbose)
    try:
        setup_waveguide(em, anisotropic_equation, h_core, w_core)

        em.settings(x_resolution=x_resolution, y_resolution=y_resolution, num_modes=num_modes_fund)
        data_fund = em.sweep(key='wavelength', values=2 * wavelengths_shg, result=['effective_index'])
        n_fund = np.array(data_fund['effective_index'])[:, fund_mode_idx]

        em.settings(num_modes=num_modes_target, max_effective_index=max_effective_index)
        data_target = em.sweep(key='wavelength', values=wavelengths_shg, result=['effective_index'])
        n_target = np.array(data_target['effective_index'])[:, target_mode_idx]
    finally:
        em.close(save=False)

    delta_n = n_fund - n_target
    if np.sign(delta_n[0]) == np.sign(delta_n[-1]):
        return None

    # np.interp needs its xp array increasing; this assumes delta_n is monotonic across the window
    # (matches the assumption already made in the original notebook's crossing-finding cell).
    wl_cross = np.interp(0, delta_n, wavelengths_shg)
    return {
        'wavelength_shg': wl_cross,
        'n_eff': np.interp(wl_cross, wavelengths_shg, n_target),
        'dn_dWL_fund': np.interp(wl_cross, wavelengths_shg, np.gradient(n_fund, wavelengths_shg)),
        'dn_dWL_target': np.interp(wl_cross, wavelengths_shg, np.gradient(n_target, wavelengths_shg)),
    }


def mode_gradient_width_height(anisotropic_equation, base_point, base_mode_idx, num_modes,
                                d_width=5.0, d_height=5.0, window=5, overlap_threshold=0.9,
                                x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                                simulation_name='mode_gradient', verbose=False):
    """Central-difference dn/dwidth and dn/dheight for one mode at base_point =
    (h_core, w_core, wavelength), each step tracked via overlap against base_point/base_mode_idx
    directly (not a walking chain), so tracking error can't accumulate across the 4 evaluations.

    Each perturbation is only a small (+-d_width/d_height, default 5nm) displacement, so it's
    normally very reliable -- but a genuine near-degeneracy can still occasionally make one step
    track a different physical mode instead of a true continuation, silently producing a wildly
    wrong derivative (observed directly: a handful of points came back with dWL/dwidth 10-50x the
    surrounding trend). `overlap_threshold` guards against this: if EITHER side of a
    central-difference pair has overlap below it, that gradient comes back as None rather than a
    wrong number -- callers (see `phase_matching_row`) should treat None as "not computed, don't
    trust or plot this," not as a real zero.

    Also returns the raw solve_and_identify() result for each of the 4 perturbation points
    ('w_plus', 'w_minus', 'h_plus', 'h_minus') so the overlap values behind the check above (or a
    None result) can be inspected directly if needed.
    """
    h0, w0, wl0 = base_point

    def solve_at(h, w):
        return solve_and_identify(anisotropic_equation, base_point, base_mode_idx, (h, w, wl0),
                                   num_modes, window=window, x_resolution=x_resolution,
                                   y_resolution=y_resolution, max_effective_index=max_effective_index,
                                   simulation_name=simulation_name, verbose=verbose)

    w_plus = solve_at(h0, w0 + d_width)
    w_minus = solve_at(h0, w0 - d_width)
    h_plus = solve_at(h0 + d_height, w0)
    h_minus = solve_at(h0 - d_height, w0)

    dn_dw = None
    if w_plus['overlap'] >= overlap_threshold and w_minus['overlap'] >= overlap_threshold:
        dn_dw = (w_plus['n_eff'] - w_minus['n_eff']) / (2 * d_width)
    dn_dh = None
    if h_plus['overlap'] >= overlap_threshold and h_minus['overlap'] >= overlap_threshold:
        dn_dh = (h_plus['n_eff'] - h_minus['n_eff']) / (2 * d_height)

    return {
        'dn_dwidth': dn_dw, 'dn_dheight': dn_dh,
        'w_plus': w_plus, 'w_minus': w_minus, 'h_plus': h_plus, 'h_minus': h_minus,
    }


def implicit_wavelength_gradient(fund_grad, target_grad, crossing):
    """d(phase-matching wavelength)/d(width) and .../d(height), via the implicit function theorem
    on F(WL,w,h) = n_fund(WL,w,h) - n_target(WL,w,h) = 0.

    Either result is None if the dn_dwidth/dn_dheight it depends on came back None (unreliable,
    see mode_gradient_width_height) for the fundamental or target mode.
    """
    F_WL = crossing['dn_dWL_fund'] - crossing['dn_dWL_target']
    F_w = None
    if fund_grad['dn_dwidth'] is not None and target_grad['dn_dwidth'] is not None:
        F_w = fund_grad['dn_dwidth'] - target_grad['dn_dwidth']
    F_h = None
    if fund_grad['dn_dheight'] is not None and target_grad['dn_dheight'] is not None:
        F_h = fund_grad['dn_dheight'] - target_grad['dn_dheight']
    return {
        'dWL_dwidth': -F_w / F_WL if F_w is not None else None,
        'dWL_dheight': -F_h / F_WL if F_h is not None else None,
    }


def phase_matching_row(anisotropic_equation, h_core, w_core, wavelengths_shg, target_mode_idx,
                        target_mode_name='target', fund_mode_idx=0,
                        num_modes_fund=6, num_modes_target=35,
                        d_width=5.0, d_height=5.0, window=5, grad_overlap_threshold=0.9,
                        x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                        verbose=False):
    """One full phase-matching table row: crossing point, per-mode dn/dWL, per-mode dn/dwidth and
    dn/dheight, and the derived d(PM wavelength)/d(width)/d(height) -- combines find_crossing,
    mode_gradient_width_height (both modes), and implicit_wavelength_gradient.

    Assumes target_mode_idx is already correct AT THIS (h_core, w_core) -- confirm via em.plot()
    or solve_and_identify first; mode index is not guaranteed stable across geometry changes (see
    EMode_Troubleshooting_Log.md).

    `grad_overlap_threshold` is passed through to mode_gradient_width_height for both the
    fundamental and target mode -- a gradient whose underlying perturbation tracked unreliably
    comes back as None in the returned row (dn_dwidth_fund/dn_dwidth_target/dWL_dwidth, and/or the
    height equivalents) rather than a silently wrong value. The crossing wavelength/n_eff
    themselves are unaffected either way, since they come from the already-verified main tracked
    mode, not from these perturbation steps.

    Returns None if find_crossing finds no crossing in wavelengths_shg, else a flat dict (ready to
    collect into a table alongside other rows).
    """
    crossing = find_crossing(anisotropic_equation, h_core, w_core, wavelengths_shg,
                              fund_mode_idx=fund_mode_idx, target_mode_idx=target_mode_idx,
                              num_modes_fund=num_modes_fund, num_modes_target=num_modes_target,
                              x_resolution=x_resolution, y_resolution=y_resolution,
                              max_effective_index=max_effective_index, verbose=verbose)
    if crossing is None:
        return None

    fund_base_point = (h_core, w_core, 2 * crossing['wavelength_shg'])
    fund_grad = mode_gradient_width_height(anisotropic_equation, fund_base_point, fund_mode_idx,
                                            num_modes=num_modes_fund, d_width=d_width, d_height=d_height,
                                            window=window, overlap_threshold=grad_overlap_threshold,
                                            x_resolution=x_resolution, y_resolution=y_resolution,
                                            max_effective_index=max_effective_index, verbose=verbose)

    target_base_point = (h_core, w_core, crossing['wavelength_shg'])
    target_grad = mode_gradient_width_height(anisotropic_equation, target_base_point, target_mode_idx,
                                              num_modes=num_modes_target, d_width=d_width, d_height=d_height,
                                              window=window, overlap_threshold=grad_overlap_threshold,
                                              x_resolution=x_resolution, y_resolution=y_resolution,
                                              max_effective_index=max_effective_index, verbose=verbose)

    wl_grad = implicit_wavelength_gradient(fund_grad, target_grad, crossing)

    return {
        'target_mode_name': target_mode_name,
        'target_mode_idx': target_mode_idx,
        'h_core': h_core,
        'w_core': w_core,
        'wavelength_shg': crossing['wavelength_shg'],
        'n_eff': crossing['n_eff'],
        'dn_dWL_fund': crossing['dn_dWL_fund'],
        'dn_dWL_target': crossing['dn_dWL_target'],
        'dn_dwidth_fund': fund_grad['dn_dwidth'],
        'dn_dwidth_target': target_grad['dn_dwidth'],
        'dn_dheight_fund': fund_grad['dn_dheight'],
        'dn_dheight_target': target_grad['dn_dheight'],
        'dWL_dwidth': wl_grad['dWL_dwidth'],
        'dWL_dheight': wl_grad['dWL_dheight'],
    }


def sweep_crossing(anisotropic_equation, anchor_point, anchor_mode_idx, targets, wavelengths_shg,
                    num_modes=50, window=20, x_resolution=10.0, y_resolution=10.0,
                    max_effective_index=2.6, verbose=False):
    """For each (h, w) in `targets`, track the continuation of `anchor_mode_idx` from
    `anchor_point` = (h, w, wavelength) via solve_and_identify, then find its crossing with the
    fundamental over `wavelengths_shg`, re-verifying mode identity AT the crossing wavelength too
    (not just the tracking wavelength -- they can differ a lot for big geometry jumps).

    Generalizes the width-only overnight batch to arbitrary (h, w) points, for both height and
    width sweeps and for any mode (not just TM04). Resilient: a failure or no-crossing at one
    point doesn't stop the rest.

    Returns a dict keyed by (h, w) -> None (failed/no crossing) or a result dict with 'mode_idx',
    'overlap', 'recheck_overlap', 'recheck_mode_idx', 'crossing', and 'trusted' (bool: both
    overlaps >= 0.8 and both checks agree on mode index).
    """
    anchor_h, anchor_w, anchor_wl = anchor_point
    results = {}
    for (h, w) in targets:
        key = (h, w)
        print(f"\n=== Point h={h}, w={w} ===")
        try:
            id_result = solve_and_identify(anisotropic_equation, anchor_point, anchor_mode_idx,
                                            (h, w, anchor_wl), num_modes=num_modes, window=window,
                                            x_resolution=x_resolution, y_resolution=y_resolution,
                                            max_effective_index=max_effective_index, verbose=verbose)
            print(f"  [Check 1/2] Tracked at anchor WL={anchor_wl:.3f}nm: mode index {id_result['mode_idx']}, overlap={id_result['overlap']:.4f}")
            if id_result['overlap'] < 0.8:
                print("  WARNING: low overlap at tracking step.")

            crossing = find_crossing(anisotropic_equation, h, w, wavelengths_shg,
                                      fund_mode_idx=0, target_mode_idx=id_result['mode_idx'],
                                      num_modes_fund=2, num_modes_target=num_modes,
                                      x_resolution=x_resolution, y_resolution=y_resolution,
                                      max_effective_index=max_effective_index)
            if crossing is None:
                print(f"  No crossing found in {wavelengths_shg[0]}-{wavelengths_shg[-1]}nm.")
                results[key] = None
                continue

            recheck = solve_and_identify(anisotropic_equation, anchor_point, anchor_mode_idx,
                                          (h, w, crossing['wavelength_shg']), num_modes=num_modes, window=window,
                                          x_resolution=x_resolution, y_resolution=y_resolution,
                                          max_effective_index=max_effective_index, verbose=verbose)
            print(f"  [Check 2/2] Re-verified at crossing WL={crossing['wavelength_shg']:.3f}nm: mode index {recheck['mode_idx']}, overlap={recheck['overlap']:.4f}")
            if recheck['overlap'] < 0.8:
                print("  WARNING: low overlap at crossing WL.")
            if recheck['mode_idx'] != id_result['mode_idx']:
                print(f"  WARNING: mode index disagreement ({id_result['mode_idx']} vs {recheck['mode_idx']}).")

            print(f"  Crossing: {crossing['wavelength_shg']:.3f} nm, n_eff={crossing['n_eff']:.5f}")
            results[key] = {
                'mode_idx': id_result['mode_idx'], 'overlap': id_result['overlap'],
                'recheck_overlap': recheck['overlap'], 'recheck_mode_idx': recheck['mode_idx'],
                'crossing': crossing,
                'trusted': (id_result['overlap'] >= 0.8 and recheck['overlap'] >= 0.8
                            and id_result['mode_idx'] == recheck['mode_idx']),
            }
        except Exception as e:
            print(f"  FAILED: {repr(e)}")
            results[key] = None
    return results


def format_table(rows):
    """Plain-text table from a list of phase_matching_row() dicts (None entries skipped).
    No pandas dependency -- return the raw list yourself if you want a DataFrame instead.
    """
    rows = [r for r in rows if r is not None]
    if not rows:
        return "(no rows)"

    columns = [
        ('target_mode_name', '{}', 'Mode'),
        ('h_core', '{:.1f}', 'h'),
        ('w_core', '{:.1f}', 'w'),
        ('wavelength_shg', '{:.3f}', 'PM WL (nm)'),
        ('n_eff', '{:.5f}', 'n_eff'),
        ('dWL_dwidth', '{:.6f}', 'dWL/dw'),
        ('dWL_dheight', '{:.6f}', 'dWL/dh'),
    ]
    header = " | ".join(f"{label:<12}" for _, _, label in columns)
    lines = [header, "-" * len(header)]
    for r in rows:
        # a gradient column can be None if mode_gradient_width_height's overlap_threshold check
        # rejected the underlying perturbation as unreliable (see emode_helpers.py) -- show 'n/a'
        # rather than crashing on NoneType.__format__
        lines.append(" | ".join((f"{fmt.format(r[key]):<12}" if r[key] is not None else f"{'n/a':<12}")
                                 for key, fmt, _ in columns))
    return "\n".join(lines)


def save_mode_plot(anisotropic_equation, h_core, w_core, wavelength, mode_idx, num_modes,
                    file_name, component='Ey', file_type='png',
                    x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                    simulation_name='save_mode_plot', verbose=False):
    """Solve at (h_core, w_core, wavelength) and save a field plot of `mode_idx` to disk headlessly
    (em.plot()'s file_name param saves instead of opening the interactive GUI window) -- keeps a
    visual record of a mode that was successfully matched/analyzed during an automated sweep.
    """
    em = launch_session(simulation_name, verbose=verbose)
    try:
        setup_waveguide(em, anisotropic_equation, h_core, w_core)
        em.settings(wavelength=wavelength, num_modes=num_modes, x_resolution=x_resolution,
                    y_resolution=y_resolution, max_effective_index=max_effective_index)
        em.FDM()
        em.plot(mode=mode_idx, component=component, file_name=file_name, file_type=file_type)
    finally:
        em.close(save=False)


def visual_mode_survey(anisotropic_equation, h, w, wavelength, num_modes, modes_to_plot,
                        x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                        component='Ey', simulation_name='mode_survey', verbose=False):
    """Solve once at (h, w, wavelength) and plot each mode in modes_to_plot for visual review --
    the human-in-the-loop step for confirming mode identity before a long automated run (mode
    index is not a stable identifier across geometry -- see EMode_Troubleshooting_Log.md).

    Returns the FDM() result dict (n_eff_tilde, TE_fraction, TM_indices) alongside the plots.
    """
    em = launch_session(simulation_name, verbose=verbose)
    try:
        setup_waveguide(em, anisotropic_equation, h, w)
        fdm_result = solve_modes(em, 'survey', wavelength=wavelength, num_modes=num_modes,
                                  x_resolution=x_resolution, y_resolution=y_resolution,
                                  max_effective_index=max_effective_index)
        print(f"=== Survey at h={h}, w={w}, wavelength={wavelength} "
              f"(all plots below are this SAME geometry, only mode index varies) ===")
        for mode in modes_to_plot:
            print(f"-- mode {mode} --  n_eff={fdm_result['n_eff_tilde'][mode].real:.5f}")
            em.plot(mode=mode, component=component)
    finally:
        em.close(save=False)
    return fdm_result


def walk_mode_across_points(anisotropic_equation, start_point, start_mode_idx, target_points,
                             tracking_wavelength, num_modes, window=15,
                             x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                             overlap_threshold=0.8, review_threshold=None, max_jump_distance=None,
                             verbose=False, on_point=None, resume_solved=None):
    """Track a mode's raw index across a whole set of (h, w) target points, starting from a
    user-confirmed (start_point, start_mode_idx) -- the automated counterpart to visual_mode_survey.

    Walks nearest-neighbor (always tracking from the closest already-solved point, not always from
    the original start_point) rather than jumping to every target directly from one anchor, since
    mode index has been shown to swing widely over even modest geometry changes (TM40 shifted from
    index 23 to 26 for a single 50nm width step) -- small chained steps keep overlap tracking
    reliable without needing an enormous window/num_modes for every point. `window`/`num_modes` can
    still be generous ("moderately brute force") since each individual step is small.

    Three-tier outcome per step, based on `overlap_threshold` and `review_threshold`:
      - overlap >= overlap_threshold: accepted cleanly.
      - review_threshold <= overlap < overlap_threshold (only possible when review_threshold is
        given): FLAGGED -- still recorded with a real mode_idx and still usable as a source for
        tracking later points (so one shaky-but-plausible match doesn't force its neighbors onto a
        much longer, less reliable jump), but marked info['flagged_for_review']=True so it's easy to
        single out for visual review later (Step 5 processes flagged points normally, since they
        aren't None, so a field plot still gets saved for them).
      - overlap below that floor (below review_threshold if given, else below overlap_threshold):
        REJECTED -- same as an exception: solved as None, unusable as a source, retried on a later
        run.

    `max_jump_distance`, if given, caps how far (Euclidean, in nm) a source point may be from the
    target it's tracking to -- a source beyond this is never considered, even as a last resort.
    Without this cap, a point with no good nearby source still gets tracked from whatever solved
    point is globally closest, however far that is (even all the way back to start_point); long
    jumps have been observed to track less reliably than short ones, so on a point with no good
    option nearby, this can silently produce a low-confidence guess (or cascade into a worse guess
    at ITS neighbors too). With the cap, a point with nothing solved within range is simply left
    unattempted this run rather than guessed at -- once every remaining point is out of range of
    every solved point, the walk stops early rather than looping (a global-nearest search can't
    find anything closer later, so there's nothing more it can do this run); the leftover points
    are retried on a later run, when a nearer neighbor may have since succeeded.

    Resilient: a failed/low-confidence point doesn't stop the rest of the walk, and points reached
    only through a failed point are walked from their next-nearest solved neighbor instead.

    If given, `on_point(point, info, solved, problems, candidate)` is called right after each point
    is resolved (before moving to the next), so a caller can checkpoint progress to disk during a
    long walk instead of losing everything if it's interrupted partway through. `problems` is a
    list of (reason, detail) tuples -- empty if the point tracked cleanly, else one entry per issue
    ('exception'/'low_overlap'/'flagged'/'saturated') -- for a caller that wants to log
    failures/warnings persistently (see `log_failed_point`). `candidate` is the raw
    solve_and_identify() result ({'mode_idx', 'overlap', 'n_eff'}) if a solve actually happened this
    step, else None (an exception before any result came back) -- unlike `info`, this is populated
    even for a REJECTED point, so a caller can still save/inspect the field plot of whatever
    candidate mode was tried and rejected, not just the ones that passed.

    `resume_solved`, if given, pre-seeds already-known points (e.g. reloaded from a checkpoint after
    an interrupted run) so the walk can continue from where it left off instead of re-solving them.
    `target_points` should already exclude any point present in `resume_solved`.

    Returns {point: None or {'mode_idx', 'overlap', 'tracked_from', 'saturated', 'flagged_for_review'}}
    for every point in target_points that was attempted -- a point left unreachable by
    `max_jump_distance` is simply absent (ready to retry on a later run). start_point itself is not
    included, it's already known.
    """
    max_jump_sq = None if max_jump_distance is None else max_jump_distance ** 2
    remaining = [tuple(p) for p in target_points]
    solved = {tuple(start_point): {'mode_idx': start_mode_idx, 'overlap': 1.0,
                                    'tracked_from': None, 'saturated': False,
                                    'flagged_for_review': False}}
    if resume_solved:
        solved.update({tuple(p): info for p, info in resume_solved.items()})

    while remaining:
        best = None
        for p in remaining:
            for s, info in solved.items():
                if info is None:
                    continue
                d = (p[0] - s[0]) ** 2 + (p[1] - s[1]) ** 2
                if max_jump_sq is not None and d > max_jump_sq:
                    continue
                if best is None or d < best[0]:
                    best = (d, p, s)
        if best is None:
            print(f"\n  STOPPING: {len(remaining)} point(s) have no solved source within "
                  f"max_jump_distance={max_jump_distance} -- left for a later run: {remaining}")
            break
        _, next_point, from_point = best
        remaining.remove(next_point)
        from_info = solved[from_point]

        problems = []
        result = None
        try:
            result = solve_and_identify(
                anisotropic_equation, (from_point[0], from_point[1], tracking_wavelength),
                from_info['mode_idx'], (next_point[0], next_point[1], tracking_wavelength),
                num_modes=num_modes, window=window, x_resolution=x_resolution,
                y_resolution=y_resolution, max_effective_index=max_effective_index, verbose=verbose)
            saturated = result['mode_idx'] >= num_modes - 2
            floor = overlap_threshold if review_threshold is None else review_threshold
            if result['overlap'] < floor:
                print(f"  REJECTED: overlap {result['overlap']:.3f} below threshold "
                      f"{floor} tracking {next_point} from {from_point}")
                problems.append(('low_overlap', f"overlap={result['overlap']:.3f}, "
                                                 f"threshold={floor}"))
                info = None
            else:
                flagged = result['overlap'] < overlap_threshold
                info = {'mode_idx': result['mode_idx'], 'overlap': result['overlap'],
                        'tracked_from': from_point, 'saturated': saturated,
                        'flagged_for_review': flagged}
                if flagged:
                    print(f"  FLAGGED (needs review): overlap {result['overlap']:.3f} below "
                          f"{overlap_threshold} (>= review_threshold {review_threshold}) "
                          f"tracking {next_point} from {from_point}")
                    problems.append(('flagged', f"overlap={result['overlap']:.3f}, "
                                                 f"threshold={overlap_threshold}"))
                if saturated:
                    print(f"  WARNING: mode_idx={result['mode_idx']} near num_modes={num_modes} "
                          f"ceiling at {next_point} -- may be truncated, consider raising num_modes")
                    problems.append(('saturated', f"mode_idx={result['mode_idx']}, num_modes={num_modes}"))
        except Exception as e:
            print(f"  FAILED tracking {next_point} from {from_point}: {repr(e)}")
            info = None
            problems.append(('exception', repr(e)))

        solved[next_point] = info
        print(f"{from_point} -> {next_point}: {info}")
        if on_point is not None:
            on_point(next_point, info, solved, problems, result)

    del solved[tuple(start_point)]
    return solved


def fund_target_overlap(anisotropic_equation, h_core, w_core, wavelength_shg,
                         target_mode_idx, fund_mode_idx=0, num_modes_fund=6, num_modes_target=35,
                         x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                         simulation_name='fund_target_overlap', verbose=False):
    """Spatial overlap between the fundamental (at 2x the SHG wavelength) and the target mode (at
    the SHG wavelength) at a phase-matching point -- a physically meaningful modal-overlap figure
    for SHG conversion efficiency, distinct from the mode-TRACKING overlap used elsewhere in this
    module (that compares the same mode across two different geometries; this compares two
    different modes at the SAME geometry/phase-matching condition).

    Assumes target_mode_idx is already correct at (h_core, w_core, wavelength_shg) -- e.g. from a
    phase_matching_row() result -- not re-verified here.

    Returns {'overlap', 'n_eff_fund', 'n_eff_target'}.
    """
    em = launch_session(simulation_name, verbose=verbose)
    try:
        setup_waveguide(em, anisotropic_equation, h_core, w_core)
        fund_fdm = solve_modes(em, 'fund', wavelength=2 * wavelength_shg, num_modes=num_modes_fund,
                                x_resolution=x_resolution, y_resolution=y_resolution,
                                max_effective_index=max_effective_index)
        target_fdm = solve_modes(em, 'target', wavelength=wavelength_shg, num_modes=num_modes_target,
                                  x_resolution=x_resolution, y_resolution=y_resolution,
                                  max_effective_index=max_effective_index)
        overlap = abs(em.overlap(label_a='fund', mode_a=fund_mode_idx,
                                  label_b='target', mode_b=target_mode_idx))
        n_eff_fund = fund_fdm['n_eff_tilde'][fund_mode_idx].real
        n_eff_target = target_fdm['n_eff_tilde'][target_mode_idx].real
    finally:
        em.close(save=False)

    return {'overlap': overlap, 'n_eff_fund': n_eff_fund, 'n_eff_target': n_eff_target}


def scan_for_crossings(anisotropic_equation, h, w, wavelengths_shg, fund_mode_idx=0,
                        num_modes_fund=2, num_modes_scan=40, exclude_indices=(),
                        x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                        simulation_name='scan_for_crossings', verbose=False):
    """Look for a phase-matching crossing with the fundamental across EVERY raw mode index
    0..num_modes_scan-1 (except exclude_indices) at a single (h, w) point -- a cheap way to
    discover candidate 'other modes' (e.g. TM02, TM20, ...) without knowing their names ahead of
    time. Does this in exactly 2 EMode sweep calls total (not num_modes_scan separate find_crossing
    calls) by reusing the same fund/target wavelength sweeps across all mode-index columns.

    Returns {mode_idx: {'wavelength_shg', 'n_eff'}} for every index that shows a crossing in
    wavelengths_shg. Candidates found here still need visual confirmation (via visual_mode_survey)
    before being trusted as a specific named mode -- this only tells you *something* crosses there.
    """
    wavelengths_shg = np.asarray(wavelengths_shg)
    em = launch_session(simulation_name, verbose=verbose)
    try:
        setup_waveguide(em, anisotropic_equation, h, w)
        em.settings(x_resolution=x_resolution, y_resolution=y_resolution, num_modes=num_modes_fund)
        data_fund = em.sweep(key='wavelength', values=2 * wavelengths_shg, result=['effective_index'])
        n_fund = np.array(data_fund['effective_index'])[:, fund_mode_idx]

        em.settings(num_modes=num_modes_scan, max_effective_index=max_effective_index)
        data_target = em.sweep(key='wavelength', values=wavelengths_shg, result=['effective_index'])
        n_target_all = np.array(data_target['effective_index'])
    finally:
        em.close(save=False)

    found = {}
    for mode_idx in range(num_modes_scan):
        if mode_idx in exclude_indices:
            continue
        n_target = n_target_all[:, mode_idx]
        delta_n = n_fund - n_target
        if np.sign(delta_n[0]) == np.sign(delta_n[-1]):
            continue
        wl_cross = np.interp(0, delta_n, wavelengths_shg)
        found[mode_idx] = {
            'wavelength_shg': wl_cross,
            'n_eff': np.interp(wl_cross, wavelengths_shg, n_target),
        }
    return found
