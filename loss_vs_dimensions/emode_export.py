"""EMode-facing extraction helpers for the loss-vs-dimensions sweep.

Shapes and units below were confirmed against a live `inspect_emode_outputs.py` run
(2026-09-21, AlN core h=340/w=400, num_modes=2, x_resolution=y_resolution=10nm):
  - `get_fields(key=[...])` returns `{wavelength_str: Field}` -- note the dict key is a STRING
    ('450.0'), not a float.
  - `Field.field` has shape `(len(key), num_modes, len(grid.x), len(grid.y))` -- e.g. (6, 2,
    200, 234) for 6 requested keys/2 modes/200 x-points/234 y-points. So the field-name axis is
    first, and the two spatial axes are (nx, ny), NOT (ny, nx).
  - `get_shape(key='core')['metadata']['scattering_sum']` (and the direct `scattering()` return)
    is a length-`num_modes` list, indexable by mode_idx, ALREADY in dB/m -- confirmed by
    matching it exactly against report()'s printed "core scattering (dB/m)" column (1247.24 for
    mode 0 in both places). Note report() also has a separate "Loss (dB/m)" column, which is
    the FDM material-loss term (zero here, since nothing sets shape(loss_dB_per_m=...) in this
    pipeline -- the mode is solved lossless on purpose) -- scattering is additive on top of it,
    matching this pipeline's split between native scattering and post-processed absorption.

Still UNVERIFIED: build_core_mask_from_geometry's trapezoid convention (which edge `mask` sets,
which way `sidewall_angle` tilts) -- cross-check against em.plot(component='Shapes') or
em.plot(component='Index') for one point before trusting it broadly.
"""

import numpy as np


def extract_scattering_loss_dB_per_m(em, shape_name='core', mode_idx=0):
    """Native EMode sidewall-scattering loss for one mode.

    em.scattering(shape=shape_name) must already have been called this solve.
    scattering_sum's *structure* (length-num_modes, indexed by mode_idx) is confirmed; its
    UNITS are not (see module docstring) -- treat the dB/m label here as provisional until
    checked against report()'s printed loss dB/m column.
    """
    shape = em.get_shape(key=shape_name)
    metadata = shape['metadata'] if isinstance(shape, dict) else shape.metadata
    scattering_sum = np.asarray(metadata['scattering_sum'])
    return float(scattering_sum[mode_idx])


def _get_field_entry(fields_dict, wavelength):
    if wavelength is not None:
        for key in (wavelength, str(wavelength)):
            if key in fields_dict:
                return fields_dict[key]
        raise KeyError(f"wavelength {wavelength!r} not in get_fields() result keys "
                        f"{list(fields_dict.keys())}")
    return next(iter(fields_dict.values()))


def extract_mode_fields_for_export(em, mode_idx=0, wavelength=None,
                                    keys=('Ex', 'Ey', 'Ez', 'Sx', 'Sy', 'Sz')):
    """Grid coordinates + named field components for one solved mode, for absorption_model.py's
    and scattering_model.py's post-processing (no further EMode calls needed once exported).

    Confirmed against a live run: em.get_fields(key=[...]) returns {wavelength_str: Field},
    Field.field has shape (len(key), num_modes, len(grid.x), len(grid.y)) -- field-name axis
    first, then mode, then (nx, ny). Index by name (not position) to stay correct regardless of
    key order.

    Requests all 6 components by default (the same combo inspect_emode_outputs.py's diagnostic
    confirmed working) rather than a single key like ['Sz'] alone -- that errors with
    ArgumentError('Invalid field name'), so a Poynting/E component apparently can't be requested
    in isolation.

    Returns (x, y, {name: array}) -- x, y in nm, each array transposed to shape (ny, nx) to
    match the (ny, nx) convention used by absorption_model.py / emode_export.build_core_mask_from_geometry
    (both built on np.meshgrid(x, y), which puts y first).
    """
    fields = em.get_fields(key=list(keys))
    field_obj = _get_field_entry(fields, wavelength)

    raw = np.asarray(field_obj.field)  # (len(field_names), num_modes, nx, ny)
    if raw.ndim != 4:
        raise ValueError(f"unexpected field ndim={raw.ndim}, shape={raw.shape} -- "
                          "update extract_mode_fields_for_export to match")

    x = np.asarray(field_obj.grid.x)
    y = np.asarray(field_obj.grid.y)
    expected_shape = (len(y), len(x))

    result = {}
    for name in keys:
        idx = field_obj.field_names.index(name)
        arr = raw[idx, mode_idx].T  # (nx, ny) -> (ny, nx)
        if arr.shape != expected_shape:
            raise ValueError(f"{name} shape {arr.shape} doesn't match (len(y), len(x))="
                              f"{expected_shape} -- grid/field axis order assumption is wrong")
        result[name] = arr
    return x, y, result


def build_core_mask_from_geometry(x, y, h_core, w_core, sidewall_angle, y_bottom):
    """Analytic core-region mask for a trapezoidal ridge (mask width `w_core` at the BOTTOM of
    the core, narrowing by `sidewall_angle` going up -- matches emode_helpers.set_core_width's
    shape() call: height=h_core, mask=w_core, etch_depth=h_core, sidewall_angle=sidewall_angle).

    UNVERIFIED ASSUMPTION: this reimplements EMode's own shape rasterization rather than
    reading it back from EMode, because the backend's exact mask/etch_depth/sidewall_angle
    convention isn't documented (see EMode_Function_Reference.md) and there's no client-side
    geometry code to confirm it against (checked emodeconnection/geometry.py -- unrelated, EME
    section curves only). Cross-check this mask against em.plot(component='Index') or
    em.plot(component='Shapes') for one point before trusting it broadly; if it's flipped
    (mask at top instead of bottom, or widening instead of narrowing with sidewall_angle), swap
    the sign on the `frac` term below.

    `y_bottom` [nm] is the y-coordinate of the core/substrate interface (bottom of the core) in
    this grid's coordinate system -- also used by absorption_model.distance_from_bottom_interface
    indirectly, since that function derives it from the mask's own lowest row instead.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xx, yy = np.meshgrid(x, y)
    height_above_bottom = yy - y_bottom
    in_height = (height_above_bottom >= 0) & (height_above_bottom <= h_core)
    frac = np.clip(height_above_bottom / h_core, 0.0, 1.0)
    half_width = (w_core / 2) - frac * h_core * np.tan(np.radians(sidewall_angle))
    return in_height & (np.abs(xx) <= half_width)
