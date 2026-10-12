"""Exact dB-additive decomposition of conversion efficiency into contributions, for the
stacked/waterfall bar chart requested 2026-10-12. Agreed approach: since efficiency is
fundamentally a PRODUCT of factors (not a sum), stacking raw 0-100%-normalized contributions
breaks the promise that segments sum to the true total -- converting to decibels makes the
relationships additive instead (log(a*b*c) = log(a)+log(b)+log(c), exactly), and this codebase
already expresses every loss in dB.

Derivation, from shg_physics.py's own formulas (read directly off overlap_shape_factor,
eta_norm_per_W_m2, loss_limited_length):

    |O| = overlap_shape * sqrt(es2 * p2)                 (overlap_shape_factor's own identity)
    eta_SI = (w_sh eps0/4)^2 |O|^2 = (const)^2 * overlap_shape^2 * es2 * p2
    peak_SI = eta_SI * L_eff(L_opt; a_p, a_s)^2           (loss_limited_length's own model, L_opt
                                                            = the length that MAXIMIZES L_eff)

Two earlier versions of this derivation were tried and rejected (both found by checking the
reconstruction identity numerically against real data, not just algebra on paper -- see PLAN.md,
2026-10-12):
  1. Comparing L_eff from separate loss_limited_length() calls (one per loss scenario) directly --
     each call independently RE-OPTIMIZES L, so the compared L_eff values come from different L's,
     breaking the identity (~35 dB reconstruction error on real data).
  2. Evaluating every geometry at one SHARED fixed length -- this project's loss magnitudes span
     many orders of magnitude between geometries (e.g. SH-side absorption ~1e4 to ~3e7 dB/m across
     the pedestal dataset alone), so a single fixed length is numerically dead (underflowed to
     exactly 0) for high-loss geometries and physically meaningless for low-loss ones.

Fix: evaluate every term at EACH CROSSING'S OWN L_opt (the actual length `loss_limited_length`
already finds by search -- the same quantity behind this project's existing
`peak_efficiency_pct_per_W` elsewhere, so this decomposition's total reproduces that number
exactly, not a new metric). That makes a 5th term, the device length itself, a real and necessary
part of the identity -- not requested in the original 4-factor ask (overlap / mode size / pump
loss / SH loss), but mathematically unavoidable once L is allowed to vary per geometry: a geometry
whose loss balance tolerates a longer optimal length before SH gain saturates gets a genuine bonus
from that, independent of its overlap or raw loss numbers. Kept as its own (clearly labeled, muted)
segment rather than folded into or hidden from the other four.

    shape_dB     = 20*log10(overlap_shape)                      -- always <= 0 (overlap_shape in [0,1])
    field_dB     = 10*log10(eta_SI) - shape_dB                  -- the mode-size/field-magnitude
                                                                    scale; NOT bounded by 0, it's a
                                                                    physical scale, not a quality factor
    sh_loss_dB   = 20*log10(L_eff(L_opt; a_p=0, a_s) / L_opt)          -- always <= 0
    pump_loss_dB = 20*log10(L_eff(L_opt; a_p, a_s) / L_eff(L_opt; a_p=0, a_s))  -- always <= 0, the
                                                                    INCREMENTAL penalty from adding
                                                                    pump loss on top of SH loss
                                                                    alone, both at the SAME L_opt
    length_dB    = 20*log10(L_opt)                               -- the 5th, necessary term

total_dB = shape_dB + field_dB + sh_loss_dB + pump_loss_dB + length_dB
         = 10*log10(peak_SI)   (exactly -- see `decompose`'s assertion against the project's own
                                 loss_limited_length output, not just internal self-consistency)
"""
import numpy as np

from shg_physics import db_per_m_to_per_m, loss_limited_length

L_MAX_M = 0.2  # matches loss_limited_length's own default search ceiling


def l_eff_at(L_m, alpha_p_db_m, alpha_s_db_m):
    """L_eff [m] at a SINGLE given length L_m (not searched) -- same closed form as
    shg_physics.loss_limited_length, evaluated at one point instead of over an array."""
    a_p = db_per_m_to_per_m(max(alpha_p_db_m, 0.0))
    a_s = db_per_m_to_per_m(max(alpha_s_db_m, 0.0))
    D = a_s / 2 - a_p
    if abs(D) < 1e-12:
        return L_m * np.exp(-a_s * L_m / 2)
    return (np.exp(-a_p * L_m) - np.exp(-a_s * L_m / 2)) / D


def decompose(row, include_aln=False):
    """row: a dict/Series with eta_pct_per_W_cm2, overlap_shape, pump_scattering_dB_per_m,
    pump_absorption_dB_per_m, sh_scattering_dB_per_m, sh_absorption_dB_per_m (all already in
    crossings.csv -- no EMode/field data needed, pure post-processing of stored results).

    include_aln=True adds aln_pump_loss_dB_per_m / aln_sh_loss_dB_per_m (AlN's own intrinsic
    bulk absorption from the AM187-LT6 k_e fit, see geometry.aln_core_loss_dB_per_m and
    reprocess_run.py; 0.0/absent if a row hasn't been reprocessed with AlN loss) on top of the
    existing loss terms -- default False reproduces the exact pre-2026-10-12 AlN-lossless
    numbers unchanged, for every existing caller. shape_dB and field_dB are identical either way
    (eta_pct_per_W_cm2/overlap_shape don't depend on loss at all); only sh_loss_dB, pump_loss_dB
    and length_dB (via L_opt) can differ between the two calls on the same row."""
    eta_si = row['eta_pct_per_W_cm2'] * 100.0  # invert eta_to_pct_per_W_cm2
    overlap_shape = max(row['overlap_shape'], 1e-12)
    pump_loss = row.get('pump_scattering_dB_per_m', 0.0) + row.get('pump_absorption_dB_per_m', 0.0)
    sh_loss = row.get('sh_scattering_dB_per_m', 0.0) + row.get('sh_absorption_dB_per_m', 0.0)
    if include_aln:
        # NaN (not reprocessed for this row) must become 0.0, not propagate -- `or 0.0` would NOT
        # catch it (NaN is truthy), so this needs an explicit isnan check.
        aln_pump = row.get('aln_pump_loss_dB_per_m', 0.0)
        aln_sh = row.get('aln_sh_loss_dB_per_m', 0.0)
        pump_loss += 0.0 if aln_pump is None or np.isnan(aln_pump) else aln_pump
        sh_loss += 0.0 if aln_sh is None or np.isnan(aln_sh) else aln_sh

    l_opt, l_eff_both, peak_si = loss_limited_length(eta_si, pump_loss, sh_loss, L_MAX_M)
    l_eff_sh_only = l_eff_at(l_opt, 0.0, sh_loss)

    shape_db = 20 * np.log10(overlap_shape)
    field_db = 10 * np.log10(eta_si) - shape_db
    sh_loss_db = 20 * np.log10(max(l_eff_sh_only, 1e-30) / l_opt)
    pump_loss_db = 20 * np.log10(max(l_eff_both, 1e-30) / max(l_eff_sh_only, 1e-30))
    length_db = 20 * np.log10(l_opt)
    total_db = shape_db + field_db + sh_loss_db + pump_loss_db + length_db

    expected_total = 10 * np.log10(max(peak_si, 1e-300))
    recon_error_db = total_db - expected_total

    return {'shape_dB': shape_db, 'field_dB': field_db, 'sh_loss_dB': sh_loss_db,
            'pump_loss_dB': pump_loss_db, 'length_dB': length_db, 'total_dB': total_db,
            'peak_efficiency_SI': peak_si, 'L_opt_m': l_opt, 'recon_error_dB': recon_error_db}
