"""Diagnostic: where do low-order SH partners (TM02/TM20) phase-match? Wide SH window."""

import copy

from survey_config import SETTINGS as _BASE

SETTINGS = copy.deepcopy(_BASE)
SETTINGS.update({'lambda_sh_min': 215.0, 'lambda_sh_max': 275.0, 'refine_top_n': 12})

GEOMETRIES = [('ridge', {'h_core': 300.0, 'w_core': 500.0}),
              ('ridge', {'h_core': 350.0, 'w_core': 500.0})]
