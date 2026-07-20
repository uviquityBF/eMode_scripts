# EMode Function Reference

Pulled from the official docs at https://docs.emodephotonix.com/emodeguide.html (fetched 2026-07-15).
All functions below are called as `em.<name>(...)` where `em = emc.EMode()`. None of these are
real Python methods — `emodeconnection`'s `EMode.__getattr__` (emodeconnection.py:286) forwards any
attribute call straight to the EMode.exe backend as `EM_<name>`, so this page is the only real
parameter reference; there are no local docstrings.

Every function also accepts `simulation_name` (str, default `'emode'`) to target a specific
simulation instance; omitted below for brevity except where it's the only parameter.

---

## File Management
Source: https://docs.emodephotonix.com/emodeguide/file-management.html

### init
Creates a simulation instance with an associated `.eph` file. Called automatically by `emc.EMode()`.
- `save_path` (str, default `'.'`)
- `simulation_name` (str, default `'emode'`)

### open
Loads an existing `.eph` file.
- `save_path` (str, default `'.'`)
- `simulation_name` (str, default `'emode'`)
- `new_simulation_name` (bool|str, default `False`) — alternate name to avoid overwriting original
- `force` (bool, default `False`)

### get
Retrieves a variable/parameter from the simulation into Python.
- `key` (str, required) — one of `Ex, Ey, Ez, Hx, Hy, Hz, Sx, Sy, Sz`, or `'S_matrix'` for EMode3D
- `profile` (str, default `'_default'`)

### get_fields
Retrieves field data.
- `key` (str|list[str], required)
- `include_expand` (bool, default `True`)
- `include_pml` (bool, default `True`)
- `unfold` (bool, default `True`) — full window vs. solved window only
- `profile` (str, default `'_default'`)
→ returns `dict[float, Field]` keyed by wavelength

### get_grid
Retrieves grid configuration.
- `include_expand`, `include_pml`, `unfold` (bool, default `True` each)
- `profile` (str, default `'_default'`)
→ returns `dict[float, Grid]` keyed by wavelength

### get_shape
Retrieves shape data + metadata (scattering/confinement results).
- `key` (str, required)
- `profile` (str, default `'_default'`)

### get_profile
Retrieves the full profile object (settings, shapes, grid, field data).
- `profile` (str, default `'_default'`)

### create_profile_set
Groups several single-wavelength profiles into one multi-wavelength set (shapes must match across
profiles). Originals are removed after grouping.
- `profiles` (str|list[str], required)
- `profile_set_name` (str, default `'_default'`)

### delete_profile
Removes a named profile, or resets `'_default'`.
- `profile` (str, required)

### clear_field_data
Deletes `Fx, Fy, Ex, Ey, Ez, Hx, Hy, Hz, Sx, Sy, Sz, x, y, permittivity, permeability` from every
profile to shrink the `.eph` file. `profile` param is currently ignored (clears all).

### save
Saves the simulation file, keeps it open.
- `save_all_fields` (bool, default `False`) — full E/H/S data vs. raw only (Fx, Fy)
- `file_type` (str, default `'eph'`) — `'eph'` or `'mat'`
- `close` (bool, default `False`)
- `new_save_path` (str, default `None`)

### close
Saves or deletes the simulation file (called via `emodeconnection`'s `close()`).
- `save` (bool, default `True`)
- `save_all_fields` (bool, default `False`)
- `file_type` (str, default `'eph'`)

---

## Setup
Source: https://docs.emodephotonix.com/emodeguide/setup.html

### settings
Simulation settings for mode solving and mesh generation. **`window_width` and `window_height` are
required, no default.**

| Name | Type | Default |
|---|---|---|
| profile | str | `'_default'` |
| wavelength | float [nm] | 1550 |
| frequency | float [Hz] | None |
| x_resolution | float [nm] | 10 |
| y_resolution | float [nm] | 10 |
| window_width | float [nm] | **required** |
| window_height | float [nm] | **required** |
| boundary_condition | str (2 chars) | `'00'` |
| num_modes | int | 1 |
| field_to_solve | `'Et'`\|`'Ht'` | `'Et'` |
| max_effective_index | float | 0 |
| tolerance | float | 1e-12 |
| bend_radius | float [nm] | 0 |
| pml_NSEW_bool | list[4] | `[0,0,0,0]` |
| num_pml_layers | int or list[4] | 10 |
| remove_pml_modes_bool | bool | False |
| background_material | str or MaterialProperties/MaterialSpec | `"Vacuum"` |
| expansion_resolution | float or list [nm] | 20 |
| expansion_size | float or list [nm] | 0 |
| subpixel_avg | bool | True |
| generate_chi2 | bool | False |
| include_heat | bool | True |
| propagation_resolution | float [nm] | wavelength/10 |
| eme_scattering | bool | False |

Note: `boundary_condition` is a **2-character string**, not a single value like `'TM'` seen in some
scripts — worth double-checking against actual accepted values if a script uses a non-2-char string.

### add_material
Registers a custom material via wavelength-dependent refractive index equation(s).
- `name` (str, required)
- `refractive_index_equation` (str or list[3], required)
- `wavelength_unit` (`'nm'`\|`'um'`, default `'um'`)
- `wavelength_range` (list [um], default `[0.2, 2.0]`)
- `citation` (str, default `'User defined.'`)
- `loss` (float [dB/m], default 0)
- `thermal_conductivity` (float [W/m·K], default 1e-10)
- `resistivity` (float [Ohm-nm], default infinity)
- `dn_dT` (float [K⁻¹], default 0)
- `eps_r_dc` (float, default 1.0)
- `d` (list 3x6 or None, default None) — 2nd-order nonlinear d-matrix
- `phi`, `theta` (float, default 0) — crystal orientation angles

### import_database
Loads custom materials from an external text file.
- `filename` (str, required)

File format example (note this example happens to use `^` for power — see `add_material` below,
this is not representative of the inline equation parser):
```
name = custom_SiO2
refractive_index_equation = (1 + 0.696166/(1 - (0.0684043/x)^2) + 0.4079426/(1 - (0.1162414/x)^2) + 0.8974794/(1 - (9.896161/x)^2))^0.5
wavelength_unit = um
wavelength_range = [0.21, 6.7]
citation = '(1) I. H. Malitson, "Interspecimen comparison of the refractive index of fused silica," J. Opt. Soc. Am. 55, 1205 (1965).'
```

### shape
Creates/modifies a geometric shape with material assignment.
- `name` (str, default auto-generated)
- `material` (str or MaterialSpec/MaterialProperties, default `"Vacuum"`)
- `loss_dB_per_m` (float, default 0)
- `vertices` (list or int, default 0)
- `width` (float, default `window_width`)
- `height` (float, default 0)
- `position` (list[2], default `(0, 'auto')`)
- `mask` (float or list, default `width`)
- `mask_offset` (float or list, default 0)
- `tone` (`'n'`/`'N'`/`'p'`/`'P'`, default `'n'`)
- `etch_depth` (float, default 0)
- `sidewall_angle` (float [degrees], default 0)
- `fill_material` (str or MaterialSpec/MaterialProperties, default `"transparent_fill"`)
- `correlation_length` (float or list [nm], default `[0,0]`)
- `roughness_rms` (float or list [nm], default `[0,0]`)
- `shape_type` (str, default `'planar'`) — e.g. `'conformal'` for conformal overlays
- `priority` (float, default auto-generated)
- `fem_resolution` (float [nm], default 500)
- `current` (float [A], default 0)
- `voltage` (float [V], default None)
- `heat_only` (bool, default False)

### reset
Clears stored settings/shapes.
- `kind` (`'shapes'`/`'settings'`/`'all'`, default `'shapes'`)

---

## Solver / Analysis
Source: https://docs.emodephotonix.com/emodeguide/solver-analysis.html

### FDM
Computes waveguide modes via finite difference method; auto-generates mesh.
- `profile` (str or int, default `'_default'`)
- `section` (str, default None) — EME section name to solve a slice
- `propagation_distance` (float [nm], default None)
- `mode_filter` (`'forward'`/`'backward'`/`'none'`, default `'forward'`)
- `fLanczos` (int, default 5)
- `solve_type` (`'isotropic'`/`'anisotropic'`/`'auto'`, default `'auto'`)
- `include_heat` (bool, default True)
- `scattering` (bool, default False) — auto-calc interfacial scattering
→ returns dict with `field`, `n_eff_tilde`, `TE_fraction`, `TE_indices`, `TM_indices`

### sweep
Parameter sweep across settings/shape/section params.
- `key` (str) — `'settings, KEY'`, `'shape, NAME, KEY'`, or `'section, NAME, KEY'`
- `values` (list or array)
- `solve_type` (`'mesh'`/`'FDM'`/`'EME'`, default auto)
- `result` (str or list, default `'effective_index'`) — any inspectable value, `'scattering_loss'`, or `'mode_order'`
- `seed` (bool, default True) — seed each step with previous results

### confinement
Confinement factor of a shape (area used to define the index profile, by default).
- `profile` (str, default `'_default'`)
- `shape_list` (str or list, default `'all'`)
- `mode_list` (str or list, default `'all'`) — `'all'`, `'TE'`, `'TM'`, or indices
- `vertices` (list of Nx2, default None) — polygon override
- `ignore_priority` (bool, default False)

### effective_area
Computes effective modal area(s) (µm²). Stores `effective_area` array; shown in `report()`.
- `profile` (str, default `'_default'`)

### orthogonality
Max mode-overlap value among the mode list (should be < 1e-3 for an accurate mode list).
- `profile` (str or int, default `'_default'`)

### group_index
Group index via FDM run twice (original + 0.01% longer wavelength). Stores `group_index` array;
shown in `report()`.
- `profile` (str, default `'_default'`)

### report
Displays mode report table (mode #, n_eff, TE fraction, loss dB/m, confinement, effective area).
- `profile` (str, default `'_default'`)
- `save` (bool, default False)
- `file_name` (str, default `'mode_report'`)
- `file_type` (`'txt'`/`'latex'`/`'csv'`, default `'txt'`)

### label_profile
Snapshots current settings + field data as a labeled dataset (`dataset_NAME`).
- `name` (str, default `'0'`)

### overlap
Overlap integral between two modes (Coldren et al. 2012 formula).
- `profile_a` (str or int, default `'_default'`)
- `mode_a` (int, default 0)
- `simulation_name_a` (str, default `'emode'`)
- `profile_b` (str or int, default `'_default'`)
- `mode_b` (int, default 0)
- `simulation_name_b` (str, default `'emode'`)

**Checked 2026-07-15:** the docs name these params `profile_a`/`profile_b`, but every script in this
repo (`AlN_Uviquity.py`, `example_LNOI.ipynb`, all `AlN_2D_3*` notebooks) consistently uses
`label_a`/`label_b` instead — that's a doc/version mismatch, not a bug in the scripts. Keep using
`label_a`/`label_b`; it's what the installed backend actually expects.

### mode_order
Mode correspondence between two mode lists by field similarity.
- `profile_a`, `profile_b` (str or int, default `''`)
- `raw_fields` (bool, default False)

### scattering
Scattering loss from a shape/mode via Volume Current Method. Stores
`scattering_vertical_edges`, `scattering_horizontal_edges`, `scattering_sum`, `edges`,
`scattering_all_edges` in shape metadata.
- `profile` (str, default `'_default'`)
- `shape` (str or list, default None) — None = all shapes
- `shapes` (str) — alias for `shape`
- `mode_list` (default `'all'`)

### plot
Interactive plot of fields/index/shapes, or save to file.
- `component` (`'Ex/y/z'`/`'Hx/y/z'`/`'Sx/y/z'`/`'Index'`/`'Shapes'`, default `'Ex'`)
- `plot_function` (`'real'`/`'imag'`/`'abs'`/`'abs^2'`/`'log'`, default `'real'`)
- `mode` (int, default 0)
- `aspect_ratio` (`'norm'`(0.707)/`'real'`/float, default `'norm'`)
- `index_outline` (bool, default True)
- `text_display` (bool, default True)
- `mesh_display` (bool, default False)
- `window_display` (bool, default False)
- `legend` (bool, default True)
- `port` (int or str, default 0) — EME input port
- `plane` (`'x-y'`/`'z-x'`/`'z-y'`, default `'z-x'`) — EME cross-section
- `slice_position` (float or None, default None)
- `forward_only` (bool, default False) — EME
- `resolution` (float or `'auto'`, default `'auto'`)
- `file_name` (str, default None) — if set, saves instead of opening an interactive window
- `file_type` (`'pdf'`/`'png'`, default `''`)

**This is the function that opens the native "EMode Plot" GUI window** — omit `file_name` and it
blocks waiting for that window; pass `file_name` to save headlessly instead in scripts/notebooks
where you don't want a blocking window.

### material_explorer
Interactive plot of refractive indices of all available materials (dashed = out-of-range
extrapolation).

### refractive_index / permeability / permittivity / d_matrix
Look up material properties from the database (or a custom value).
- `material` (str) — for AlGaAs, use composition syntax e.g. `"AlGaAs, 0.2"`
- `wavelength` (float [nm], default 1550)
- `reference` (bool, default False) — also return citation

### mesh
Generalized meshing for arbitrary shapes on a rectangular grid.
- `profile` (str, default `'_default'`)
- `run_mesh` (bool, default True)
- `verbose` (bool, default True) — progress bar

---

## EME (Eigenmode Expansion) — EMode3D
Source: https://docs.emodephotonix.com/emodeguide/eme.html

### EME_settings
Global EME defaults, inherited by sections created afterward (existing sections unaffected).
- `apply_scattering` (bool or list[float], default False)
- `beta_interpolation` (`'uniform'`/`'linear'`, default `'uniform'`)
- `junction_normalization` (bool/str/dict, default `'gain'`)
- `overlap_variation` (float, default 0.01) — mode-list overlap threshold for auto z-slicing
- `minimum_z_step` (float [nm], default 0.1)

### straight_section
- `name` (str, optional, auto-generated)
- `profile` (str, required)
- `length` (float [nm], required)
- `offset` (float or (x,y), default `(0,0)`)
- `settings` (dict or None, default None)

### taper_section
Linearly interpolates cross-section between two profiles, auto z-slicing to track mode evolution.
- `name` (str, optional)
- `profile`, `profile_end` (str, required)
- `length` (float [nm], required)
- `settings` (dict or None, default None) — notably `overlap_variation`, `minimum_z_step`

### gds_section
- `name` (str, optional)
- `profile` (str, required) — base cross-section outside GDS mask
- `gds_path` (str, required)
- `layer_map` (dict[str,int], required)
- `length` (float, optional — derived from GDS bbox if omitted)
- `cell_index` (int or str, default 0)
- `scale` (float, default 1)
- `port_poses` (dict, optional)
- `heal` (bool, default True)
- `grow` (float, default 1e-3)
- `settings` (dict or None, default None)

### copy_section
Reuses a pre-computed S-matrix (avoids redundant solving).
- `name` (str, optional)
- `section_name` (str, required)
- `mirror` (bool, default False) — swap left/right ports
- `port_swap` (dict, optional)
- `settings` (dict or None, default None)

### EME
Core solver — computes the full S-matrix across all declared sections.
- `warm_start` (bool, default False) — seed taper/gds refinement from prior solution

### plot_S_matrix
- `input` (int or str, default 0)
- `output` (int or str, default 1)
- `plot_function` (`'abs^2'`/`'angle'`/`'real'`/`'imag'`, default `'abs^2'`)
- `file_name` (str, optional) — saves to `EM_figures/`; interactive if omitted
- `file_type` (`'pdf'`/`'png'`, default `''`)

---

## Multi-Physics (FEM) — EMode3D, requires 3D license
Source: https://docs.emodephotonix.com/emodeguide/fem.html

### heat  (beta)
Steady-state thermal simulation across a waveguide cross-section.
- `min_angle` (float, default 30) — triangular mesh granularity; lower = denser but may not converge
- `boundary_temperature` (float [K], default 298)
- `boundaries` (list[str], default `['bottom']`) — any of `'top'/'bottom'/'left'/'right'`
- `verbose` (bool, default True)
→ returns dict: `p` (mesh points), `t` (mesh triangles), `temperature`, `thermal_conductivity`,
`heat_generation`, plus `boundary_temperature`/`boundaries` echoed back

Related shape params: `heat_only` (bool, default False), `fem_resolution` (float [nm], default 500).
Related material params: `thermal_conductivity` [W/m·K], `resistivity` [Ohm·nm], `dn_dT` [1/K].

### electrostatic  (beta)
Steady-state electrostatic simulation across a waveguide cross-section.
- `min_angle` (float, default 30)
- `verbose` (bool, default True)
→ returns dict: `p`, `t`, `voltage`, `eps_dc_grid`

Related shape param: `voltage` (float [V], default None). Related material param: `eps_r_dc`.

---

## Verified against this repo (2026-07-15)
- `add_material`'s `refractive_index_equation` **does accept Python-style `**` for power** — tested
  directly with the repo's AlN Sellmeier equations (`eq_o`/`eq_e` from `AlN_2D_3_overlap.ipynb` etc.);
  returned `refractive_index(material='custom_AlN', wavelength=450)` = `[2.111, 2.186, 2.111]`, no
  parser errors. No need to switch to `^`.
- `overlap()`'s real working parameter names are `label_a`/`label_b` (not `profile_a`/`profile_b` as
  the docs state) — confirmed by consistent usage across every script in this repo.
