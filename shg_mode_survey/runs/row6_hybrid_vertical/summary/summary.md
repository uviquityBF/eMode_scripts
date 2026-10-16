# Survey run `hybrid_vertical1`

23 geometries (23 ok, 0 failed), 7541 guided phase-match crossings (184 refined).

NCE = normalized conversion efficiency [%/W/cm^2], lossless; peak = loss-limited eta*L_eff^2 [%/W] at L_opt (scattering: EMode-native roughness; absorption: interface mechanisms + confinement-weighted bulk material loss, e.g. a lossy strip -- see geometry.py's lossy_mask/lossy_bulk_loss_dB_per_m and survey.bulk_absorption_loss; 0 wherever a geometry has no lossy region defined). overlap_shape is 0..1; A_shg is the plane-wave-equivalent interaction area for AlN d33.

**Window/box-mode filter**: 0 crossing(s) with an edge ratio > 0.02 excluded from every table below -- the SH field hasn't decayed by the simulation window's edge, meaning it's at least partly an artifact of the window's hard walls rather than real lateral confinement (see `shg_physics.lateral_edge_ratio`). Checked at full-refined resolution (`sh_edge_ratio`) where refined, at screening resolution (`sh_edge_ratio_screen`, same field `eta_screen` itself used) otherwise; `survey.py` also now skips window-limited crossings when choosing what to refine, so new runs shouldn't need the refined check to catch many. Full data, flag included, stays in `crossings.csv`.

## Top 25 by NCE

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid h=250 w=400 custom sin_w=700 sin_h=500 | TM10 | TM100 | 0.04 | 223.80 | 126 | 0.2437 | 34 | 0.214 | 0.147 | 1.78e-16 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=650 | TM10 | TM100 | 0.06 | 223.59 | 78.2 | 0.2359 | 54.4 | 0.261 | 0.152 | 1.97e-16 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM10 | TM100 | 0.17 | 224.21 | 71.8 | 0.1684 | 59.8 | 0.200 | 0.172 | 1.15e-15 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM10 | TM83? | 0.09 | 223.61 | 67.9 | 0.2036 | 63.5 | 0.200 | 0.176 | 6.46e-16 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM10 | TM100? | 0.24 | 223.77 | 67.8 | 0.1715 | 62.8 | 0.213 | 0.205 | 3.06e-17 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=650 | TM10 | TM101 | 0.05 | 222.09 | 55.4 | 0.2086 | 76.7 | 0.257 | 0.243 | 1.17e-17 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=650 | TM10 | TM103? | 0.05 | 223.59 | 53.2 | 0.1778 | 79.6 | 0.254 | 0.178 | 3.89e-17 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=800 | TM10 | TM103? | 0.11 | 223.52 | 50.2 | 0.2256 | 84.4 | 0.298 | 0.189 | 3.53e-16 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=800 | TM10 | TM100 | 0.05 | 223.48 | 49.8 | 0.1939 | 84.7 | 0.288 | 0.164 | 4.03e-17 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=650 | TM10 | TM100 | 0.04 | 223.58 | 39.4 | 0.1479 | 107 | 0.254 | 0.170 | 3.54e-17 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=650 | TM10 | TM103? | 0.08 | 221.93 | 34.3 | 0.1766 | 124 | 0.254 | 0.229 | 1.31e-16 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=950 | TM10 | TM102? | 0.24 | 223.40 | 33.8 | 0.2156 | 126 | 0.335 | 0.251 | 1.55e-16 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=800 | TM10 | TM100 | 0.06 | 223.46 | 33 | 0.1542 | 127 | 0.287 | 0.179 | 3.8e-17 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM00 | TM06 | 0.01 | 219.99 | 33 | 0.0609 | 116 | 0.134 | 0.214 | 1.11e-21 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM10 | TM82 | 0.10 | 230.72 | 32.6 | 0.1660 | 125 | 0.220 | 0.199 | 2.2e-15 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=500 | TM00 | TM07 | 0.05 | 218.16 | 31.7 | 0.0660 | 122 | 0.138 | 0.268 | 6.63e-22 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=800 | TM10 | TM101 | 0.06 | 221.98 | 30.9 | 0.2139 | 137 | 0.287 | 0.318 | 1.64e-17 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM106? | 0.08 | 223.31 | 30.6 | 0.2409 | 138 | 0.368 | 0.226 | 6.02e-17 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=650 | TM10 | TM101? | 0.04 | 223.58 | 27.9 | 0.1252 | 151 | 0.256 | 0.185 | 6.12e-17 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM105? | 0.04 | 223.43 | 27.5 | 0.1586 | 153 | 0.327 | 0.191 | 6.43e-17 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=650 | TM00 | TM09 | 0.01 | 219.43 | 26.1 | 0.0704 | 146 | 0.149 | 0.310 | 5.82e-22 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM104? | 0.05 | 223.41 | 26 | 0.1708 | 162 | 0.338 | 0.195 | 1.37e-17 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=650 | TM10 | TM82 | 0.25 | 232.62 | 25.9 | 0.1935 | 154 | 0.265 | 0.314 | 8.91e-16 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=650 | TM01 | TM101 | 0.05 | 221.35 | 25.4 | 0.1016 | 163 | 0.227 | 0.243 | 1.36e-18 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=800 | TM10 | TM101 | 0.31 | 222.05 | 25.3 | 0.1734 | 167 | 0.289 | 0.406 | 5.6e-17 | refined |

## Top 25 by loss-limited peak efficiency (refined)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | sh_edge_ratio | pump_scattering_dB_per_m | sh_scattering_dB_per_m | pump_absorption_dB_per_m | sh_absorption_dB_per_m | L_opt_mm | peak_efficiency_pct_per_W |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid h=250 w=400 custom sin_w=700 sin_h=500 | TM10 | TM100 | 0.04 | 223.80 | 126 | 1.78e-16 | 962 | 45492 | 2.28e+03 | 1.53e+07 | 0.01 | 3.96e-07 |
| hybrid h=250 w=400 custom sin_w=700 sin_h=650 | TM10 | TM100 | 0.06 | 223.59 | 78.2 | 1.97e-16 | 927 | 45783 | 2.33e+03 | 1.53e+07 | 0.01 | 2.45e-07 |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM10 | TM100 | 0.17 | 224.21 | 71.8 | 1.15e-15 | 970 | 43430 | 2.24e+03 | 1.47e+07 | 0.01 | 2.44e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM10 | TM100? | 0.24 | 223.77 | 67.8 | 3.06e-17 | 1059 | 44558 | 2.18e+03 | 1.54e+07 | 0.01 | 2.1e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=650 | TM10 | TM103? | 0.05 | 223.59 | 53.2 | 3.89e-17 | 1020 | 40692 | 2.23e+03 | 1.5e+07 | 0.01 | 1.75e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=800 | TM10 | TM100 | 0.05 | 223.48 | 49.8 | 4.03e-17 | 1002 | 45649 | 2.26e+03 | 1.54e+07 | 0.01 | 1.56e-07 |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM10 | TM83? | 0.09 | 223.61 | 67.9 | 6.46e-16 | 974 | 34384 | 2.29e+03 | 1.81e+07 | 0.01 | 1.53e-07 |
| hybrid h=250 w=400 custom sin_w=700 sin_h=800 | TM10 | TM103? | 0.11 | 223.52 | 50.2 | 3.53e-16 | 918 | 41845 | 2.35e+03 | 1.61e+07 | 0.01 | 1.44e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=650 | TM00 | TM07 | 0.01 | 232.42 | 19.9 | 8.04e-22 | 311 | 2535 | 1.3e+03 | 1.06e+07 | 0.01 | 1.33e-07 |
| hybrid h=350 w=400 custom sin_w=700 sin_h=650 | TM10 | TM100 | 0.04 | 223.58 | 39.4 | 3.54e-17 | 1093 | 45694 | 2.17e+03 | 1.49e+07 | 0.01 | 1.31e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM10 | TM82 | 0.10 | 230.72 | 32.6 | 2.2e-15 | 1008 | 27029 | 1.69e+03 | 1.38e+07 | 0.01 | 1.27e-07 |
| hybrid h=450 w=400 custom sin_w=700 sin_h=650 | TM00 | TM80 | 0.07 | 229.99 | 24 | 8.72e-23 | 449 | 21829 | 980 | 1.21e+07 | 0.01 | 1.22e-07 |
| hybrid h=450 w=400 custom sin_w=700 sin_h=650 | TM10 | TM101 | 0.05 | 222.09 | 55.4 | 1.17e-17 | 1189 | 44532 | 2.27e+03 | 1.85e+07 | 0.01 | 1.19e-07 |
| hybrid h=400 w=400 custom sin_w=700 sin_h=650 | TM00 | TM80? | 0.06 | 230.21 | 22.3 | 1.04e-22 | 408 | 21724 | 1.05e+03 | 1.2e+07 | 0.01 | 1.15e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM00 | TM80 | 0.10 | 231.03 | 18.3 | 1.04e-20 | 320 | 25315 | 1.34e+03 | 1.09e+07 | 0.01 | 1.14e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=800 | TM00 | TM80? | 0.16 | 230.85 | 20.6 | 1.17e-20 | 314 | 24714 | 1.34e+03 | 1.16e+07 | 0.01 | 1.14e-07 |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM00 | TM06 | 0.01 | 219.99 | 33 | 1.11e-21 | 303 | 3467 | 2e+03 | 1.48e+07 | 0.01 | 1.12e-07 |
| hybrid h=350 w=400 custom sin_w=700 sin_h=650 | TM10 | TM82 | 0.25 | 232.62 | 25.9 | 8.91e-16 | 1025 | 26064 | 1.52e+03 | 1.32e+07 | 0.01 | 1.1e-07 |
| hybrid h=450 w=400 custom sin_w=700 sin_h=1100 | TM00 | TM83? | 0.06 | 229.99 | 23.5 | 5.28e-22 | 448 | 20992 | 988 | 1.27e+07 | 0.01 | 1.09e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM00 | TM06 | 0.01 | 225.27 | 18 | 4.3e-23 | 337 | 2994 | 1.48e+03 | 1.11e+07 | 0.01 | 1.09e-07 |
| hybrid h=450 w=400 custom sin_w=700 sin_h=950 | TM00 | TM80? | 0.23 | 229.89 | 22.3 | 1.88e-21 | 448 | 22196 | 990 | 1.26e+07 | 0.01 | 1.05e-07 |
| hybrid h=350 w=400 custom sin_w=700 sin_h=800 | TM10 | TM100 | 0.06 | 223.46 | 33 | 3.8e-17 | 1070 | 46647 | 2.2e+03 | 1.54e+07 | 0.01 | 1.03e-07 |
| hybrid h=300 w=400 custom sin_w=700 sin_h=650 | TM00 | TM80 | 0.02 | 230.86 | 16.4 | 7.47e-21 | 315 | 24825 | 1.34e+03 | 1.1e+07 | 0.01 | 1.02e-07 |
| hybrid h=400 w=400 custom sin_w=700 sin_h=1100 | TM00 | TM83? | 0.06 | 230.22 | 21.5 | 7.32e-22 | 406 | 20851 | 1.06e+03 | 1.26e+07 | 0.01 | 1.01e-07 |
| hybrid h=350 w=400 custom sin_w=700 sin_h=950 | TM00 | TM80 | 0.26 | 230.44 | 20 | 4.63e-21 | 362 | 21870 | 1.17e+03 | 1.23e+07 | 0.01 | 9.81e-08 |

## Best TM->TM pairs (best instance of each pump->SH pair)

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid h=250 w=400 custom sin_w=700 sin_h=500 | TM10 | TM100 | 0.04 | 223.80 | 126 | 0.2437 | 34 | 0.214 | 0.147 | 1.78e-16 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM10 | TM83? | 0.09 | 223.61 | 67.9 | 0.2036 | 63.5 | 0.200 | 0.176 | 6.46e-16 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM10 | TM100? | 0.24 | 223.77 | 67.8 | 0.1715 | 62.8 | 0.213 | 0.205 | 3.06e-17 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=650 | TM10 | TM101 | 0.05 | 222.09 | 55.4 | 0.2086 | 76.7 | 0.257 | 0.243 | 1.17e-17 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=650 | TM10 | TM103? | 0.05 | 223.59 | 53.2 | 0.1778 | 79.6 | 0.254 | 0.178 | 3.89e-17 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=950 | TM10 | TM102? | 0.24 | 223.40 | 33.8 | 0.2156 | 126 | 0.335 | 0.251 | 1.55e-16 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM00 | TM06 | 0.01 | 219.99 | 33 | 0.0609 | 116 | 0.134 | 0.214 | 1.11e-21 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM10 | TM82 | 0.10 | 230.72 | 32.6 | 0.1660 | 125 | 0.220 | 0.199 | 2.2e-15 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=500 | TM00 | TM07 | 0.05 | 218.16 | 31.7 | 0.0660 | 122 | 0.138 | 0.268 | 6.63e-22 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM106? | 0.08 | 223.31 | 30.6 | 0.2409 | 138 | 0.368 | 0.226 | 6.02e-17 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=650 | TM10 | TM101? | 0.04 | 223.58 | 27.9 | 0.1252 | 151 | 0.256 | 0.185 | 6.12e-17 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM105? | 0.04 | 223.43 | 27.5 | 0.1586 | 153 | 0.327 | 0.191 | 6.43e-17 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=650 | TM00 | TM09 | 0.01 | 219.43 | 26.1 | 0.0704 | 146 | 0.149 | 0.310 | 5.82e-22 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM104? | 0.05 | 223.41 | 26 | 0.1708 | 162 | 0.338 | 0.195 | 1.37e-17 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=650 | TM01 | TM101 | 0.05 | 221.35 | 25.4 | 0.1016 | 163 | 0.227 | 0.243 | 1.36e-18 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=650 | TM00 | TM80 | 0.07 | 229.99 | 24 | 0.0632 | 142 | 0.162 | 0.205 | 8.72e-23 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=1100 | TM00 | TM83? | 0.06 | 229.99 | 23.5 | 0.0672 | 145 | 0.167 | 0.244 | 5.28e-22 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=950 | TM00 | TM80? | 0.23 | 229.89 | 22.3 | 0.0644 | 153 | 0.167 | 0.267 | 1.88e-21 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=800 | TM10 | TM102 | 0.02 | 221.16 | 21.4 | 0.1984 | 199 | 0.288 | 0.263 | 9.3e-18 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=800 | TM00 | TM85? | 0.10 | 229.94 | 20.9 | 0.0648 | 164 | 0.162 | 0.275 | 3.36e-21 | refined |

## Best crossing per geometry

| geom | pump_label | sh_label | sh_te_fraction | wavelength_sh | eta_pct_per_W_cm2 | overlap_shape | A_shg_um2 | A_eff_pump_um2 | A_eff_sh_um2 | sh_edge_ratio | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid h=250 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM106? | 0.08 | 223.31 | 30.6 | 0.2409 | 138 | 0.368 | 0.226 | 6.02e-17 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=450 | TM10 | TM100 | 0.17 | 224.21 | 71.8 | 0.1684 | 59.8 | 0.200 | 0.172 | 1.15e-15 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=500 | TM10 | TM100 | 0.04 | 223.80 | 126 | 0.2437 | 34 | 0.214 | 0.147 | 1.78e-16 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=650 | TM10 | TM100 | 0.06 | 223.59 | 78.2 | 0.2359 | 54.4 | 0.261 | 0.152 | 1.97e-16 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=800 | TM10 | TM103? | 0.11 | 223.52 | 50.2 | 0.2256 | 84.4 | 0.298 | 0.189 | 3.53e-16 | refined |
| hybrid h=250 w=400 custom sin_w=700 sin_h=950 | TM10 | TM102? | 0.24 | 223.40 | 33.8 | 0.2156 | 126 | 0.335 | 0.251 | 1.55e-16 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM104? | 0.05 | 223.41 | 26 | 0.1708 | 162 | 0.338 | 0.195 | 1.37e-17 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=500 | TM10 | TM100? | 0.24 | 223.77 | 67.8 | 0.1715 | 62.8 | 0.213 | 0.205 | 3.06e-17 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=650 | TM10 | TM103? | 0.05 | 223.59 | 53.2 | 0.1778 | 79.6 | 0.254 | 0.178 | 3.89e-17 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=800 | TM10 | TM100 | 0.05 | 223.48 | 49.8 | 0.1939 | 84.7 | 0.288 | 0.164 | 4.03e-17 | refined |
| hybrid h=300 w=400 custom sin_w=700 sin_h=950 | TM10 | TM100 | 0.31 | 223.52 | 24 | 0.1552 | 176 | 0.315 | 0.256 | 7.66e-17 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=1100 | TM10 | TM105? | 0.04 | 223.43 | 27.5 | 0.1586 | 153 | 0.327 | 0.191 | 6.43e-17 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=650 | TM10 | TM100 | 0.04 | 223.58 | 39.4 | 0.1479 | 107 | 0.254 | 0.170 | 3.54e-17 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=800 | TM10 | TM100 | 0.06 | 223.46 | 33 | 0.1542 | 127 | 0.287 | 0.179 | 3.8e-17 | refined |
| hybrid h=350 w=400 custom sin_w=700 sin_h=950 | TM10 | TM100 | 0.15 | 223.49 | 22.7 | 0.1374 | 185 | 0.309 | 0.210 | 7.41e-17 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=1100 | TM00 | TM83? | 0.06 | 230.22 | 21.5 | 0.0637 | 159 | 0.163 | 0.246 | 7.32e-22 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=650 | TM10 | TM103? | 0.08 | 221.93 | 34.3 | 0.1766 | 124 | 0.254 | 0.229 | 1.31e-16 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=800 | TM10 | TM101 | 0.06 | 221.98 | 30.9 | 0.2139 | 137 | 0.287 | 0.318 | 1.64e-17 | refined |
| hybrid h=400 w=400 custom sin_w=700 sin_h=950 | TM10 | TM102 | 0.02 | 221.51 | 19.8 | 0.2094 | 214 | 0.305 | 0.322 | 5.74e-18 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=1100 | TM00 | TM83? | 0.06 | 229.99 | 23.5 | 0.0672 | 145 | 0.167 | 0.244 | 5.28e-22 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=650 | TM10 | TM101 | 0.05 | 222.09 | 55.4 | 0.2086 | 76.7 | 0.257 | 0.243 | 1.17e-17 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=800 | TM10 | TM101 | 0.31 | 222.05 | 25.3 | 0.1734 | 167 | 0.289 | 0.406 | 5.6e-17 | refined |
| hybrid h=450 w=400 custom sin_w=700 sin_h=950 | TM10 | TM101? | 0.18 | 222.16 | 22.4 | 0.1862 | 189 | 0.308 | 0.380 | 9.31e-17 | refined |
