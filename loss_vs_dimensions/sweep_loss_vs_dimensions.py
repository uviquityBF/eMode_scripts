"""Loss vs. waveguide dimensions: fundamental TM00 at the pump wavelength.

Combines two loss mechanisms per (h_core, w_core) point:
  - Sidewall scattering loss: fully native EMode (roughness_rms/correlation_length on the core
    shape + em.scattering(), Volume Current Method) -- see emode_export.extract_scattering_loss_dB_per_m.
  - Non-uniform material absorption loss: NOT fed into EMode at all. The mode is solved
    lossless, its z-Poynting flux is exported once, and absorption_model.py post-processes
    arbitrary sidewall-/interface-localized absorption assumptions against that export in pure
    Python -- so re-exploring absorption assumptions never needs another EMode call.

IMPORTANT: run inspect_emode_outputs.py once first and check its output against the
ASSUMPTION comments in emode_export.py -- this script's native-scattering and field-export
extraction depends on those unverified assumptions about EMode's return shapes.

Checkpointed like the phase-matching pipeline: re-running skips (h, w) points already present
in RESULTS_CSV with a matching export file AND matching ROUGHNESS_RMS/CORRELATION_LENGTH (each
row records the roughness assumptions that produced its scattering_loss_dB_per_m, so a changed
assumption doesn't silently mix with old results), so an interrupted run or a transient
EMode.exe failure (see CLAUDE.md's known-gotchas) only costs the points not yet done.
"""

import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 '..', 'phase_matching_pipeline'))
import emode_helpers as pmh  # noqa: E402

import numpy as np  # noqa: E402

from emode_export import (  # noqa: E402
    extract_scattering_loss_dB_per_m,
    extract_mode_fields_for_export,
    build_core_mask_from_geometry,
)

# --- Fixed physical/material parameters -----------------------------------------------------
WAVELENGTH_PUMP = 450.0  # [nm]
EQ_O = ('(1+2.8032/(1-0.015287/x**2)+0.36335/(1-0.036095/x**2)'
        '-33508000/(1+367200000/x**2))**0.5')
EQ_E = ('(1+0.017061/(1-0.043855/x**2)+3.1976/(1-0.022642/x**2)'
        '-57269000/(1-74226000/x**2))**0.5')
ANISOTROPIC_EQUATION = f"[{EQ_O},{EQ_E},{EQ_O}]"
SIDEWALL_ANGLE = 5.0  # [deg], matches emode_helpers.setup_waveguide's default
SUBSTRATE_HEIGHT = 1000.0  # [nm], matches emode_helpers.setup_waveguide's default -- passed
# explicitly (rather than relying on that default) since the core/substrate interface position
# (y_bottom below) depends on it: confirmed against a live em.plot(component='Shapes') that the
# core sits directly on top of the substrate at y=SUBSTRATE_HEIGHT, NOT centered in the window.

# --- Sidewall roughness assumptions (fed into EMode's native scattering calc) -------------
ROUGHNESS_RMS = [2.0, 2.0]  # [nm]
CORRELATION_LENGTH = [50.0, 50.0]  # [nm]

# --- Solver settings --------------------------------------------------------------------
X_RESOLUTION, Y_RESOLUTION = 10.0, 10.0  # [nm]
NUM_MODES = 4  # small: only need the fundamental (index 0), a few extra for a sane FDM solve
MAX_EFFECTIVE_INDEX = 2.6
FUND_MODE_IDX = 0

# --- Geometry sweep: width sweep at a couple of fixed heights (edit freely) ----------------
#HEIGHTS = [300.0, 340.0, 380.0]
HEIGHTS = [340.0]
WIDTHS = np.arange(300.0, 1001.0, 50.0)
TARGET_POINTS = [(h, w) for h in HEIGHTS for w in WIDTHS]

RESULTS_CSV = 'loss_vs_dimensions_results.csv'
EXPORTS_DIR = 'field_exports'
FIELDNAMES = ['h_core', 'w_core', 'n_eff', 'scattering_loss_dB_per_m',
              'roughness_rms', 'correlation_length', 'export_path', 'status']


def export_path_for(h_core, w_core):
    return os.path.join(EXPORTS_DIR, f'h{h_core:.1f}_w{w_core:.1f}.npz')


def load_done_points(csv_path):
    """Points already solved under the CURRENT ROUGHNESS_RMS/CORRELATION_LENGTH -- a row solved
    under different roughness assumptions (module constants edited since that row was written)
    is deliberately NOT treated as done, so changing them and re-running picks up the change
    automatically instead of silently mixing old and new assumptions in one results file.
    """
    done = {}
    if not os.path.exists(csv_path):
        return done
    current_roughness = json.dumps(ROUGHNESS_RMS)
    current_correlation = json.dumps(CORRELATION_LENGTH)
    with open(csv_path, newline='') as f:
        for row in csv.DictReader(f):
            if (row['status'] == 'ok' and os.path.exists(row['export_path'])
                    and row.get('roughness_rms') == current_roughness
                    and row.get('correlation_length') == current_correlation):
                done[(float(row['h_core']), float(row['w_core']))] = row
    return done


def append_result(csv_path, row):
    write_header = not (os.path.exists(csv_path) and os.path.getsize(csv_path) > 0)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def solve_one_point(h_core, w_core, simulation_name='loss_vs_dimensions'):
    """Solve the lossless fundamental at (h_core, w_core), compute native scattering loss, and
    export (x, y, core_mask, Ex, Ey, Ez, Sz) for later absorption_model.py/scattering_model.py
    post-processing. Returns a result dict, or raises on failure (caller logs it and moves on).
    """
    em = pmh.launch_session(simulation_name, clear='all')
    try:
        pmh.setup_waveguide(em, ANISOTROPIC_EQUATION, h_core, w_core,
                             sidewall_angle=SIDEWALL_ANGLE, substrate_height=SUBSTRATE_HEIGHT)
        em.shape(name='core', roughness_rms=ROUGHNESS_RMS, correlation_length=CORRELATION_LENGTH)

        em.settings(wavelength=WAVELENGTH_PUMP, num_modes=NUM_MODES,
                    x_resolution=X_RESOLUTION, y_resolution=Y_RESOLUTION,
                    max_effective_index=MAX_EFFECTIVE_INDEX)
        fdm = em.FDM()
        n_eff = float(np.real(fdm['n_eff_tilde'][FUND_MODE_IDX]))

        em.confinement(shape_list='core')
        em.scattering(shape='core')
        scattering_loss = extract_scattering_loss_dB_per_m(em, mode_idx=FUND_MODE_IDX)

        x, y, fields = extract_mode_fields_for_export(em, mode_idx=FUND_MODE_IDX)
        # y_bottom: confirmed via a live em.plot(component='Shapes') that the core sits directly
        # on top of the substrate (not centered in the window) -- the core/substrate interface
        # is at y=SUBSTRATE_HEIGHT in this grid's coordinates, independent of h_core/window_margin.
        y_bottom = SUBSTRATE_HEIGHT
        core_mask = build_core_mask_from_geometry(x, y, h_core, w_core, SIDEWALL_ANGLE, y_bottom)
    finally:
        em.close(save=False)

    return {'n_eff': n_eff, 'scattering_loss_dB_per_m': scattering_loss,
            'x': x, 'y': y, 'fields': fields, 'core_mask': core_mask}


def main():
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    done = load_done_points(RESULTS_CSV)
    remaining = [p for p in TARGET_POINTS if p not in done]
    print(f"{len(done)} point(s) already done, {len(remaining)} remaining.")

    for h_core, w_core in remaining:
        print(f"\n=== h={h_core}, w={w_core} ===")
        export_path = export_path_for(h_core, w_core)
        try:
            result = solve_one_point(h_core, w_core)
            fields = result['fields']
            np.savez(export_path, x=result['x'], y=result['y'],
                     Ex=fields['Ex'], Ey=fields['Ey'], Ez=fields['Ez'], Sz=fields['Sz'],
                     core_mask=result['core_mask'], h_core=h_core, w_core=w_core,
                     n_eff=result['n_eff'], wavelength_pump=WAVELENGTH_PUMP)
            row = {'h_core': h_core, 'w_core': w_core, 'n_eff': result['n_eff'],
                   'scattering_loss_dB_per_m': result['scattering_loss_dB_per_m'],
                   'roughness_rms': json.dumps(ROUGHNESS_RMS),
                   'correlation_length': json.dumps(CORRELATION_LENGTH),
                   'export_path': export_path, 'status': 'ok'}
            print(f"  n_eff={result['n_eff']:.5f}, "
                  f"scattering_loss={result['scattering_loss_dB_per_m']:.3g} dB/m")
        except Exception as e:
            print(f"  FAILED: {repr(e)}")
            row = {'h_core': h_core, 'w_core': w_core, 'n_eff': '',
                   'scattering_loss_dB_per_m': '',
                   'roughness_rms': json.dumps(ROUGHNESS_RMS),
                   'correlation_length': json.dumps(CORRELATION_LENGTH),
                   'export_path': '', 'status': f'failed: {e!r}'}
        append_result(RESULTS_CSV, row)


if __name__ == '__main__':
    main()
