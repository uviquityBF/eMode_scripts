"""Reusable EMode session/geometry/mode-tracking helpers, factored out of AlN_2D_4_sweep.ipynb.

See EMode_Troubleshooting_Log.md and EMode_Function_Reference.md for the backend quirks these
helpers work around.
"""

import numpy as np
import emodeconnection as emc


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
                        simulation_name='solve_and_identify', verbose=False):
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
        setup_waveguide(em, anisotropic_equation, h_a, w_a)
        solve_modes(em, 'anchor', wavelength=wl_a, num_modes=num_modes,
                    x_resolution=x_resolution, y_resolution=y_resolution,
                    max_effective_index=max_effective_index)

        set_core_width(em, h_t, w_t)
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
                                d_width=5.0, d_height=5.0, window=5,
                                x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                                simulation_name='mode_gradient', verbose=False):
    """Central-difference dn/dwidth and dn/dheight for one mode at base_point =
    (h_core, w_core, wavelength), each step tracked via overlap against base_point/base_mode_idx
    directly (not a walking chain), so tracking error can't accumulate across the 4 evaluations.

    Also returns the raw solve_and_identify() result for each of the 4 perturbation points
    ('w_plus', 'w_minus', 'h_plus', 'h_minus') -- check their 'overlap' values before trusting the
    gradient. A low overlap on any one of them means that step likely tracked a different physical
    mode, not a true continuation of base_mode_idx, and the gradient built from it is unreliable.
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

    dn_dw = (w_plus['n_eff'] - w_minus['n_eff']) / (2 * d_width)
    dn_dh = (h_plus['n_eff'] - h_minus['n_eff']) / (2 * d_height)

    return {
        'dn_dwidth': dn_dw, 'dn_dheight': dn_dh,
        'w_plus': w_plus, 'w_minus': w_minus, 'h_plus': h_plus, 'h_minus': h_minus,
    }


def implicit_wavelength_gradient(fund_grad, target_grad, crossing):
    """d(phase-matching wavelength)/d(width) and .../d(height), via the implicit function theorem
    on F(WL,w,h) = n_fund(WL,w,h) - n_target(WL,w,h) = 0.
    """
    F_WL = crossing['dn_dWL_fund'] - crossing['dn_dWL_target']
    F_w = fund_grad['dn_dwidth'] - target_grad['dn_dwidth']
    F_h = fund_grad['dn_dheight'] - target_grad['dn_dheight']
    return {'dWL_dwidth': -F_w / F_WL, 'dWL_dheight': -F_h / F_WL}


def phase_matching_row(anisotropic_equation, h_core, w_core, wavelengths_shg, target_mode_idx,
                        target_mode_name='target', fund_mode_idx=0,
                        num_modes_fund=6, num_modes_target=35,
                        d_width=5.0, d_height=5.0, window=5,
                        x_resolution=10.0, y_resolution=10.0, max_effective_index=2.6,
                        verbose=False):
    """One full phase-matching table row: crossing point, per-mode dn/dWL, per-mode dn/dwidth and
    dn/dheight, and the derived d(PM wavelength)/d(width)/d(height) -- combines find_crossing,
    mode_gradient_width_height (both modes), and implicit_wavelength_gradient.

    Assumes target_mode_idx is already correct AT THIS (h_core, w_core) -- confirm via em.plot()
    or solve_and_identify first; mode index is not guaranteed stable across geometry changes (see
    EMode_Troubleshooting_Log.md).

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
                                            window=window, x_resolution=x_resolution, y_resolution=y_resolution,
                                            max_effective_index=max_effective_index, verbose=verbose)

    target_base_point = (h_core, w_core, crossing['wavelength_shg'])
    target_grad = mode_gradient_width_height(anisotropic_equation, target_base_point, target_mode_idx,
                                              num_modes=num_modes_target, d_width=d_width, d_height=d_height,
                                              window=window, x_resolution=x_resolution, y_resolution=y_resolution,
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
        lines.append(" | ".join(f"{fmt.format(r[key]):<12}" for key, fmt, _ in columns))
    return "\n".join(lines)
