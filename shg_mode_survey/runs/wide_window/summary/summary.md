# Survey run `wide_window`

4 geometries (4 ok, 0 failed), 246 guided phase-match crossings (48 refined).

NCE = normalized conversion efficiency [%/W/cm^2], lossless; peak = loss-limited eta*L_eff^2 [%/W] at L_opt (scattering: EMode-native roughness; absorption: interface mechanisms + confinement-weighted bulk material loss, e.g. a lossy strip -- see geometry.py's lossy_mask/lossy_bulk_loss_dB_per_m and survey.bulk_absorption_loss; 0 wherever a geometry has no lossy region defined). overlap_shape is 0..1; A_shg is the plane-wave-equivalent interaction area for AlN d33.

**Window/box-mode filter**: 0 crossing(s) with an edge ratio > 0.02 excluded from every table below -- the SH field hasn't decayed by the simulation window's edge, meaning it's at least partly an artifact of the window's hard walls rather than real lateral confinement (see `shg_physics.lateral_edge_ratio`). Checked at full-refined resolution (`sh_edge_ratio`) where refined, at screening resolution (`sh_edge_ratio_screen`, same field `eta_screen` itself used) otherwise; `survey.py` also now skips window-limited crossings when choosing what to refine, so new runs shouldn't need the refined check to catch many. Full data, flag included, stays in `crossings.csv`. **123 crossing(s) predate this check (no `sh_edge_ratio_screen`) and could not be verified either way** -- they pass through unflagged, not verified clean; re-run `survey.py` to refresh.

## Top 25 by NCE

| h | w | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 500 | TM10 | TM60 | 0.13 | 240.94 | 19.1 | 0.0269 | 216 | 0.133 | 0.090 | nan | refined |
| 300 | 500 | TM10 | TM60 | 0.13 | 240.94 | 19.1 | 0.0269 | 216 | 0.133 | 0.090 | 1.73e-09 | refined |
| 350 | 500 | TM10 | TM60 | 0.07 | 239.16 | 15.8 | 0.0249 | 255 | 0.138 | 0.091 | nan | refined |
| 350 | 500 | TM10 | TM60 | 0.07 | 239.16 | 15.8 | 0.0249 | 255 | 0.138 | 0.091 | 9.25e-10 | refined |
| 350 | 500 | TM00 | TM22 | 0.13 | 263.27 | 5.26 | 0.0172 | 541 | 0.140 | 0.121 | nan | refined |
| 350 | 500 | TM00 | TM22 | 0.13 | 263.27 | 5.26 | 0.0172 | 541 | 0.140 | 0.121 | 1.8e-11 | refined |
| 350 | 500 | TM00 | TM04 | 0.01 | 227.85 | 4.76 | 0.0140 | 748 | 0.124 | 0.138 | 2.74e-21 | refined |
| 350 | 500 | TM00 | TM04 | 0.01 | 227.85 | 4.76 | 0.0140 | 748 | 0.124 | 0.138 | nan | refined |
| 350 | 500 | TM10 | TM04 | 0.01 | 240.43 | 4.75 | 0.0152 | 841 | 0.139 | 0.153 | nan | refined |
| 350 | 500 | TM10 | TM04 | 0.01 | 240.43 | 4.75 | 0.0152 | 841 | 0.139 | 0.153 | 7.38e-10 | refined |
| 300 | 500 | TM00 | TM40 | 0.07 | 267.40 | 4.54 | 0.0158 | 636 | 0.137 | 0.091 | nan | refined |
| 300 | 500 | TM00 | TM40 | 0.07 | 267.40 | 4.54 | 0.0158 | 636 | 0.137 | 0.091 | 1.9e-12 | refined |
| 300 | 500 | TM10 | TM80 | 0.03 | 216.36 | 3.98 | 0.0107 | 1.17e+03 | 0.117 | 0.074 | nan | refined |
| 300 | 500 | TM10 | TM80 | 0.03 | 216.36 | 3.98 | 0.0107 | 1.17e+03 | 0.117 | 0.074 | 7.72e-11 | refined |
| 300 | 500 | TM00 | TM04 | 0.06 | 218.02 | 3.94 | 0.0118 | 997 | 0.112 | 0.126 | nan | refined |
| 300 | 500 | TM00 | TM04 | 0.06 | 218.02 | 3.94 | 0.0118 | 997 | 0.112 | 0.126 | 1.2e-19 | refined |
| 300 | 500 | TM10 | TM04 | 0.13 | 225.73 | 3.79 | 0.0123 | 1.17e+03 | 0.123 | 0.146 | 6.95e-10 | refined |
| 300 | 500 | TM10 | TM04 | 0.13 | 225.73 | 3.79 | 0.0123 | 1.17e+03 | 0.123 | 0.146 | nan | refined |
| 350 | 500 | TM10 | TM80 | 0.04 | 215.74 | 3.25 | 0.0100 | 1.4e+03 | 0.124 | 0.079 | 2.68e-11 | refined |
| 350 | 500 | TM10 | TM80 | 0.04 | 215.74 | 3.25 | 0.0100 | 1.4e+03 | 0.124 | 0.079 | nan | refined |
| 300 | 500 | TM00 | TM22 | 0.09 | 254.46 | 2.67 | 0.0116 | 1.17e+03 | 0.130 | 0.120 | nan | refined |
| 300 | 500 | TM00 | TM22 | 0.09 | 254.46 | 2.67 | 0.0116 | 1.17e+03 | 0.130 | 0.120 | 2.07e-10 | refined |
| 350 | 500 | TM10 | TM42 | 0.08 | 248.60 | 2.48 | 0.0105 | 1.55e+03 | 0.144 | 0.129 | nan | refined |
| 350 | 500 | TM10 | TM42 | 0.08 | 248.60 | 2.48 | 0.0105 | 1.55e+03 | 0.144 | 0.129 | 1.03e-10 | refined |
| 350 | 500 | TM10 | TM24 | 0.14 | 228.81 | 2.04 | 0.0087 | 2.07e+03 | 0.132 | 0.138 | nan | refined |

## Top 25 by loss-limited peak efficiency (refined)

| h | w | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | sh_edge_ratio | pump_scattering_dB_per_m | sh_scattering_dB_per_m | pump_absorption_dB_per_m | sh_absorption_dB_per_m | L_opt_mm | peak_efficiency_pct_per_W |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 350 | 500 | TM00 | TM04 | 0.01 | 227.85 | 4.76 | nan | 434 | 1181 | 1.15e+03 | 0 | 4.32 | 0.111 |
| 350 | 500 | TM00 | TM04 | 0.01 | 227.85 | 4.76 | 2.74e-21 | 434 | 1181 | 1.15e+03 | 0 | 4.32 | 0.111 |
| 350 | 500 | TM10 | TM04 | 0.01 | 240.43 | 4.75 | nan | 1892 | 1346 | 1.28e+03 | 0 | 2.69 | 0.0387 |
| 350 | 500 | TM10 | TM04 | 0.01 | 240.43 | 4.75 | 7.38e-10 | 1892 | 1346 | 1.28e+03 | 0 | 2.69 | 0.0387 |
| 300 | 500 | TM00 | TM04 | 0.06 | 218.02 | 3.94 | nan | 416 | 3151 | 1.55e+03 | 0 | 2.46 | 0.0322 |
| 300 | 500 | TM00 | TM04 | 0.06 | 218.02 | 3.94 | 1.2e-19 | 416 | 3151 | 1.55e+03 | 0 | 2.46 | 0.0322 |
| 350 | 500 | TM00 | TM22 | 0.13 | 263.27 | 5.26 | 1.8e-11 | 390 | 7116 | 1.25e+03 | 0 | 1.75 | 0.0208 |
| 350 | 500 | TM00 | TM22 | 0.13 | 263.27 | 5.26 | nan | 390 | 7116 | 1.25e+03 | 0 | 1.75 | 0.0208 |
| 300 | 500 | TM10 | TM04 | 0.13 | 225.73 | 3.79 | 6.95e-10 | 1823 | 4359 | 1.65e+03 | 0 | 1.56 | 0.0123 |
| 300 | 500 | TM10 | TM04 | 0.13 | 225.73 | 3.79 | nan | 1823 | 4359 | 1.65e+03 | 0 | 1.56 | 0.0123 |
| 300 | 500 | TM00 | TM22 | 0.09 | 254.46 | 2.67 | nan | 372 | 6370 | 1.67e+03 | 0 | 1.69 | 0.0101 |
| 300 | 500 | TM00 | TM22 | 0.09 | 254.46 | 2.67 | 2.07e-10 | 372 | 6370 | 1.67e+03 | 0 | 1.69 | 0.0101 |
| 300 | 500 | TM10 | TM03 | 0.01 | 259.06 | 0.704 | nan | 1632 | 1095 | 1.73e+03 | 0 | 2.80 | 0.00578 |
| 300 | 500 | TM10 | TM03 | 0.01 | 259.06 | 0.704 | 1.68e-08 | 1632 | 1095 | 1.73e+03 | 0 | 2.80 | 0.00578 |
| 300 | 500 | TM00 | TM40 | 0.07 | 267.40 | 4.54 | nan | 354 | 17098 | 1.71e+03 | 0 | 0.95 | 0.00475 |
| 300 | 500 | TM00 | TM40 | 0.07 | 267.40 | 4.54 | 1.9e-12 | 354 | 17098 | 1.71e+03 | 0 | 0.95 | 0.00475 |
| 350 | 500 | TM00 | TE12 | 0.74 | 264.54 | 1.45 | nan | 388 | 8409 | 1.25e+03 | 0 | 1.59 | 0.00464 |
| 350 | 500 | TM00 | TE12 | 0.74 | 264.54 | 1.45 | 2.18e-12 | 388 | 8409 | 1.25e+03 | 0 | 1.59 | 0.00464 |
| 300 | 500 | TM10 | TM60 | 0.13 | 240.94 | 19.1 | nan | 1746 | 43504 | 1.7e+03 | 0 | 0.44 | 0.0038 |
| 300 | 500 | TM10 | TM60 | 0.13 | 240.94 | 19.1 | 1.73e-09 | 1746 | 43504 | 1.7e+03 | 0 | 0.44 | 0.0038 |
| 350 | 500 | TM10 | TM60 | 0.07 | 239.16 | 15.8 | 9.25e-10 | 1899 | 44052 | 1.28e+03 | 0 | 0.45 | 0.00319 |
| 350 | 500 | TM10 | TM60 | 0.07 | 239.16 | 15.8 | nan | 1899 | 44052 | 1.28e+03 | 0 | 0.45 | 0.00319 |
| 350 | 500 | TM10 | TM24 | 0.14 | 228.81 | 2.04 | nan | 1952 | 10788 | 1.24e+03 | 0 | 1.03 | 0.00289 |
| 350 | 500 | TM10 | TM24 | 0.14 | 228.81 | 2.04 | 1.16e-09 | 1952 | 10788 | 1.24e+03 | 0 | 1.03 | 0.00289 |
| 300 | 500 | TM10 | TM24 | 0.13 | 218.89 | 1.67 | nan | 1852 | 9263 | 1.63e+03 | 0 | 1.08 | 0.0026 |

## Best TM->TM pairs (best instance of each pump->SH pair)

| h | w | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 500 | TM10 | TM60 | 0.13 | 240.94 | 19.1 | 0.0269 | 216 | 0.133 | 0.090 | nan | refined |
| 350 | 500 | TM00 | TM22 | 0.13 | 263.27 | 5.26 | 0.0172 | 541 | 0.140 | 0.121 | nan | refined |
| 350 | 500 | TM00 | TM04 | 0.01 | 227.85 | 4.76 | 0.0140 | 748 | 0.124 | 0.138 | 2.74e-21 | refined |
| 350 | 500 | TM10 | TM04 | 0.01 | 240.43 | 4.75 | 0.0152 | 841 | 0.139 | 0.153 | nan | refined |
| 300 | 500 | TM00 | TM40 | 0.07 | 267.40 | 4.54 | 0.0158 | 636 | 0.137 | 0.091 | nan | refined |
| 300 | 500 | TM10 | TM80 | 0.03 | 216.36 | 3.98 | 0.0107 | 1.17e+03 | 0.117 | 0.074 | nan | refined |
| 350 | 500 | TM10 | TM42 | 0.08 | 248.60 | 2.48 | 0.0105 | 1.55e+03 | 0.144 | 0.129 | nan | refined |
| 350 | 500 | TM10 | TM24 | 0.14 | 228.81 | 2.04 | 0.0087 | 2.07e+03 | 0.132 | 0.138 | nan | refined |
| 350 | 500 | TM10 | TM41 | 0.06 | 273.06 | 1.27 | 0.0085 | 2.72e+03 | 0.164 | 0.120 | nan | refined |
| 350 | 500 | TM00 | TM60 | 0.02 | 228.34 | 1.01 | 0.0062 | 3.51e+03 | 0.124 | 0.083 | nan | refined |
| 350 | 500 | TM10 | TM61 | 0.18 | 230.69 | 0.85 | 0.0055 | 4.94e+03 | 0.133 | 0.112 | nan | refined |
| 300 | 500 | TM10 | TM03 | 0.01 | 259.06 | 0.704 | 0.0071 | 5.41e+03 | 0.148 | 0.163 | nan | refined |
| 300 | 500 | TM10 | TM62 | 0.39 | 219.65 | 0.323 | 0.0031 | 1.42e+04 | nan | nan | nan | screened |
| 300 | 500 | TM10 | TM23 | 0.15 | 239.67 | 0.319 | 0.0037 | 1.3e+04 | nan | nan | nan | screened |
| 300 | 500 | TM00 | TM03 | 0.01 | 237.99 | 0.111 | 0.0022 | 3.09e+04 | nan | nan | nan | screened |
| 350 | 500 | TM00 | TM42 | 0.15 | 234.53 | 0.107 | 0.0021 | 3.19e+04 | nan | nan | nan | screened |
| 350 | 500 | TM00 | TM41? | 0.09 | 222.69 | 0.073 | 0.0016 | 5.06e+04 | nan | nan | nan | screened |
| 350 | 500 | TM00 | TM41 | 0.20 | 249.73 | 0.057 | 0.0016 | 5.43e+04 | nan | nan | nan | screened |
| 350 | 500 | TM00 | TM24 | 0.26 | 220.81 | 0.0522 | 0.0014 | 7.16e+04 | nan | nan | nan | screened |
| 350 | 500 | TM10 | TM05 | 0.02 | 220.21 | 0.0171 | 0.0008 | 2.59e+05 | nan | nan | nan | screened |

## Best crossing per geometry

| h | w | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 500 | TM10 | TM60 | 0.13 | 240.94 | 19.1 | 0.0269 | 216 | 0.133 | 0.090 | 1.73e-09 | refined |
| 300 | 500 | TM10 | TM60 | 0.13 | 240.94 | 19.1 | 0.0269 | 216 | 0.133 | 0.090 | nan | refined |
| 350 | 500 | TM10 | TM60 | 0.07 | 239.16 | 15.8 | 0.0249 | 255 | 0.138 | 0.091 | 9.25e-10 | refined |
| 350 | 500 | TM10 | TM60 | 0.07 | 239.16 | 15.8 | 0.0249 | 255 | 0.138 | 0.091 | nan | refined |
