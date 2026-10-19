"""Optimism bookkeeping for the Cerenkov (row 8) study, per user direction 2026-10-19.

Two independent uncertainties are tracked on every result instead of being baked in:

LOSS (ScAlN k at the SH wavelength, 225 nm, cannot be measured by the user):
    K_SCALES maps a case name to a multiplier on the Baumler-fit k(225 nm).
    'lossless' (0) is the most optimistic bound; 'fit' (1) is as fitted; 'fit_x0.25' is the
    in-between case; 'fit_x2' a pessimistic sensitivity. The k=0 point is what identifies the
    most-optimistic case, so it is always included.

d33 (ScAlN chi(2) enhancement -- sputtered Yoshioka 2021 is the optimistic source the project
chose on 2026-10-12, Lee et al. 2026 / MBE finds d33 ~ 0 with only d31 enhanced):
    d_scenarios(sc_fraction) -> {name: (d33, d31, d15)} pm/V. 'yoshioka' is the working value
    already used project-wide (survey_config_cerenkov_scaln_phase2.D33_D31_BY_COMP).
    'frac_<f>' keeps the fraction f of Yoshioka's enhancement over AlN (4.7/0.1) -- a one-knob
    "how much of the optimism is present" axis. 'mbe_like' is d33 ~ 0.3 with d31 interpolated from
    the MBE table quoted in Lee 2026 (0.84/1.81/2.59 pm/V at 10/20/30% Sc; >30% extrapolated),
    d15 = d31 by the project convention.
Because radiated power is a quadratic form in (d33, d31, d15), cerenkov_cases.py stores the 3x3
matrices K and W; any further scenario can be evaluated later with cerenkov_fdfd.kappa_for()
without re-solving.
"""
K_SCALES = {'lossless': 0.0, 'fit_x0.05': 0.05, 'fit_x0.1': 0.1, 'fit_x0.25': 0.25,
            'fit_x0.5': 0.5, 'fit': 1.0, 'fit_x2': 2.0}

AIN = (4.7, 0.1)

# (d33, d31) pm/V, the working values already used for rows 5.x / phase 2; 0.275 is the midpoint of the
# 23% and 32% values (same linear interpolation used for the 27.5% index blend)
_YOSHIOKA = {0.23: (44.20, 2.800), 0.275: (49.4, 3.375), 0.32: (54.60, 3.950), 0.41: (71.90, 5.200)}


def sc_fraction_from_key(chi2_key):
    """'ScAlN_0.28' is the 27.5% interpolated composition (key rounded for the d-tensor table)."""
    x = round(float(chi2_key.split('_')[1]), 3)
    return 0.275 if abs(x - 0.28) < 1e-9 else x


def d_scenarios(sc):
    d33y, d31y = _YOSHIOKA[sc]
    out = {'yoshioka': (d33y, d31y, d31y)}
    for f in (0.75, 0.5, 0.25, 0.0):
        d33 = AIN[0] + f * (d33y - AIN[0])
        d31 = AIN[1] + f * (d31y - AIN[1])
        out[f'frac_{f:g}'] = (d33, d31, d31)
    d31_mbe = 0.84 + 0.088 * (100 * sc - 10)
    out['mbe_like'] = (0.3, d31_mbe, d31_mbe)
    return out
