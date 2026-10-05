# Survey run `loaded_smoke`

1 geometries (1 ok, 0 failed), 317 guided phase-match crossings (1 refined).

NCE = normalized conversion efficiency [%/W/cm^2], lossless; peak = loss-limited eta*L_eff^2 [%/W] at L_opt (scattering: EMode-native roughness; absorption: interface mechanisms + confinement-weighted bulk material loss, e.g. a lossy strip -- see geometry.py's lossy_mask/lossy_bulk_loss_dB_per_m and survey.bulk_absorption_loss; 0 wherever a geometry has no lossy region defined). overlap_shape is 0..1; A_shg is the plane-wave-equivalent interaction area for AlN d33.

**Window/box-mode filter**: 313 crossing(s) with an edge ratio > 0.02 excluded from every table below -- the SH field hasn't decayed by the simulation window's edge, meaning it's at least partly an artifact of the window's hard walls rather than real lateral confinement (see `shg_physics.lateral_edge_ratio`). Checked at full-refined resolution (`sh_edge_ratio`) where refined, at screening resolution (`sh_edge_ratio_screen`, same field `eta_screen` itself used) otherwise; `survey.py` also now skips window-limited crossings when choosing what to refine, so new runs shouldn't need the refined check to catch many. Full data, flag included, stays in `crossings.csv`.

## Top 25 by NCE

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM04 | 0.01 | 230.99 | 0.0448 | 0.0030 | 7.46e+04 | 0.495 | 0.197 | 0.00635 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM04 | 0.01 | 230.76 | 0.00259 | 0.0008 | 1.28e+06 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TE10 | TM04? | 0.00 | 232.92 | 0.000751 | 0.0207 | 4.7e+06 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TE10 | TE14? | 0.96 | 229.70 | 9.47e-06 | 0.0023 | 3.81e+08 | nan | nan | nan | screened |

## Top 25 by loss-limited peak efficiency (refined)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | sh_edge_ratio | pump_scattering_dB_per_m | sh_scattering_dB_per_m | pump_absorption_dB_per_m | sh_absorption_dB_per_m | L_opt_mm | peak_efficiency_pct_per_W |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM04 | 0.01 | 230.99 | 0.0448 | 0.00635 | 3 | 120 | 1.31e+04 | 4.51e+07 | 0.00 | 1.64e-11 |

## Best TM->TM pairs (best instance of each pump->SH pair)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM04 | 0.01 | 230.99 | 0.0448 | 0.0030 | 7.46e+04 | 0.495 | 0.197 | 0.00635 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM04 | 0.01 | 230.76 | 0.00259 | 0.0008 | 1.28e+06 | nan | nan | nan | screened |

## Best crossing per geometry

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM04 | 0.01 | 230.99 | 0.0448 | 0.0030 | 7.46e+04 | 0.495 | 0.197 | 0.00635 | refined |
