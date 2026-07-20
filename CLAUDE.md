# eMode_scripts

EMode Photonix (`EMode.exe`) photonics simulation scripts, run via the `emodeconnection` Python
package. Primary work happens across two machines (a laptop and this desktop) that share this repo
via git — `git pull` before starting work, `pip install -r requirements.txt` in `.venv` if it changed.

## Repo layout

- `phase_matching_pipeline/` — the active deliverable. `General_PhaseMatching_Pipeline.ipynb` is the
  main notebook (import `emode_helpers.py` from the same folder). `reference/` holds prior/ad-hoc
  work kept for context only (not meant to be the active flow): the predecessor
  `PhaseMatching_Table.ipynb`, `EMode_Troubleshooting_Log.md`, `EMode_Function_Reference.md`,
  `TM04_TM40_Summary.md`, raw width/modal-index data CSVs, and a standalone copy of
  `emode_helpers.py` so those notebooks still run if reopened.
- `legacy_scripts/` — everything predating this Claude-assisted work (the original `AlN_2D_*`
  scripts/notebooks etc.). Not maintained, kept for reference only.
- `.eph` simulation files are gitignored everywhere in the repo (pattern has no leading slash, so it
  applies at any depth) — keep them out of commits regardless of which folder they land in.

## Known gotchas (from hard-won troubleshooting — see `phase_matching_pipeline/reference/EMode_Troubleshooting_Log.md` for full detail)

- **EMode license is single-seat.** "No licenses are available" on one machine usually means the
  other machine (laptop vs. desktop) has an active session, not a code bug — check there first.
- **EMode.exe is unstable under sustained/repeated calls in one long-lived process.** Transient
  `PermissionError` / `ValueError("invalid literal for int()...")` during long runs are usually this,
  not a real bug — the pipeline's checkpoint/resume design (see below) exists specifically so a
  transient failure only costs that one point, not the whole run.
- **`em.plot(file_name=...)` fails (`EModeError('unexpectected exception')`) if the path has a
  subdirectory component and isn't absolute.** A bare filename or a fully absolute path both work;
  `subdir/name` (either slash style) doesn't. Always pass an absolute path.
- **Raw mode index is not a stable identifier across geometry or wavelength** — it can shift by 7+
  from a modest width change. Always re-verify by overlap/visual survey, never assume index carries
  over; this is the whole reason the pipeline tracks mode index via `walk_mode_across_points` rather
  than reusing a fixed index across the grid.
- **VS Code's open notebook editor keeps its own in-memory buffer.** External edits to the `.ipynb`
  (including edits made by Claude) don't show up until you focus the tab and run
  `Ctrl+Shift+P` → **File: Revert File** (or close/reopen the tab) — otherwise the next run/save can
  silently clobber the edits back to the pre-edit version.

## Pipeline design notes

`General_PhaseMatching_Pipeline.ipynb` Steps 4-5 checkpoint progress to
`walked_indices_checkpoint.json` / `general_pipeline_results_partial.csv` after every point, and
resume from them automatically on re-run (skipping already-solved/successful points, retrying
failed/saturated ones). Step 5 also records a field plot per matched point in `field_plots/`
(fundamental plots are named `..._fund_TM00.png`, since the fundamental is always TM00 regardless of
the target mode). Step 7 fits `n(WL, h, w)` and `WL_pm(h, w)` surfaces from the results table using
Hermite-style least squares (value + local gradient, since EMode already computes gradients at every
grid point) — `EXCLUDED_POINTS` near the top of Step 7 lets you drop manually-identified bad points
(e.g. mode misidentification, checked via `field_plots/`) from the fits without touching the CSV.

## Deferred / pending work

- **Fresh-run versioning**: the checkpoint/resume system has no concept of "these inputs changed" —
  if you rerun after changing the ellipsometry data (`eq_o`/`eq_e` in cell 1) or non-h/w geometry
  (sidewall angle, window margins, substrate/topclad materials — currently hardcoded defaults inside
  `emode_helpers.setup_waveguide`, not exposed as notebook parameters at all), it will silently resume
  the OLD checkpoint instead of starting fresh. Needs: (1) deciding which geometry params to expose
  as notebook variables, (2) a fingerprint (e.g. hash of `anisotropic_equation` + those params) stored
  in both checkpoint files, compared on load to detect an incompatible prior run.
