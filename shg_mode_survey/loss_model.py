"""Shared loss model: the one place the survey's post-processed propagation-loss formulas live, so the
SHG survey and any stand-alone loss-vs-geometry/wavelength tool use the same code. EMode-free: it only needs
numbers/arrays that were already exported from a solved mode (core mask, Sz, EMode-native sidewall scattering).

Loss terms [dB/m], each independently switchable:
  1. sidewall/roughness scattering  -- EMode-native value passed in (survey.native_scattering); optional scale.
  2. interface/sidewall absorption  -- absorption_model mechanisms (growth-interface dislocations, C/Si/O ...),
                                       optional per-mechanism wavelength exponent.
  3. volume (Rayleigh-like) scattering in the core film -- NEW, OFF by default:
         alpha_vol = C * Gamma_core * (lam_ref / lam)^p        [C in dB/cm at lam_ref, Gamma_core = core power fraction]
     weighted by the field in the core (unlike sidewall scattering, which is weighted by the field at the wall),
     roughly width-independent. p ~ 4 only for scatterers much smaller than the wavelength.

DEFAULTS REPRODUCE THE CURRENT SURVEY MODEL EXACTLY: with an empty/None model config, evaluate() returns native
scattering + sum(compute_mechanism_losses(...)) -- the same two numbers survey.py has always added.

Config (all keys optional), e.g. survey_config.SETTINGS['loss_model'] = {
    'scattering_scale': 1.0,                                   # multiplies the native sidewall scattering
    'volume_scattering': {'enabled': True, 'C_dB_per_cm': 5.0, 'p': 4.0, 'lam_ref_nm': 450.0, 'bands': ('pump',)},
    'absorption_lambda': {'p': 2.0, 'lam_ref_nm': 450.0},      # alpha0 *= (lam_ref/lam)^p on EVERY mechanism, or give
                                                               # a mechanism its own 'lambda_exponent'/'lambda_ref_nm'
    'absorption_scale': 1.0,                                   # multiplies every mechanism's alpha0
    'scale_bands': ('pump',),                                  # bands the two scale factors act on (default both)
}
Named presets (CASES, from the 2026-11 GL04/GL03 cutback review; see case()) bundle these for the pump band.
'bands' says which of 'pump' (lam >= 300 nm) / 'sh' (lam < 300 nm) the volume term applies to; default ('pump','sh').
The 'loss_model' key is excluded from geometry fingerprints in survey.py, like the absorption mechanisms (cheap to
reprocess from exported fields, so changing it never forces EMode re-solves).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'loss_vs_dimensions'))
import absorption_model as am  # noqa: E402

SH_BAND_MAX_NM = 300.0   # same pump/SH split as survey.calibrated_sh_loss


def band_of(lam_nm):
    return 'sh' if lam_nm < SH_BAND_MAX_NM else 'pump'


def core_power_fraction(core_mask, Sz):
    """Gamma_core: fraction of the mode's (clipped, positive) z-power inside the core mask."""
    sz = np.clip(np.real(Sz), 0, None)
    tot = sz.sum()
    return float((sz * core_mask).sum() / tot) if tot > 0 else float('nan')


def _band_scale(model, key, lam_nm):
    """model[key] (default 1.0) if lam's band is in model['scale_bands'] (default both bands), else 1.0."""
    m = model or {}
    return m.get(key, 1.0) if band_of(lam_nm) in m.get('scale_bands', ('pump', 'sh')) else 1.0


def scaled_mechanisms(mechanisms, lam_nm, model=None):
    """Copy of the mechanism list with alpha0 rescaled by (lam_ref/lam)^p. A mechanism's own
    'lambda_exponent' / 'lambda_ref_nm' wins over the model-wide 'absorption_lambda'; none set -> unchanged
    (the current flat-in-wavelength behaviour)."""
    glob = (model or {}).get('absorption_lambda') or {}
    a_scale = _band_scale(model, 'absorption_scale', lam_nm)
    out = []
    for m in mechanisms:
        p = m.get('lambda_exponent', glob.get('p', 0.0))
        ref = m.get('lambda_ref_nm', glob.get('lam_ref_nm', 450.0))
        m2 = dict(m)
        if p:
            m2['alpha0'] = m['alpha0'] * (ref / lam_nm) ** p
        m2['alpha0'] *= a_scale
        out.append(m2)
    return out


def volume_scattering_dB_per_m(gamma_core, lam_nm, model=None):
    """Rayleigh-like film scattering [dB/m]; 0.0 unless model['volume_scattering']['enabled'] and lam's band is selected."""
    v = (model or {}).get('volume_scattering') or {}
    if not v.get('enabled', False) or band_of(lam_nm) not in v.get('bands', ('pump', 'sh')):
        return 0.0
    return float(v['C_dB_per_cm'] * 100.0 * gamma_core * (v.get('lam_ref_nm', 450.0) / lam_nm) ** v.get('p', 4.0))


def evaluate(core_mask, dx, y, Sz, native_scattering_dB_per_m, mechanisms, lam_nm, model=None):
    """All loss terms for one already-solved mode [dB/m]. Returns a dict:
    scattering_sidewall, absorption_interface (sum), absorption_by_mechanism, volume_scattering, total,
    gamma_core. `native_scattering_dB_per_m` may be NaN (then NaN propagates into the total, as in the survey)."""
    scale = _band_scale(model, 'scattering_scale', lam_nm)
    per = am.compute_mechanism_losses(core_mask, dx, y, Sz, scaled_mechanisms(mechanisms, lam_nm, model))
    gamma = core_power_fraction(core_mask, Sz)
    scat = native_scattering_dB_per_m * scale
    ab = float(sum(per.values()))
    vol = volume_scattering_dB_per_m(gamma, lam_nm, model)
    return {'scattering_sidewall': scat, 'absorption_interface': ab, 'absorption_by_mechanism': per,
            'volume_scattering': vol, 'total': scat + ab + vol, 'gamma_core': gamma}


# Named presets for the PUMP band (scale_bands = ('pump',): SH scattering/absorption are left as the survey has them).
# GL04 = c-plane AlN on sapphire, 350 nm core, PECVD SiO2 clad, TM, as-grown (not annealed). Refit (2026-11-17) of the survey's
# own scattering + interface-absorption terms to GL04: 450 nm straight totals vs width (coupling assumed 14.5 +- 1 dB) and the
# 350 nm cutback slopes 26.0 / 17.3 / 7.8 dB/cm at 450 / 532 / 635 nm. Profile ranges (delta chi2 < 1): scattering_scale 0-0.18,
# absorption_scale 2.1-2.4, p 3-5. Only GL03 was annealed; GL04 is as-grown. The 'target_anneal_*' presets are PROJECTIONS for the target
# process (GL04 + anneal, never measured): the as-grown GL04 floor x0.8 / x0.5, SENSITIVITY cases, NOT a fit. The x0.5 rests on GL03
# post-anneal straights (floor ~13.4 dB/cm, assumed 13 dB coupling) vs GL04 as-grown (~25) -- that mixes lot and anneal effects; the
# GL03 group-5 data (4 devices, 0.2 cm baseline; pre->post change is length-independent) cannot show the anneal effect on propagation.
def _preset(s, a, p=3.75):
    return {'scattering_scale': s, 'absorption_scale': a, 'absorption_lambda': {'p': p, 'lam_ref_nm': 450.0}, 'scale_bands': ('pump',)}


CASES = {
    'current': {},                                              # exactly the pre-2026-11 survey model
    'gl04_asgrown': _preset(0.1, 2.3),
    'gl04_asgrown_scat_hi': _preset(0.3, 2.0),
    'target_anneal_weak': _preset(0.1, 2.3 * 0.8),
    'target_anneal_central': _preset(0.1, 2.3 * 0.5),
}


def case(name):
    """Loss-model config dict for a named preset (a copy, safe to edit)."""
    import copy
    return copy.deepcopy(CASES[name])


def _selftest():
    """EMode-free check on a synthetic mode: defaults must equal the old two-term sum; each switch must act."""
    ny, nx, dx = 60, 60, 10.0
    y = np.arange(ny) * dx
    mask = np.zeros((ny, nx), bool)
    mask[15:35, 20:40] = True
    Sz = np.exp(-(((np.arange(nx) - 30) / 8.0) ** 2))[None, :] * np.exp(-(((np.arange(ny) - 25) / 8.0) ** 2))[:, None]
    mechs = [{'name': 'a', 'localization': 'interface', 'shape': 'step', 'alpha0': 3e3, 'L': 50.0},
             {'name': 'b', 'localization': 'interface', 'shape': 'exp', 'alpha0': 2e3, 'L': 40.0}]
    old = 123.0 + sum(am.compute_mechanism_losses(mask, dx, y, Sz, mechs).values())
    for model in (None, {}, {'volume_scattering': {'enabled': False, 'C_dB_per_cm': 99}}):
        r = evaluate(mask, dx, y, Sz, 123.0, mechs, 450.0, model)
        assert abs(r['total'] - old) < 1e-9 and r['volume_scattering'] == 0.0, (model, r['total'], old)
    r0 = evaluate(mask, dx, y, Sz, 123.0, mechs, 450.0)
    rv = evaluate(mask, dx, y, Sz, 123.0, mechs, 225.0, {'volume_scattering': {'enabled': True, 'C_dB_per_cm': 2.0, 'p': 4}})
    assert abs(rv['volume_scattering'] - 2.0 * 100 * rv['gamma_core'] * 16.0) < 1e-9
    rb = evaluate(mask, dx, y, Sz, 123.0, mechs, 225.0, {'volume_scattering': {'enabled': True, 'C_dB_per_cm': 2.0, 'bands': ('pump',)}})
    assert rb['volume_scattering'] == 0.0
    ra = evaluate(mask, dx, y, Sz, 0.0, mechs, 225.0, {'absorption_lambda': {'p': 2.0}})
    assert abs(ra['absorption_interface'] - 4.0 * evaluate(mask, dx, y, Sz, 0.0, mechs, 450.0)['absorption_interface']) < 1e-9
    rs = evaluate(mask, dx, y, Sz, 100.0, mechs, 450.0, {'scattering_scale': 0.5})
    assert abs(rs['scattering_sidewall'] - 50.0) < 1e-9
    rc = evaluate(mask, dx, y, Sz, 100.0, mechs, 450.0, case('gl04_asgrown'))
    base = evaluate(mask, dx, y, Sz, 0.0, mechs, 450.0)['absorption_interface']
    assert abs(rc['scattering_sidewall'] - 10.0) < 1e-9 and abs(rc['absorption_interface'] - 2.3 * base) < 1e-9
    rsh = evaluate(mask, dx, y, Sz, 100.0, mechs, 225.0, case('gl04_asgrown'))
    assert abs(rsh['scattering_sidewall'] - 100.0) < 1e-9     # pump-band presets leave SH scattering alone
    assert evaluate(mask, dx, y, Sz, 123.0, mechs, 450.0, case('current'))['total'] == r0['total']
    print('loss_model self-test OK  (defaults == old model; volume/lambda/scale switches act)', r0['total'], old)


if __name__ == '__main__':
    _selftest()
