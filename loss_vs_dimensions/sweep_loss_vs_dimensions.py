"""Loss vs. waveguide dimensions: fundamental TM00 at the pump wavelength.

Combines two loss mechanisms per (h_core, w_core) point:
  - Scattering loss: fully native EMode (roughness_rms/correlation_length on the core shape +
    em.scattering(), Volume Current Method) -- see emode_export.extract_scattering_components_dB_per_m.
    EMode's roughness_rms/correlation_length lists are [vertical (sidewall), horizontal
    (top/bottom)] per its docs (docs.emodephotonix.com/emodeguide/setup.html) -- the results CSV
    logs vertical/horizontal/sum separately since they can have very different width-dependence
    (confirmed: scattering_sum == scattering_vertical_edges + scattering_horizontal_edges).
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
    extract_scattering_components_dB_per_m,
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
ROUGHNESS_RMS = [2.0, 0.3]  # [nm]  [vertical (sidewall), horizontal (top/bottom)]
CORRELATION_LENGTH = [50.0, 10.0]  # [nm]

# --- Solver settings --------------------------------------------------------------------
X_RESOLUTION, Y_RESOLUTION = 10.0, 10.0  # [nm]
NUM_MODES = 4  # small: only need the fundamental (index 0), a few extra for a sane FDM solve
MAX_EFFECTIVE_INDEX = 2.6
FUND_MODE_IDX = 0
TE_FRACTION_WARN_THRESHOLD = 0.1  # warn if FUND_MODE_IDX's TE_fraction exceeds this -- a sign
# mode 0 may no longer be the TM-dominant fundamental at that geometry (see solve_one_point)

# --- Geometry sweep: width sweep at a couple of fixed heights (edit freely) ----------------
HEIGHTS = [300.0, 340.0, 380.0]
#HEIGHTS = [340.0]
WIDTHS = np.arange(300.0, 1001.0, 50.0)
TARGET_POINTS = [(h, w) for h in HEIGHTS for w in WIDTHS]

RESULTS_CSV = 'loss_vs_dimensions_results.csv'
EXPORTS_DIR = 'field_exports'
FIELDNAMES = ['h_core', 'w_core', 'n_eff', 'scattering_loss_dB_per_m',
              'scattering_vertical_dB_per_m', 'scattering_horizontal_dB_per_m',
              'roughness_rms', 'correlation_length', 'export_path', 'status']


def export_path_for(h_core, w_core):
    return os.path.join(EXPORTS_DIR, f'h{h_core:.1f}_w{w_core:.1f}.npz')


def migrate_csv_schema(csv_path):
    """If csv_path exists with a header that doesn't match the current FIELDNAMES (i.e. this
    module gained/lost/reordered a column since that file was written), rewrite it with the
    correct header, keeping only the rows that already have the current column count (rows from
    before the schema change are dropped -- they're stale under load_done_points' own checks
    anyway, e.g. missing a since-added column, so nothing usable is lost).

    Without this, append_result's write_header only checks whether the file is missing/empty,
    NOT whether an existing file's header still matches -- so a schema change used to silently
    append new-shape rows under a stale old-shape header, corrupting the file (hit once already:
    a 45-row sweep completed cleanly but subsequent DictReader-based reads KeyError'd on the new
    columns for the stale rows, since the header still listed the old, shorter column set).

    Always writes a `<csv_path>.schema_backup` (overwritten each time) before rewriting, so a
    migration is never silently destructive.
    """
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        return
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader, [])
        if header == FIELDNAMES:
            return
        rows = [r for r in reader if len(r) == len(FIELDNAMES)]

    backup_path = csv_path + '.schema_backup'
    import shutil
    shutil.copy(csv_path, backup_path)
    print(f"  Schema changed ({len(header)} -> {len(FIELDNAMES)} columns): backed up to "
          f"{backup_path}, migrating {len(rows)} still-valid row(s), rewriting header.")

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(FIELDNAMES)
        writer.writerows(rows)


def load_done_points(csv_path):
    """Points already solved under the CURRENT ROUGHNESS_RMS/CORRELATION_LENGTH, with the
    vertical/horizontal scattering split already present -- a row solved under different
    roughness assumptions (module constants edited since that row was written) is deliberately
    NOT treated as done, so changing them and re-running picks up the change automatically
    instead of silently mixing old and new assumptions in one results file. The explicit
    scattering_vertical_dB_per_m presence check additionally guards against a stale row from
    before that column existed, which the roughness/correlation match alone wouldn't catch if
    the values happened to be unchanged.
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
                    and row.get('correlation_length') == current_correlation
                    and row.get('scattering_vertical_dB_per_m')):
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
        # TE_fraction is a free byproduct of FDM() (no extra EMode call) -- FUND_MODE_IDX=0 is
        # only actually TM00 if this is near 0. Mode index is NOT a stable identifier across
        # geometry (see CLAUDE.md's known gotchas re: the phase-matching pipeline hitting this
        # same issue) and this sweep has no overlap-tracking safeguard like that pipeline does,
        # so this is a live sanity check, not a guarantee -- see TE_FRACTION_WARN_THRESHOLD below.
        te_fraction = float(fdm['TE_fraction'][FUND_MODE_IDX])

        em.confinement(shape_list='core')
        em.scattering(shape='core')
        scattering = extract_scattering_components_dB_per_m(em, mode_idx=FUND_MODE_IDX)

        x, y, fields = extract_mode_fields_for_export(em, mode_idx=FUND_MODE_IDX)
        # y_bottom: confirmed via a live em.plot(component='Shapes') that the core sits directly
        # on top of the substrate (not centered in the window) -- the core/substrate interface
        # is at y=SUBSTRATE_HEIGHT in this grid's coordinates, independent of h_core/window_margin.
        y_bottom = SUBSTRATE_HEIGHT
        core_mask = build_core_mask_from_geometry(x, y, h_core, w_core, SIDEWALL_ANGLE, y_bottom)
    finally:
        em.close(save=False)

    return {'n_eff': n_eff, 'scattering': scattering, 'te_fraction': te_fraction,
            'x': x, 'y': y, 'fields': fields, 'core_mask': core_mask}


def main():
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    migrate_csv_schema(RESULTS_CSV)
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
            scattering = result['scattering']
            row = {'h_core': h_core, 'w_core': w_core, 'n_eff': result['n_eff'],
                   'scattering_loss_dB_per_m': scattering['sum'],
                   'scattering_vertical_dB_per_m': scattering['vertical'],
                   'scattering_horizontal_dB_per_m': scattering['horizontal'],
                   'roughness_rms': json.dumps(ROUGHNESS_RMS),
                   'correlation_length': json.dumps(CORRELATION_LENGTH),
                   'export_path': export_path, 'status': 'ok'}
            print(f"  n_eff={result['n_eff']:.5f}, TE_fraction={result['te_fraction']:.4g}, "
                  f"scattering: sum={scattering['sum']:.3g}, "
                  f"vertical={scattering['vertical']:.3g}, "
                  f"horizontal={scattering['horizontal']:.3g} dB/m")
            if result['te_fraction'] > TE_FRACTION_WARN_THRESHOLD:
                print(f"  WARNING: TE_fraction={result['te_fraction']:.4g} exceeds "
                      f"TE_FRACTION_WARN_THRESHOLD={TE_FRACTION_WARN_THRESHOLD} at h={h_core}, "
                      f"w={w_core} -- mode 0 may no longer be the TM-dominant fundamental here; "
                      f"this point's results may be mislabeled. Consider em.plot() at this "
                      f"geometry to check visually.")
        except Exception as e:
            print(f"  FAILED: {repr(e)}")
            row = {'h_core': h_core, 'w_core': w_core, 'n_eff': '',
                   'scattering_loss_dB_per_m': '', 'scattering_vertical_dB_per_m': '',
                   'scattering_horizontal_dB_per_m': '',
                   'roughness_rms': json.dumps(ROUGHNESS_RMS),
                   'correlation_length': json.dumps(CORRELATION_LENGTH),
                   'export_path': '', 'status': f'failed: {e!r}'}
        append_result(RESULTS_CSV, row)


if __name__ == '__main__':
    main()
