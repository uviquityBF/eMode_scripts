"""Settings + geometry list for survey.py. Edit freely; changing anything that affects results
changes each geometry's fingerprint, so those geometries are recomputed on the next run
(absorption mechanisms are excluded from the fingerprint -- they're cheap to reprocess from the
exported fields).
"""

import numpy as np

SETTINGS = {
    # SH window and scan
    'lambda_sh_min': 215.0,          # [nm]
    'lambda_sh_max': 235.0,          # [nm]
    'lambda_step': 1.0,              # [nm] SH scan step (tracking needs ~<= 1 nm)
    'pump_points': 5,                # pump wavelengths solved across the window (then interpolated)
    # modes
    'num_pump_tm': 3,                # lowest-order TM-like pump modes kept
    'num_pump_te': 2,                # lowest-order TE-like pump modes kept (d31/d15 channels)
    'num_pump_candidates': 6,        # modes solved per symmetry class when picking pumps
    'num_sh_modes': 30,              # SH modes per step, nearest the pumps' n_eff
    'num_sh_refine_modes': 12,       # SH modes solved when re-identifying at a crossing
    'sh_window_margin': 0.10,        # warn if the SH n_eff span doesn't cover pumps +/- this
    'pump_group_span': 0.10,         # pumps within this n_eff spread share one SH solve per step
    # refinement (re-solve at the crossing + losses + field export) for the best screened ones
    'refine_top_n': 8,               # per geometry
    'refine_min_nce_pct': 0.01,      # [%/W/cm^2] don't refine below this screened NCE
    # a crossing whose screened SH field hasn't decayed to this fraction of its own peak by the
    # simulation window's edge is a window/box-mode artifact (quantized by the window's hard
    # walls, not real lateral confinement -- see shg_physics.lateral_edge_ratio), excluded from
    # refine_top_n's candidate pool so the refine budget isn't spent on it. Same default as
    # summarize_run.py's MAX_SH_EDGE_RATIO, which independently re-checks at full refined
    # resolution as a second pass -- found 2026-10-05 after a sweep's reported best crossing
    # (NCE 293 %/W/cm^2) turned out to be exactly this; see PLAN.md.
    'max_sh_edge_ratio': 0.02,
    # numerics
    'resolution': 10.0,              # [nm] x and y
    # roughness (EMode-native scattering), [vertical (sidewall), horizontal (top/bottom)]
    'roughness_rms': [2.5, 0.3],     # [nm]
    'correlation_length': [50.0, 10.0],  # [nm]
    # chi(2), pm/V (PLAN.md tensor table); d_ref is used for A_SHG
    'd_tensors_pm': {'AlN': {'d33': 4.7, 'd31': 0.1, 'd15': 0.1}},
    'd_ref_material': 'AlN',
    # post-processed absorption [dB/m in-layer alpha0, nm lengths] -- pump: current
    # Loss_vs_Dimensions_Dev.ipynb baseline; SH: unknown at 225 nm yet, so none.
    'pump_absorption_mechanisms': [
        {'name': 'Dislocations (growth interface)', 'localization': 'interface', 'shape': 'exp', 'alpha0': 0.2e4, 'L': 40.0},
        {'name': 'C impurities (growth interface)', 'localization': 'interface', 'shape': 'step', 'alpha0': 0.35e4, 'L': 50.0},
        {'name': 'Si impurities (growth interface)', 'localization': 'interface', 'shape': 'step', 'alpha0': 0.35e4, 'L': 50.0},
        {'name': 'O impurities (growth interface)', 'localization': 'interface', 'shape': 'step', 'alpha0': 0.5e4, 'L': 50.0},
    ],
    'sh_absorption_mechanisms': [],
}

# (family, params) -- Step 1: existing ridge only.
GEOMETRIES = [('ridge', {'h_core': 350.0, 'w_core': 400.0})]

# A wider trial grid (used by run name 'trial_grid' via survey_config_grid.py if desired):
TRIAL_GRID = [('ridge', {'h_core': float(h), 'w_core': float(w)})
              for h in (300.0, 350.0, 400.0) for w in np.arange(300.0, 801.0, 100.0)]
