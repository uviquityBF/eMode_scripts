# ALN_am135comsol

Archived 2026-08-25 when the notebook moved to per-dataset run folders (`runs/<RUN_TAG>/`) ahead of
a second run (`ALN_avgLibrary82026`). This folder holds everything Steps 4-9 produced for this
dataset: `general_pipeline_results.csv`, `fund_target_overlap.csv` / `_merged.csv`,
`phase_matching_surfaces.png`, `overlap_surfaces.png`, `walked_indices_checkpoint.json`,
`failed_points.csv`, `field_plots/`. Final state as committed in `52611eb`.

## Ellipsometry equations (cell1, as committed in 52611eb)

```python
eq_o = '(1+2.8032/(1-0.015287/x**2)+0.36335/(1-0.036095/x**2)-33508000/(1+367200000/x**2))**0.5'
eq_e = '(1+0.017061/(1-0.043855/x**2)+3.1976/(1-0.022642/x**2)-57269000/(1-74226000/x**2))**0.5'
anisotropic_equation = f"[{eq_o},{eq_e},{eq_o}]"
```

## Geometry

- `h_anchor, w_anchor = 350.0, 550.0`; `dx, dy = 10.0, 10.0`
- `h_values = [335.0, 350.0, 365.0]`
- TM04: `w = 550.0 + 12.5*i for i in range(37)` (550-1000nm, 12.5nm step)
- TM40: `w = 300.0 + 25.0*i for i in range(11)` (300-550nm, 25nm step), `anchor_point=(350.0, 400.0)`

## modes_of_interest

```python
'TM04': dict(anchor_mode_idx=42, num_modes=130, window=25, overlap_threshold=0.95,
             review_threshold=0.75, max_jump_distance=20.0,
             wavelengths_shg=np.arange(200, 300, 2.0), tracking_wavelength=227)
'TM40': dict(anchor_point=(350.0, 400.0), anchor_mode_idx=23, num_modes=50, window=25,
             overlap_threshold=0.95, review_threshold=0.75, max_jump_distance=30.0,
             wavelengths_shg=np.arange(200, 320, 2.0), tracking_wavelength=242)
```

## EXCLUDED_POINTS (45 total: 18 TM04 + 27 TM40)

Points where visual field-plot review found the tracked mode was not actually the named mode (see
Part I of the Mode Tracking Manual for why this happens). Full list preserved in git history for
this repo at commit `52611eb` (Step 7's first cell) -- not re-copied here to avoid two sources of
truth drifting apart.
