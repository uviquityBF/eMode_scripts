# Survey run `hybrid_sweep1`

24 geometries (24 ok, 0 failed), 10897 guided phase-match crossings (192 refined).

NCE = normalized conversion efficiency [%/W/cm^2], lossless; peak = loss-limited eta*L_eff^2 [%/W] at L_opt (scattering: EMode-native roughness; absorption: interface mechanisms + confinement-weighted bulk material loss, e.g. a lossy strip -- see geometry.py's lossy_mask/lossy_bulk_loss_dB_per_m and survey.bulk_absorption_loss; 0 wherever a geometry has no lossy region defined). overlap_shape is 0..1; A_shg is the plane-wave-equivalent interaction area for AlN d33.

**Window/box-mode filter**: 0 crossing(s) with an edge ratio > 0.02 excluded from every table below -- the SH field hasn't decayed by the simulation window's edge, meaning it's at least partly an artifact of the window's hard walls rather than real lateral confinement (see `shg_physics.lateral_edge_ratio`). Checked at full-refined resolution (`sh_edge_ratio`) where refined, at screening resolution (`sh_edge_ratio_screen`, same field `eta_screen` itself used) otherwise; `survey.py` also now skips window-limited crossings when choosing what to refine, so new runs shouldn't need the refined check to catch many. Full data, flag included, stays in `crossings.csv`.

## Top 25 by NCE

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM80 | 0.01 | 231.59 | 115 | 0.5175 | 32.1 | 0.226 | 0.219 | 1.32e-19 | refined |
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM100 | 0.04 | 220.17 | 77.3 | 0.4054 | 51.6 | 0.210 | 0.247 | 5.37e-20 | refined |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM100 | 0.02 | 233.63 | 61.2 | 0.5478 | 58.8 | 0.275 | 0.305 | 2.62e-19 | refined |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM120 | 0.02 | 223.60 | 51.3 | 0.4504 | 75.3 | 0.257 | 0.305 | 3.51e-20 | refined |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM81 | 0.02 | 228.54 | 48.9 | 0.1867 | 73.2 | 0.162 | 0.242 | 1e-20 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM10 | TM102? | 0.06 | 221.99 | 38.8 | 0.1978 | 109 | 0.274 | 0.262 | 4.53e-17 | refined |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM10 | TM101 | 0.08 | 221.18 | 38.5 | 0.0954 | 106 | 0.218 | 0.244 | 5.51e-19 | refined |
| hybrid h=400 w=600 custom sin_w=900 sin_h=700 | TM10 | TM102? | 0.03 | 234.36 | 36.7 | 0.1147 | 97 | 0.262 | 0.282 | 1.12e-20 | refined |
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM103 | 0.04 | 217.32 | 36.5 | 0.2667 | 112 | 0.205 | 0.287 | 5.55e-20 | refined |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM101 | 0.04 | 218.54 | 36.1 | 0.1391 | 107 | 0.151 | 0.254 | 9.68e-22 | refined |
| hybrid h=400 w=500 custom sin_w=900 sin_h=700 | TM10 | TM121? | 0.04 | 226.28 | 34.6 | 0.1245 | 112 | 0.286 | 0.260 | 3.06e-18 | refined |
| hybrid h=400 w=300 custom sin_w=900 sin_h=700 | TM00 | TM102 | 0.16 | 228.48 | 34.3 | 0.1634 | 104 | 0.175 | 0.400 | 1.45e-20 | refined |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM140 | 0.00 | 217.01 | 34.1 | 0.3587 | 119 | 0.244 | 0.314 | 9.23e-21 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM00 | TM80 | 0.07 | 230.12 | 33.9 | 0.0737 | 101 | 0.160 | 0.185 | 3.05e-21 | refined |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM10 | TM102 | 0.35 | 219.82 | 33.1 | 0.0982 | 125 | 0.216 | 0.349 | 2.16e-18 | refined |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM82 | 0.12 | 226.81 | 31.1 | 0.1235 | 117 | 0.160 | 0.288 | 7.4e-21 | refined |
| hybrid h=400 w=200 custom sin_w=1100 sin_h=700 | TM00 | TM140 | 0.24 | 226.20 | 29.5 | 0.4115 | 128 | 0.298 | 0.470 | 1.82e-19 | refined |
| hybrid h=400 w=300 custom sin_w=900 sin_h=700 | TM00 | TM121 | 0.01 | 221.65 | 28.5 | 0.1578 | 132 | 0.166 | 0.306 | 2.21e-21 | refined |
| hybrid h=400 w=300 custom sin_w=1100 sin_h=700 | TM00 | TM122 | 0.23 | 229.91 | 27.9 | 0.1606 | 127 | 0.185 | 0.475 | 5.5e-20 | refined |
| hybrid h=400 w=400 custom sin_w=900 sin_h=700 | TM00 | TM100 | 0.03 | 231.71 | 27.8 | 0.0801 | 121 | 0.169 | 0.236 | 5.61e-22 | refined |
| hybrid h=400 w=200 custom sin_w=1100 sin_h=700 | TM00 | TM160 | 0.03 | 219.84 | 26.6 | 0.3939 | 149 | 0.282 | 0.398 | 2.65e-20 | refined |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM01 | TM09? | 0.02 | 227.57 | 26.1 | 0.1093 | 152 | 0.279 | 0.278 | 2.67e-18 | refined |
| hybrid h=400 w=300 custom sin_w=900 sin_h=700 | TM00 | TM101 | 0.01 | 230.50 | 25.9 | 0.1701 | 136 | 0.178 | 0.305 | 1.54e-20 | refined |
| hybrid h=400 w=200 custom sin_w=1300 sin_h=700 | TM00 | TM160 | 0.01 | 228.16 | 25.4 | 0.5211 | 147 | 0.333 | 0.429 | 2.79e-19 | refined |
| hybrid h=400 w=300 custom sin_w=1300 sin_h=700 | TM00 | TM162 | 0.12 | 224.36 | 25.2 | 0.1598 | 146 | 0.179 | 0.503 | 2.17e-20 | refined |

## Top 25 by loss-limited peak efficiency (refined)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | sh_edge_ratio | pump_scattering_dB_per_m | sh_scattering_dB_per_m | pump_absorption_dB_per_m | sh_absorption_dB_per_m | L_opt_mm | peak_efficiency_pct_per_W |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM80 | 0.01 | 231.59 | 115 | 1.32e-19 | 700 | 26451 | 1.68e+03 | 1.53e+07 | 0.01 | 3.64e-07 |
| hybrid h=400 w=600 custom sin_w=900 sin_h=700 | TM10 | TM102? | 0.03 | 234.36 | 36.7 | 1.12e-20 | 541 | 14818 | 1.09e+03 | 1.05e+07 | 0.01 | 2.5e-07 |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM100 | 0.02 | 233.63 | 61.2 | 2.62e-19 | 549 | 18975 | 1.55e+03 | 1.43e+07 | 0.01 | 2.21e-07 |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM00 | TM80 | 0.07 | 230.12 | 33.9 | 3.05e-21 | 408 | 23892 | 1.05e+03 | 1.18e+07 | 0.01 | 1.82e-07 |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM01 | TM09? | 0.02 | 227.57 | 26.1 | 2.67e-18 | 243 | 4169 | 2.06e+03 | 1.09e+07 | 0.01 | 1.65e-07 |
| hybrid h=400 w=600 custom sin_w=900 sin_h=700 | TM01 | TM09? | 0.02 | 227.21 | 21.9 | 8.91e-19 | 146 | 3476 | 2.05e+03 | 1.08e+07 | 0.01 | 1.4e-07 |
| hybrid h=400 w=400 custom sin_w=900 sin_h=700 | TM00 | TM100 | 0.03 | 231.71 | 27.8 | 5.61e-22 | 372 | 17569 | 1.04e+03 | 1.25e+07 | 0.01 | 1.33e-07 |
| hybrid h=400 w=500 custom sin_w=900 sin_h=700 | TM10 | TM121? | 0.04 | 226.28 | 34.6 | 3.06e-18 | 703 | 27213 | 1.67e+03 | 1.45e+07 | 0.01 | 1.22e-07 |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM81 | 0.02 | 228.54 | 48.9 | 1e-20 | 660 | 23474 | 1.44e+03 | 1.75e+07 | 0.01 | 1.19e-07 |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM10 | TM82 | 0.09 | 233.14 | 23 | 6.07e-16 | 1014 | 23319 | 1.51e+03 | 1.28e+07 | 0.01 | 1.04e-07 |
| hybrid h=400 w=500 custom sin_w=900 sin_h=700 | TM01 | TM09? | 0.02 | 227.38 | 17 | 4.59e-18 | 187 | 3612 | 2.09e+03 | 1.11e+07 | 0.01 | 1.03e-07 |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM10 | TM101 | 0.08 | 221.18 | 38.5 | 5.51e-19 | 1009 | 42916 | 1.79e+03 | 1.67e+07 | 0.01 | 1.02e-07 |
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM100 | 0.04 | 220.17 | 77.3 | 5.37e-20 | 828 | 40853 | 2.72e+03 | 2.5e+07 | 0.01 | 9.17e-08 |
| hybrid h=400 w=600 custom sin_w=900 sin_h=700 | TM10 | TM120? | 0.27 | 225.70 | 22.6 | 8.43e-20 | 575 | 27075 | 1.35e+03 | 1.4e+07 | 0.01 | 8.66e-08 |
| hybrid h=400 w=300 custom sin_w=900 sin_h=700 | TM00 | TM102 | 0.16 | 228.48 | 34.3 | 1.45e-20 | 605 | 17598 | 1.47e+03 | 1.77e+07 | 0.01 | 8.12e-08 |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM10 | TM100? | 0.05 | 223.57 | 24.5 | 1.47e-16 | 1114 | 43819 | 2.17e+03 | 1.51e+07 | 0.01 | 7.95e-08 |
| hybrid h=400 w=400 custom sin_w=1100 sin_h=700 | TM00 | TM120 | 0.05 | 232.76 | 17.4 | 4.7e-21 | 359 | 12059 | 1.02e+03 | 1.29e+07 | 0.01 | 7.79e-08 |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM10 | TM102? | 0.06 | 221.99 | 38.8 | 4.53e-17 | 1130 | 41803 | 2.32e+03 | 1.93e+07 | 0.01 | 7.74e-08 |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM120 | 0.02 | 223.60 | 51.3 | 3.51e-20 | 648 | 27749 | 2.37e+03 | 2.23e+07 | 0.01 | 7.66e-08 |
| hybrid h=400 w=300 custom sin_w=1100 sin_h=700 | TM00 | TM122 | 0.23 | 229.91 | 27.9 | 5.5e-20 | 572 | 14391 | 1.42e+03 | 1.68e+07 | 0.01 | 7.42e-08 |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM10 | TM83 | 0.12 | 229.08 | 17.7 | 1.73e-17 | 963 | 25970 | 1.4e+03 | 1.33e+07 | 0.01 | 7.41e-08 |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM101 | 0.03 | 232.18 | 24.5 | 4.98e-19 | 562 | 17523 | 1.64e+03 | 1.57e+07 | 0.01 | 7.36e-08 |
| hybrid h=400 w=400 custom sin_w=1500 sin_h=700 | TM00 | TM160 | 0.17 | 234.18 | 16.6 | 6.81e-21 | 350 | 10031 | 998 | 1.3e+07 | 0.01 | 7.3e-08 |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM82 | 0.12 | 226.81 | 31.1 | 7.4e-21 | 674 | 21791 | 1.52e+03 | 1.81e+07 | 0.01 | 7.1e-08 |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM10 | TM81 | 0.03 | 234.75 | 7.27 | 2.79e-17 | 933 | 27528 | 1.2e+03 | 8.73e+06 | 0.01 | 7.08e-08 |

## Best TM->TM pairs (best instance of each pump->SH pair)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM80 | 0.01 | 231.59 | 115 | 0.5175 | 32.1 | 0.226 | 0.219 | 1.32e-19 | refined |
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM100 | 0.04 | 220.17 | 77.3 | 0.4054 | 51.6 | 0.210 | 0.247 | 5.37e-20 | refined |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM120 | 0.02 | 223.60 | 51.3 | 0.4504 | 75.3 | 0.257 | 0.305 | 3.51e-20 | refined |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM81 | 0.02 | 228.54 | 48.9 | 0.1867 | 73.2 | 0.162 | 0.242 | 1e-20 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM10 | TM102? | 0.06 | 221.99 | 38.8 | 0.1978 | 109 | 0.274 | 0.262 | 4.53e-17 | refined |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM10 | TM101 | 0.08 | 221.18 | 38.5 | 0.0954 | 106 | 0.218 | 0.244 | 5.51e-19 | refined |
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM103 | 0.04 | 217.32 | 36.5 | 0.2667 | 112 | 0.205 | 0.287 | 5.55e-20 | refined |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM101 | 0.04 | 218.54 | 36.1 | 0.1391 | 107 | 0.151 | 0.254 | 9.68e-22 | refined |
| hybrid h=400 w=500 custom sin_w=900 sin_h=700 | TM10 | TM121? | 0.04 | 226.28 | 34.6 | 0.1245 | 112 | 0.286 | 0.260 | 3.06e-18 | refined |
| hybrid h=400 w=300 custom sin_w=900 sin_h=700 | TM00 | TM102 | 0.16 | 228.48 | 34.3 | 0.1634 | 104 | 0.175 | 0.400 | 1.45e-20 | refined |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM140 | 0.00 | 217.01 | 34.1 | 0.3587 | 119 | 0.244 | 0.314 | 9.23e-21 | refined |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM10 | TM102 | 0.35 | 219.82 | 33.1 | 0.0982 | 125 | 0.216 | 0.349 | 2.16e-18 | refined |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM82 | 0.12 | 226.81 | 31.1 | 0.1235 | 117 | 0.160 | 0.288 | 7.4e-21 | refined |
| hybrid h=400 w=300 custom sin_w=900 sin_h=700 | TM00 | TM121 | 0.01 | 221.65 | 28.5 | 0.1578 | 132 | 0.166 | 0.306 | 2.21e-21 | refined |
| hybrid h=400 w=300 custom sin_w=1100 sin_h=700 | TM00 | TM122 | 0.23 | 229.91 | 27.9 | 0.1606 | 127 | 0.185 | 0.475 | 5.5e-20 | refined |
| hybrid h=400 w=200 custom sin_w=1100 sin_h=700 | TM00 | TM160 | 0.03 | 219.84 | 26.6 | 0.3939 | 149 | 0.282 | 0.398 | 2.65e-20 | refined |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM01 | TM09? | 0.02 | 227.57 | 26.1 | 0.1093 | 152 | 0.279 | 0.278 | 2.67e-18 | refined |
| hybrid h=400 w=300 custom sin_w=1300 sin_h=700 | TM00 | TM162 | 0.12 | 224.36 | 25.2 | 0.1598 | 146 | 0.179 | 0.503 | 2.17e-20 | refined |
| hybrid h=400 w=500 custom sin_w=900 sin_h=700 | TM10 | TM142 | 0.07 | 216.41 | 25.1 | 0.1171 | 166 | 0.267 | 0.333 | 1.12e-19 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM10 | TM100? | 0.05 | 223.57 | 24.5 | 0.1273 | 172 | 0.277 | 0.184 | 1.47e-16 | refined |

## Best crossing per geometry

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid h=400 w=200 custom sin_w=1100 sin_h=700 | TM00 | TM140 | 0.24 | 226.20 | 29.5 | 0.4115 | 128 | 0.298 | 0.470 | 1.82e-19 | refined |
| hybrid h=400 w=200 custom sin_w=1300 sin_h=700 | TM00 | TM160 | 0.01 | 228.16 | 25.4 | 0.5211 | 147 | 0.333 | 0.429 | 2.79e-19 | refined |
| hybrid h=400 w=200 custom sin_w=1500 sin_h=700 | TM00 | TM180 | 0.01 | 229.76 | 20.9 | 0.5525 | 176 | 0.362 | 0.503 | 1.45e-19 | refined |
| hybrid h=400 w=200 custom sin_w=700 sin_h=700 | TM00 | TM80 | 0.01 | 231.59 | 115 | 0.5175 | 32.1 | 0.226 | 0.219 | 1.32e-19 | refined |
| hybrid h=400 w=200 custom sin_w=900 sin_h=700 | TM00 | TM100 | 0.02 | 233.63 | 61.2 | 0.5478 | 58.8 | 0.275 | 0.305 | 2.62e-19 | refined |
| hybrid h=400 w=300 custom sin_w=1100 sin_h=700 | TM00 | TM122 | 0.23 | 229.91 | 27.9 | 0.1606 | 127 | 0.185 | 0.475 | 5.5e-20 | refined |
| hybrid h=400 w=300 custom sin_w=1300 sin_h=700 | TM00 | TM162 | 0.12 | 224.36 | 25.2 | 0.1598 | 146 | 0.179 | 0.503 | 2.17e-20 | refined |
| hybrid h=400 w=300 custom sin_w=1500 sin_h=700 | TM00 | TM162 | 0.05 | 231.39 | 23.7 | 0.1869 | 147 | 0.193 | 0.542 | 4.18e-20 | refined |
| hybrid h=400 w=300 custom sin_w=700 sin_h=700 | TM00 | TM81 | 0.02 | 228.54 | 48.9 | 0.1867 | 73.2 | 0.162 | 0.242 | 1e-20 | refined |
| hybrid h=400 w=300 custom sin_w=900 sin_h=700 | TM00 | TM102 | 0.16 | 228.48 | 34.3 | 0.1634 | 104 | 0.175 | 0.400 | 1.45e-20 | refined |
| hybrid h=400 w=400 custom sin_w=1100 sin_h=700 | TM00 | TM120 | 0.05 | 232.76 | 17.4 | 0.0749 | 193 | 0.174 | 0.337 | 4.7e-21 | refined |
| hybrid h=400 w=400 custom sin_w=1300 sin_h=700 | TM00 | TM140 | 0.35 | 233.53 | 15.4 | 0.0837 | 216 | 0.176 | 0.563 | 6.11e-21 | refined |
| hybrid h=400 w=400 custom sin_w=1500 sin_h=700 | TM00 | TM160 | 0.17 | 234.18 | 16.6 | 0.0905 | 200 | 0.177 | 0.499 | 6.81e-21 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=700 | TM10 | TM102? | 0.06 | 221.99 | 38.8 | 0.1978 | 109 | 0.274 | 0.262 | 4.53e-17 | refined |
| hybrid h=400 w=400 custom sin_w=900 sin_h=700 | TM00 | TM100 | 0.03 | 231.71 | 27.8 | 0.0801 | 121 | 0.169 | 0.236 | 5.61e-22 | refined |
| hybrid h=400 w=500 custom sin_w=1100 sin_h=700 | TM10 | TM140 | 0.43 | 228.78 | 15.8 | 0.1183 | 240 | 0.358 | 0.486 | 1.85e-18 | refined |
| hybrid h=400 w=500 custom sin_w=1300 sin_h=700 | TM10 | TM203? | 0.08 | 216.90 | 10.2 | 0.1150 | 402 | 0.374 | 0.480 | 4.59e-19 | refined |
| hybrid h=400 w=500 custom sin_w=1500 sin_h=700 | TM10 | TM180 | 0.02 | 232.15 | 13.2 | 0.1725 | 278 | 0.507 | 0.403 | 2.23e-18 | refined |
| hybrid h=400 w=500 custom sin_w=700 sin_h=700 | TM10 | TM101 | 0.08 | 221.18 | 38.5 | 0.0954 | 106 | 0.218 | 0.244 | 5.51e-19 | refined |
| hybrid h=400 w=500 custom sin_w=900 sin_h=700 | TM10 | TM121? | 0.04 | 226.28 | 34.6 | 0.1245 | 112 | 0.286 | 0.260 | 3.06e-18 | refined |
| hybrid h=400 w=600 custom sin_w=1100 sin_h=700 | TM10 | TM160 | 0.03 | 220.58 | 16.3 | 0.0641 | 238 | 0.271 | 0.290 | 4.86e-21 | refined |
| hybrid h=400 w=600 custom sin_w=1300 sin_h=700 | TM10 | TM180 | 0.02 | 223.03 | 15.8 | 0.0769 | 242 | 0.298 | 0.331 | 4.31e-21 | refined |
| hybrid h=400 w=600 custom sin_w=1500 sin_h=700 | TM01? | TM29? | 0.03 | 227.01 | 9.61 | 0.0861 | 406 | 0.516 | 0.366 | 3.28e-19 | refined |
| hybrid h=400 w=600 custom sin_w=900 sin_h=700 | TM10 | TM102? | 0.03 | 234.36 | 36.7 | 0.1147 | 97 | 0.262 | 0.282 | 1.12e-20 | refined |
