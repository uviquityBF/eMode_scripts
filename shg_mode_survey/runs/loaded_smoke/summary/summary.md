# Survey run `loaded_smoke`

1 geometries (1 ok, 0 failed), 317 guided phase-match crossings (8 refined).

NCE = normalized conversion efficiency [%/W/cm^2], lossless; peak = loss-limited eta*L_eff^2 [%/W] at L_opt (scattering: EMode-native roughness; absorption: interface mechanisms + confinement-weighted bulk material loss, e.g. a lossy strip -- see geometry.py's lossy_mask/lossy_bulk_loss_dB_per_m and survey.bulk_absorption_loss; 0 wherever a geometry has no lossy region defined). overlap_shape is 0..1; A_shg is the plane-wave-equivalent interaction area for AlN d33.

**Window/box-mode filter**: 8 refined crossing(s) with `sh_edge_ratio` > 0.02 excluded from every table below -- the SH field hasn't decayed by the simulation window's edge, meaning it's at least partly an artifact of the window's hard walls rather than real lateral confinement (see `shg_physics.lateral_edge_ratio`). Full data, flag included, stays in `crossings.csv`. **309 screened-only crossing(s) have no field export and so could not be checked** -- they pass through unflagged, not verified clean; re-run with a higher `refine_top_n` (or refine them individually) before trusting a screened-only entry in these tables.

## Top 25 by NCE

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM301 | 0.03 | 224.91 | 0.683 | 0.0069 | 4.79e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM262? | 0.11 | 218.17 | 0.621 | 0.0063 | 5.5e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM163 | 0.05 | 229.10 | 0.443 | 0.0059 | 7.19e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM262 | 0.04 | 224.50 | 0.422 | 0.0055 | 7.78e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM64? | 0.00 | 226.72 | 0.422 | 0.0093 | 8.09e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM45? | 0.04 | 226.63 | 0.42 | 0.0087 | 8.21e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM205? | 0.04 | 226.44 | 0.413 | 0.0095 | 8.27e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM184? | 0.05 | 228.80 | 0.391 | 0.0094 | 8.61e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM124? | 0.48 | 222.30 | 0.33 | 0.0079 | 1.06e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM242 | 0.03 | 228.65 | 0.318 | 0.0049 | 1e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM144 | 0.37 | 217.23 | 0.294 | 0.0044 | 1.17e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM144 | 0.12 | 219.85 | 0.261 | 0.0070 | 1.37e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM143 | 0.03 | 234.48 | 0.258 | 0.0074 | 1.25e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM184? | 0.10 | 215.62 | 0.247 | 0.0065 | 1.5e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM44? | 0.02 | 226.14 | 0.192 | 0.0063 | 1.79e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM341 | 0.03 | 218.23 | 0.188 | 0.0035 | 1.81e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM84? | 0.01 | 222.16 | 0.173 | 0.0034 | 1.93e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TE134? | 1.00 | 216.02 | 0.166 | 0.0032 | 2.08e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM282? | 0.06 | 222.20 | 0.149 | 0.0032 | 2.23e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM143 | 0.03 | 231.43 | 0.145 | 0.0034 | 2.16e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM104? | 0.05 | 221.79 | 0.144 | 0.0048 | 2.48e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TE301? | 0.51 | 226.40 | 0.136 | 0.0032 | 2.38e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM184 | 0.06 | 215.39 | 0.133 | 0.0029 | 2.62e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TE192? | 0.67 | 227.51 | 0.111 | 0.0043 | 3.07e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM163 | 0.04 | 231.79 | 0.1 | 0.0045 | 3.28e+04 | nan | nan | nan | screened |

## Top 25 by loss-limited peak efficiency (refined)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | sh_edge_ratio | pump_scattering_dB_per_m | sh_scattering_dB_per_m | pump_absorption_dB_per_m | sh_absorption_dB_per_m | L_opt_mm | peak_efficiency_pct_per_W |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Best TM->TM pairs (best instance of each pump->SH pair)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM301 | 0.03 | 224.91 | 0.683 | 0.0069 | 4.79e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM262? | 0.11 | 218.17 | 0.621 | 0.0063 | 5.5e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM163 | 0.05 | 229.10 | 0.443 | 0.0059 | 7.19e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM262 | 0.04 | 224.50 | 0.422 | 0.0055 | 7.78e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM64? | 0.00 | 226.72 | 0.422 | 0.0093 | 8.09e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM45? | 0.04 | 226.63 | 0.42 | 0.0087 | 8.21e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM205? | 0.04 | 226.44 | 0.413 | 0.0095 | 8.27e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM184? | 0.05 | 228.80 | 0.391 | 0.0094 | 8.61e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM124? | 0.48 | 222.30 | 0.33 | 0.0079 | 1.06e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM242 | 0.03 | 228.65 | 0.318 | 0.0049 | 1e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM144 | 0.37 | 217.23 | 0.294 | 0.0044 | 1.17e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM144 | 0.12 | 219.85 | 0.261 | 0.0070 | 1.37e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM143 | 0.03 | 234.48 | 0.258 | 0.0074 | 1.25e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM10 | TM44? | 0.02 | 226.14 | 0.192 | 0.0063 | 1.79e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM341 | 0.03 | 218.23 | 0.188 | 0.0035 | 1.81e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM84? | 0.01 | 222.16 | 0.173 | 0.0034 | 1.93e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM282? | 0.06 | 222.20 | 0.149 | 0.0032 | 2.23e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM143 | 0.03 | 231.43 | 0.145 | 0.0034 | 2.16e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM104? | 0.05 | 221.79 | 0.144 | 0.0048 | 2.48e+04 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM184 | 0.06 | 215.39 | 0.133 | 0.0029 | 2.62e+04 | nan | nan | nan | screened |

## Best crossing per geometry

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM301 | 0.03 | 224.91 | 0.683 | 0.0069 | 4.79e+03 | nan | nan | nan | screened |
