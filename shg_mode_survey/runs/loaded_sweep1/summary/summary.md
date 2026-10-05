# Survey run `loaded_sweep1`

8 geometries (8 ok, 0 failed), 2399 guided phase-match crossings (64 refined).

NCE = normalized conversion efficiency [%/W/cm^2], lossless; peak = loss-limited eta*L_eff^2 [%/W] at L_opt (scattering: EMode-native roughness; absorption: interface mechanisms + confinement-weighted bulk material loss, e.g. a lossy strip -- see geometry.py's lossy_mask/lossy_bulk_loss_dB_per_m and survey.bulk_absorption_loss; 0 wherever a geometry has no lossy region defined). overlap_shape is 0..1; A_shg is the plane-wave-equivalent interaction area for AlN d33.

## Top 25 by NCE

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | status |
|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM123? | 0.00 | 230.51 | 293 | 0.2705 | 8.94 | 0.100 | 0.227 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM05? | 0.01 | 225.44 | 159 | 0.3268 | 16.3 | 0.173 | 0.373 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.2347 | 16.3 | 0.188 | 0.661 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM03 | 0.00 | 229.74 | 152 | 0.2833 | 16.8 | 0.181 | 0.308 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM03 | 0.00 | 231.29 | 150 | 0.2615 | 17.6 | 0.188 | 0.316 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM04 | 0.00 | 227.83 | 136 | 0.3132 | 18.9 | 0.178 | 0.335 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TM106? | 0.00 | 231.43 | 111 | 0.1943 | 25.5 | 0.196 | 0.602 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM162? | 0.01 | 230.69 | 77.2 | 0.1328 | 34 | 0.101 | 0.430 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM86 | 0.00 | 221.19 | 59 | 0.0877 | 57.5 | 0.322 | 0.366 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM67 | 0.06 | 220.73 | 57.3 | 0.1996 | 45.7 | 0.165 | 0.445 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM09? | 0.05 | 225.20 | 53.1 | 0.1068 | 57.5 | 0.108 | 0.326 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM26 | 0.00 | 234.91 | 43.6 | 0.0939 | 68.2 | 0.193 | 1.030 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM05? | 0.06 | 225.11 | 39.8 | 0.0718 | 80.6 | 0.296 | 0.379 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM00 | TM65 | 0.01 | 233.32 | 39.1 | 0.0848 | 66.7 | 0.104 | 0.945 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM123 | 0.05 | 231.17 | 33.8 | 0.0799 | 89 | 0.120 | 0.623 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM165? | 0.02 | 225.38 | 33.4 | 0.0511 | 97.6 | 0.201 | 0.357 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM88? | 0.02 | 224.52 | 31.7 | 0.1230 | 81.9 | 0.171 | 0.859 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM05? | 0.01 | 225.74 | 28.5 | 0.0646 | 115 | 0.343 | 0.391 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TM145 | 0.02 | 234.01 | 28.2 | 0.0939 | 99.5 | 0.205 | 1.149 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM143? | 0.04 | 230.22 | 27.7 | 0.1128 | 95.5 | 0.186 | 0.475 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM165 | 0.03 | 231.41 | 27 | 0.0679 | 111 | 0.138 | 0.930 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM103 | 0.02 | 233.97 | 25.2 | 0.0676 | 118 | 0.129 | 0.633 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TM48? | 0.01 | 226.61 | 25.1 | 0.1014 | 114 | 0.183 | 1.147 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM83 | 0.02 | 222.92 | 21.8 | 0.0755 | 123 | nan | nan | screened |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM00 | TM128? | 0.01 | 215.98 | 21.1 | 0.0469 | 161 | 0.265 | 0.317 | refined |

## Top 25 by loss-limited peak efficiency (refined)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | pump_scattering_dB_per_m | sh_scattering_dB_per_m | pump_absorption_dB_per_m | sh_absorption_dB_per_m | L_opt_mm | peak_efficiency_pct_per_W |
|---|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM26 | 0.00 | 234.91 | 43.6 | 1072 | 0 | 6.78e+05 | 9.81e+05 | 0.01 | 2.78e-06 |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM00 | TM65 | 0.01 | 233.32 | 39.1 | 356 | 6 | 1.08e+06 | 4.86e+05 | 0.01 | 2.36e-06 |
| loaded t=600 e=0 custom h_s=70 w_s=1000 | TM00 | TM26 | 0.00 | 234.46 | 3.51 | 30 | 0 | 8.27e+04 | 8.01e+05 | 0.02 | 1.81e-06 |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM46 | 0.00 | 233.88 | 12.7 | 1150 | 0 | 7.63e+05 | 6.96e+05 | 0.01 | 1.01e-06 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TM145 | 0.02 | 234.01 | 28.2 | 511 | 0 | 1.02e+06 | 8.9e+05 | 0.01 | 9.9e-07 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 98 | 4 | 1.11e+06 | 2.93e+06 | 0.00 | 8.54e-07 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM25 | 0.00 | 232.72 | 18.9 | 99 | 6 | 1.14e+06 | 6.21e+05 | 0.01 | 8.22e-07 |
| loaded t=600 e=0 custom h_s=70 w_s=500 | TM00 | TM66 | 0.01 | 233.10 | 0.735 | 42 | 7 | 4.88e+04 | 8.83e+05 | 0.02 | 4.06e-07 |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM103 | 0.02 | 233.97 | 25.2 | 1313 | 7 | 9.2e+05 | 1.63e+06 | 0.01 | 3.76e-07 |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM165 | 0.03 | 231.41 | 27 | 1277 | 21 | 9.44e+05 | 1.75e+06 | 0.01 | 3.27e-07 |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM20 | TM64? | 0.01 | 227.26 | 1.09 | 3 | 52 | 1.47e+04 | 1.46e+06 | 0.02 | 3.27e-07 |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM162? | 0.01 | 230.69 | 77.2 | 363 | 69 | 1.24e+06 | 5.61e+06 | 0.00 | 3.07e-07 |
| loaded t=600 e=0 custom h_s=70 w_s=1000 | TM00 | TM46 | 0.00 | 233.97 | 1.32 | 31 | 3 | 8.53e+04 | 1.39e+06 | 0.01 | 2.7e-07 |
| loaded t=600 e=0 custom h_s=70 w_s=500 | TM20 | TM66 | 0.01 | 234.90 | 0.12 | 9 | 0 | 1.66e+04 | 5.01e+05 | 0.05 | 2.45e-07 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TM106? | 0.00 | 231.43 | 111 | 519 | 6 | 1.15e+06 | 1.29e+07 | 0.00 | 2.18e-07 |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM00 | TM85 | 0.01 | 231.26 | 18.1 | 361 | 63 | 1.18e+06 | 1.42e+06 | 0.01 | 2.06e-07 |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM123? | 0.00 | 230.51 | 293 | 364 | 78 | 1.25e+06 | 2.6e+07 | 0.00 | 1.96e-07 |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM123 | 0.05 | 231.17 | 33.8 | 1360 | 21 | 1.06e+06 | 4e+06 | 0.00 | 1.68e-07 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM03 | 0.00 | 231.29 | 150 | 254 | 22 | 1.23e+06 | 2.12e+07 | 0.00 | 1.43e-07 |
| loaded t=600 e=0 custom h_s=70 w_s=1000 | TM10 | TM66 | 0.01 | 234.44 | 0.361 | 33 | 0 | 4.5e+04 | 1.41e+06 | 0.02 | 9.34e-08 |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM45 | 0.00 | 232.12 | 13.9 | 100 | 25 | 1.17e+06 | 1.83e+06 | 0.01 | 8.83e-08 |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM124? | 0.02 | 221.13 | 15.5 | 162 | 508 | 3.44e+05 | 5.98e+06 | 0.00 | 7.44e-08 |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM00 | TM145? | 0.02 | 222.90 | 20.6 | 383 | 669 | 1.68e+06 | 7.62e+06 | 0.00 | 5.95e-08 |
| loaded t=600 e=0 custom h_s=70 w_s=1000 | TM10 | TM86 | 0.01 | 233.47 | 0.327 | 46 | 1 | 1.26e+05 | 1.56e+06 | 0.01 | 4.98e-08 |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM20 | TM103 | 0.01 | 230.93 | 12.1 | 521 | 108 | 1.21e+06 | 7.65e+06 | 0.00 | 3.9e-08 |

## Best TM->TM pairs (best instance of each pump->SH pair)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | status |
|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM123? | 0.00 | 230.51 | 293 | 0.2705 | 8.94 | 0.100 | 0.227 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM05? | 0.01 | 225.44 | 159 | 0.3268 | 16.3 | 0.173 | 0.373 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.2347 | 16.3 | 0.188 | 0.661 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM03 | 0.00 | 229.74 | 152 | 0.2833 | 16.8 | 0.181 | 0.308 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM03 | 0.00 | 231.29 | 150 | 0.2615 | 17.6 | 0.188 | 0.316 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM04 | 0.00 | 227.83 | 136 | 0.3132 | 18.9 | 0.178 | 0.335 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TM106? | 0.00 | 231.43 | 111 | 0.1943 | 25.5 | 0.196 | 0.602 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM162? | 0.01 | 230.69 | 77.2 | 0.1328 | 34 | 0.101 | 0.430 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM86 | 0.00 | 221.19 | 59 | 0.0877 | 57.5 | 0.322 | 0.366 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM67 | 0.06 | 220.73 | 57.3 | 0.1996 | 45.7 | 0.165 | 0.445 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM09? | 0.05 | 225.20 | 53.1 | 0.1068 | 57.5 | 0.108 | 0.326 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM26 | 0.00 | 234.91 | 43.6 | 0.0939 | 68.2 | 0.193 | 1.030 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM00 | TM65 | 0.01 | 233.32 | 39.1 | 0.0848 | 66.7 | 0.104 | 0.945 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM10 | TM123 | 0.05 | 231.17 | 33.8 | 0.0799 | 89 | 0.120 | 0.623 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM165? | 0.02 | 225.38 | 33.4 | 0.0511 | 97.6 | 0.201 | 0.357 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM88? | 0.02 | 224.52 | 31.7 | 0.1230 | 81.9 | 0.171 | 0.859 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM05? | 0.01 | 225.74 | 28.5 | 0.0646 | 115 | 0.343 | 0.391 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM20 | TM145 | 0.02 | 234.01 | 28.2 | 0.0939 | 99.5 | 0.205 | 1.149 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM10 | TM143? | 0.04 | 230.22 | 27.7 | 0.1128 | 95.5 | 0.186 | 0.475 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM165 | 0.03 | 231.41 | 27 | 0.0679 | 111 | 0.138 | 0.930 | refined |

## Best crossing per geometry

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | status |
|---|---|---|---|---|---|---|---|---|---|---|
| loaded t=354 e=0 custom h_s=150 w_s=1000 | TM00 | TM05? | 0.01 | 225.44 | 159 | 0.3268 | 16.3 | 0.173 | 0.373 | refined |
| loaded t=354 e=0 custom h_s=150 w_s=500 | TM00 | TM123? | 0.00 | 230.51 | 293 | 0.2705 | 8.94 | 0.100 | 0.227 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=1000 | TM10 | TM86 | 0.00 | 221.19 | 59 | 0.0877 | 57.5 | 0.322 | 0.366 | refined |
| loaded t=354 e=0 custom h_s=70 w_s=500 | TM00 | TM165? | 0.02 | 225.38 | 33.4 | 0.0511 | 97.6 | 0.201 | 0.357 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=1000 | TM00 | TM05 | 0.00 | 233.44 | 154 | 0.2347 | 16.3 | 0.188 | 0.661 | refined |
| loaded t=600 e=0 custom h_s=150 w_s=500 | TM10 | TM09? | 0.05 | 225.20 | 53.1 | 0.1068 | 57.5 | 0.108 | 0.326 | refined |
| loaded t=600 e=0 custom h_s=70 w_s=1000 | TM00 | TM89? | 0.14 | 221.63 | 16.4 | 0.0522 | 198 | 0.473 | 0.675 | refined |
| loaded t=600 e=0 custom h_s=70 w_s=500 | TM20 | TM611? | 0.03 | 217.12 | 0.774 | 0.0133 | 4.51e+03 | 0.737 | 0.799 | refined |
