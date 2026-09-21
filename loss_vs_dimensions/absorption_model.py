"""Post-processed, non-uniform absorption loss from an already-solved (lossless) mode.

This module has no EMode dependency at all -- it consumes plain numpy arrays (grid
coordinates, a core-region mask, and the mode's z-Poynting flux) that get exported once
from an EMode session, and computes modal absorption loss for arbitrary spatially-varying
absorption assumptions entirely in Python. The point is to let you try many different
absorption profiles/parameters without re-running EMode each time.

Physics: first-order perturbation theory for a weak, spatially-varying power absorption
coefficient alpha(x, y) [dB/m] gives the modal loss as the Poynting-flux-weighted spatial
average of alpha(x, y) (the continuous generalization of the usual confinement-factor x
material-loss product, which is just this same average when alpha is piecewise-uniform per
shape):

    loss_dB_per_m = integral( alpha(x, y) * Sz(x, y) ) dA  /  integral( Sz(x, y) ) dA

`alpha0` can be passed directly in dB/m -- the weighted average is linear, so it commutes
with the dB/m <-> 1/m conversion factor and no unit juggling is needed here.
"""

import numpy as np


def profile_step(distance, alpha0, L):
    """alpha0 for distance <= L (within the assumed damage/interface layer), else 0.
    `distance` and `L` in nm; NaN distance (outside the region this profile applies to) -> 0.
    """
    distance = np.asarray(distance, dtype=float)
    return np.where(np.isnan(distance), 0.0, np.where(distance <= L, alpha0, 0.0))


def profile_exp(distance, alpha0, L):
    """alpha0 * exp(-distance / L) -- exponential decay from the interface/sidewall into the
    core, characteristic length L [nm]. NaN distance -> 0.
    """
    distance = np.asarray(distance, dtype=float)
    return np.where(np.isnan(distance), 0.0, alpha0 * np.exp(-distance / L))


PROFILE_SHAPES = {'step': profile_step, 'exp': profile_exp}


def distance_from_sidewall(core_mask):
    """Distance [in grid-index units -- multiply by dx for nm] from each core pixel to the
    nearest non-core pixel IN THE SAME ROW (i.e. purely lateral, "normal to the sidewall" for
    a roughly vertical sidewall) -- not a 2D Euclidean distance transform, which would also
    pull in the (irrelevant, per the assumed physics) vertical direction near top/bottom
    corners of the core.

    Assumes each row of `core_mask` (2D bool array, shape (ny, nx)) has at most one contiguous
    run of True values (a single ridge cross-section) -- true for the simple trapezoidal core
    shapes used in this pipeline. Returns a float array, NaN outside the core.
    """
    ny, nx = core_mask.shape
    dist = np.full((ny, nx), np.nan)
    cols = np.arange(nx)
    for row in range(ny):
        in_core = core_mask[row]
        if not in_core.any():
            continue
        core_cols = cols[in_core]
        left, right = core_cols.min(), core_cols.max()
        row_dist = np.minimum(cols - left, right - cols).astype(float)
        dist[row, in_core] = row_dist[in_core]
    return dist


def distance_from_bottom_interface(y, core_mask):
    """Distance [same units as `y`, typically nm] from the bottom of the core (the
    core/substrate interface) upward, for every core pixel -- varies only with height, per the
    assumed physics of interface-driven absorption. `y` is a 1D array of row coordinates
    (length ny, matching core_mask's first axis). NaN outside the core.
    """
    ny, nx = core_mask.shape
    y = np.asarray(y, dtype=float)
    rows_with_core = np.where(core_mask.any(axis=1))[0]
    if len(rows_with_core) == 0:
        return np.full((ny, nx), np.nan)
    y_bottom = y[rows_with_core.min()]
    dist = np.full((ny, nx), np.nan)
    row_dist = y - y_bottom
    dist[core_mask] = np.broadcast_to(row_dist[:, None], (ny, nx))[core_mask]
    return dist


def mechanism_alpha_map(core_mask, dx, y, mechanism):
    """alpha(x, y) map [dB/m] for ONE named physical mechanism (zero outside the core, and
    zero everywhere for a localization this mechanism doesn't apply to).

    `mechanism` is a dict: {'name': str, 'localization': 'sidewall'|'interface',
    'shape': 'step'|'exp', 'alpha0': float [dB/m], 'L': float [nm]}. 'sidewall' varies with
    lateral distance from the nearest sidewall (distance_from_sidewall); 'interface' varies
    with height above the core/substrate interface (distance_from_bottom_interface). `dx` [nm]
    is the grid's x-resolution (for converting sidewall pixel-distance to nm); `y` [nm] is the
    grid's 1D y-coordinate array, needed for the interface distance.
    """
    localization = mechanism['localization']
    if localization == 'sidewall':
        dist_nm = distance_from_sidewall(core_mask) * dx
    elif localization == 'interface':
        dist_nm = distance_from_bottom_interface(y, core_mask)
    else:
        raise ValueError(f"unknown localization {localization!r} for mechanism "
                          f"{mechanism.get('name')!r} -- must be 'sidewall' or 'interface'")
    fn = PROFILE_SHAPES[mechanism['shape']]
    return fn(dist_nm, mechanism['alpha0'], mechanism['L'])


def modal_absorption_loss(alpha_map, Sz):
    """Poynting-flux-weighted spatial average of alpha_map -> modal loss [same units as
    alpha_map, e.g. dB/m]. `Sz` is the mode's z-Poynting flux over the same grid (any
    consistent power-density units -- only relative weighting matters, so it need not be
    normalized). Negative/near-zero-noise Sz values (e.g. in evanescent tails, PML) are
    clipped to zero so they don't contribute negative weight.
    """
    Sz = np.clip(np.real(Sz), 0, None)
    total_power = Sz.sum()
    if total_power <= 0:
        raise ValueError("Sz has no positive power -- check field export/orientation")
    return float((alpha_map * Sz).sum() / total_power)


def compute_mechanism_losses(core_mask, dx, y, Sz, mechanisms):
    """Modal absorption loss [dB/m] for EACH mechanism independently -- one EMode-free
    calculation per mechanism, from the same exported (core_mask, Sz) data.

    `mechanisms` is a list of dicts, each as described in mechanism_alpha_map. Returns
    {mechanism['name']: loss_dB_per_m}, in the same order as `mechanisms` (Python dicts
    preserve insertion order) -- sum the values yourself for the total absorption contribution;
    each mechanism's own loss can also be plotted/inspected separately.
    """
    return {m['name']: modal_absorption_loss(mechanism_alpha_map(core_mask, dx, y, m), Sz)
            for m in mechanisms}
