# Survey run `loaded_sweep1`

16 geometries (16 ok, 0 failed), 4798 guided phase-match crossings (96 refined).

NCE = normalized conversion efficiency [%/W/cm^2], lossless; peak = loss-limited eta*L_eff^2 [%/W] at L_opt (scattering: EMode-native roughness; absorption: interface mechanisms + confinement-weighted bulk material loss, e.g. a lossy strip -- see geometry.py's lossy_mask/lossy_bulk_loss_dB_per_m and survey.bulk_absorption_loss; 0 wherever a geometry has no lossy region defined). overlap_shape is 0..1; A_shg is the plane-wave-equivalent interaction area for AlN d33.

**Window/box-mode filter**: 2421 crossing(s) with an edge ratio > 0.02 excluded from every table below -- the SH field hasn't decayed by the simulation window's edge, meaning it's at least partly an artifact of the window's hard walls rather than real lateral confinement (see `shg_physics.lateral_edge_ratio`). Checked at full-refined resolution (`sh_edge_ratio`) where refined, at screening resolution (`sh_edge_ratio_screen`, same field `eta_screen` itself used) otherwise; `survey.py` also now skips window-limited crossings when choosing what to refine, so new runs shouldn't need the refined check to catch many. Full data, flag included, stays in `crossings.csv`. **2335 crossing(s) predate this check (no `sh_edge_ratio_screen`) and could not be verified either way** -- they pass through unflagged, not verified clean; re-run `survey.py` to refresh.

## Top 25 by NCE

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM05? | 0.01 | 225.44 | 159 | 0.3268 | 16.3 | 0.173 | 0.373 | 0.0159 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.2347 | 16.3 | 0.188 | 0.661 | 0.000517 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.2347 | 16.3 | 0.188 | 0.661 | 0.000517 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM03 | 0.00 | 229.74 | 152 | 0.2833 | 16.8 | 0.181 | 0.308 | 0.0037 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM03 | 0.00 | 229.74 | 152 | 0.2833 | 16.8 | 0.181 | 0.308 | 0.0037 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM03 | 0.00 | 231.29 | 150 | 0.2615 | 17.6 | 0.188 | 0.316 | 0.00193 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM03 | 0.00 | 231.29 | 150 | 0.2615 | 17.6 | 0.188 | 0.316 | 0.00193 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM04 | 0.00 | 227.83 | 136 | 0.3132 | 18.9 | 0.178 | 0.335 | 0.00735 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM86 | 0.00 | 221.19 | 59 | 0.0877 | 57.5 | 0.322 | 0.366 | 0.0197 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM09? | 0.05 | 225.20 | 53.1 | 0.1068 | 57.5 | 0.108 | 0.326 | 0.00806 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM05? | 0.06 | 225.11 | 39.8 | 0.0718 | 80.6 | 0.296 | 0.379 | 0.0143 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM05? | 0.01 | 225.74 | 28.5 | 0.0646 | 115 | 0.343 | 0.391 | 0.0129 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM05? | 0.01 | 225.74 | 28.5 | 0.0646 | 115 | 0.343 | 0.391 | 0.0129 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM83 | 0.02 | 222.92 | 21.8 | 0.0755 | 123 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM128? | 0.01 | 215.98 | 21.1 | 0.0469 | 161 | 0.265 | 0.317 | 0.0122 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM126 | 0.07 | 225.16 | 17.1 | 0.0684 | 178 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM221? | 0.01 | 230.71 | 13 | 0.0546 | 201 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM126? | 0.38 | 225.59 | 10.2 | 0.0437 | 298 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM302? | 0.04 | 225.21 | 10.1 | 0.0339 | 318 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM20 | TM63 | 0.01 | 233.72 | 9.98 | 0.0605 | 281 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM146 | 0.03 | 222.88 | 9.42 | 0.0412 | 325 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM202 | 0.03 | 234.29 | 8.98 | 0.0392 | 332 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM87? | 0.01 | 226.79 | 7.92 | 0.0638 | 326 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM20 | TM242 | 0.03 | 229.61 | 7.25 | 0.0536 | 391 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM00 | TM46 | 0.06 | 222.13 | 7.21 | 0.0419 | 374 | nan | nan | nan | screened |

## Top 25 by loss-limited peak efficiency (refined)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | sh_edge_ratio | pump_scattering_dB_per_m | sh_scattering_dB_per_m | pump_absorption_dB_per_m | sh_absorption_dB_per_m | L_opt_mm | peak_efficiency_pct_per_W |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.000517 | 98 | 4 | 1.11e+06 | 2.93e+06 | 0.00 | 8.54e-07 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.000517 | 98 | 4 | 1.11e+06 | 2.93e+06 | 0.00 | 8.54e-07 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM03 | 0.00 | 231.29 | 150 | 0.00193 | 254 | 22 | 1.23e+06 | 2.12e+07 | 0.00 | 1.43e-07 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM03 | 0.00 | 231.29 | 150 | 0.00193 | 254 | 22 | 1.23e+06 | 2.12e+07 | 0.00 | 1.43e-07 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM03 | 0.00 | 229.74 | 152 | 0.0037 | 104 | 29 | 1.32e+06 | 4.86e+07 | 0.00 | 2.93e-08 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM03 | 0.00 | 229.74 | 152 | 0.0037 | 104 | 29 | 1.32e+06 | 4.86e+07 | 0.00 | 2.93e-08 |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM86 | 0.00 | 221.19 | 59 | 0.0197 | 146 | 2581 | 3.52e+05 | 3.75e+07 | 0.00 | 2.72e-08 |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM128? | 0.01 | 215.98 | 21.1 | 0.0122 | 109 | 20086 | 5.76e+05 | 2.25e+07 | 0.00 | 2.24e-08 |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM05? | 0.06 | 225.11 | 39.8 | 0.0143 | 79 | 613 | 3.26e+05 | 4.42e+07 | 0.00 | 1.35e-08 |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM05? | 0.01 | 225.74 | 28.5 | 0.0129 | 126 | 597 | 2.64e+05 | 4.48e+07 | 0.00 | 9.62e-09 |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM05? | 0.01 | 225.74 | 28.5 | 0.0129 | 126 | 597 | 2.64e+05 | 4.48e+07 | 0.00 | 9.62e-09 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM05? | 0.01 | 225.44 | 159 | 0.0159 | 110 | 603 | 1.57e+06 | 8.66e+07 | 0.00 | 8.34e-09 |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM09? | 0.05 | 225.20 | 53.1 | 0.00806 | 1424 | 924 | 1.36e+06 | 5.92e+07 | 0.00 | 6.68e-09 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TM26 | 0.02 | 230.43 | 4.01 | 0.00569 | 521 | 281 | 1.2e+06 | 1.84e+07 | 0.00 | 4.81e-09 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM04 | 0.00 | 227.83 | 136 | 0.00735 | 107 | 104 | 1.43e+06 | 1.14e+08 | 0.00 | 4.29e-09 |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM84? | 0.00 | 229.38 | 6.08 | 0.0197 | 68 | 50 | 2.58e+05 | 7.31e+07 | 0.00 | 7.72e-10 |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TE10 | TM06 | 0.00 | 234.74 | 0.0448 | 0.00393 | 3436 | 0 | 1.17e+06 | 1.43e+06 | 0.01 | 5.14e-10 |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TE00 | TM05 | 0.00 | 231.83 | 0.0416 | 0.00244 | 779 | 43 | 1.37e+06 | 4.92e+06 | 0.00 | 1.73e-10 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TE10 | TM05 | 0.00 | 232.27 | 0.0249 | 0.000869 | 436 | 10 | 1.36e+06 | 4.97e+06 | 0.00 | 1.03e-10 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM20 | TM26? | 0.00 | 224.39 | 1.76 | 0.00451 | 533 | 656 | 1.59e+06 | 9.03e+07 | 0.00 | 8.4e-11 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM20 | TM26? | 0.00 | 224.39 | 1.76 | 0.00451 | 533 | 656 | 1.59e+06 | 9.03e+07 | 0.00 | 8.4e-11 |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM20 | TM04 | 0.00 | 230.90 | 0.256 | 0.00643 | 67 | 32 | 6.37e+04 | 4.93e+07 | 0.00 | 7.7e-11 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TE15 | 1.00 | 230.99 | 0.0117 | 0.00693 | 520 | 98 | 1.17e+06 | 9.96e+06 | 0.00 | 3.02e-11 |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TE10 | TM05? | 0.00 | 225.59 | 0.0757 | 0.0156 | 365 | 537 | 9.66e+05 | 4.48e+07 | 0.00 | 1.96e-11 |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM04 | 0.01 | 230.99 | 0.0448 | 0.00635 | 3 | 120 | 1.31e+04 | 4.51e+07 | 0.00 | 1.64e-11 |

## Best TM->TM pairs (best instance of each pump->SH pair)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM05? | 0.01 | 225.44 | 159 | 0.3268 | 16.3 | 0.173 | 0.373 | 0.0159 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.2347 | 16.3 | 0.188 | 0.661 | 0.000517 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM03 | 0.00 | 229.74 | 152 | 0.2833 | 16.8 | 0.181 | 0.308 | 0.0037 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM03 | 0.00 | 231.29 | 150 | 0.2615 | 17.6 | 0.188 | 0.316 | 0.00193 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM04 | 0.00 | 227.83 | 136 | 0.3132 | 18.9 | 0.178 | 0.335 | 0.00735 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM86 | 0.00 | 221.19 | 59 | 0.0877 | 57.5 | 0.322 | 0.366 | 0.0197 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM09? | 0.05 | 225.20 | 53.1 | 0.1068 | 57.5 | 0.108 | 0.326 | 0.00806 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM05? | 0.01 | 225.74 | 28.5 | 0.0646 | 115 | 0.343 | 0.391 | 0.0129 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM83 | 0.02 | 222.92 | 21.8 | 0.0755 | 123 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM128? | 0.01 | 215.98 | 21.1 | 0.0469 | 161 | 0.265 | 0.317 | 0.0122 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM126 | 0.07 | 225.16 | 17.1 | 0.0684 | 178 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM221? | 0.01 | 230.71 | 13 | 0.0546 | 201 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM126? | 0.38 | 225.59 | 10.2 | 0.0437 | 298 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM302? | 0.04 | 225.21 | 10.1 | 0.0339 | 318 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM20 | TM63 | 0.01 | 233.72 | 9.98 | 0.0605 | 281 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM146 | 0.03 | 222.88 | 9.42 | 0.0412 | 325 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM202 | 0.03 | 234.29 | 8.98 | 0.0392 | 332 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM87? | 0.01 | 226.79 | 7.92 | 0.0638 | 326 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM20 | TM242 | 0.03 | 229.61 | 7.25 | 0.0536 | 391 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM00 | TM46 | 0.06 | 222.13 | 7.21 | 0.0419 | 374 | nan | nan | nan | screened |

## Best crossing per geometry

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM05? | 0.01 | 225.44 | 159 | 0.3268 | 16.3 | 0.173 | 0.373 | 0.0159 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM03 | 0.00 | 229.74 | 152 | 0.2833 | 16.8 | 0.181 | 0.308 | 0.0037 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TE10 | TM84 | 0.00 | 229.41 | 0.00648 | 0.1012 | 4.57e+05 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM83 | 0.02 | 222.92 | 21.8 | 0.0755 | 123 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM86 | 0.00 | 221.19 | 59 | 0.0877 | 57.5 | 0.322 | 0.366 | 0.0197 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM05? | 0.01 | 225.74 | 28.5 | 0.0646 | 115 | 0.343 | 0.391 | 0.0129 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM301 | 0.03 | 224.91 | 0.683 | 0.0069 | 4.79e+03 | nan | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM04 | 0.01 | 230.99 | 0.0448 | 0.0030 | 7.46e+04 | 0.495 | 0.197 | 0.00635 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.2347 | 16.3 | 0.188 | 0.661 | 0.000517 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.2347 | 16.3 | 0.188 | 0.661 | 0.000517 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM09? | 0.05 | 225.20 | 53.1 | 0.1068 | 57.5 | 0.108 | 0.326 | 0.00806 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TE10 | TM06 | 0.00 | 234.74 | 0.0448 | 0.1441 | 6.58e+04 | 0.092 | 0.975 | 0.00393 | refined |
| loaded t=600 e=0 custom h_s=70 w_s=1000 | TM10 | TM244? | 0.04 | 218.59 | 0.295 | 0.0087 | 1.15e+04 | nan | nan | nan | screened |
| loaded t=600 e=0 custom h_s=70 w_s=1000 | TM20 | TM67? | 0.00 | 229.61 | 0.000363 | 0.0003 | 8.69e+06 | 0.876 | 0.510 | 0.0162 | refined |
| loaded t=600 e=0 custom h_s=70 w_s=500 | TE00 | TM07? | 0.07 | 229.81 | 0.0292 | 0.0694 | 1.1e+05 | 0.100 | 0.345 | 0.0144 | refined |
| loaded t=600 e=0 custom h_s=70 w_s=500 | TM20 | TM86 | 0.01 | 233.44 | 0.0685 | 0.0042 | 4.51e+04 | nan | nan | nan | screened |
