"""Bare partially-etched AlN rib, no loading strip at all (Simulation Study Plan row 1.2) --
geometry.Loaded's new no-strip mode (h_s=0, added 2026-10-14), the B=0 edge case of the Rib-loaded
topology, grouped under row 1 since it's still plain AlN. User request: "a plain, unloaded rib
waveguide... just AlN but not fully etched, over some significant range of thicknesses."

Two dimensions: t_film (total film thickness, the "range of thicknesses" asked for) x
etch_fraction (how much of that thickness is etched away outside the rib -- 0 would be row 4's
fully-unetched extreme, 1 would be row 1's fully-etched ridge; this sweep stays strictly between
them). etch_depth = etch_fraction * t_film, kept PROPORTIONAL to t_film (not a fixed nm value)
so every geometry is a similarly-shaped rib at a different overall size, rather than a
fixed-etch-depth cut that would mean a very different residual-slab fraction at each t_film.

w_rib fixed at 500nm (matches row 1's best w_core=500 and row 4's common w_s=500/1000 choices) --
not swept here to keep this first pass cheap; revisit if results motivate a width sweep too.

T_FILM_VALUES = (300, 400, 500, 600, 700) nm x ETCH_FRACTION_VALUES = (0.5, 0.7) -- 10 geometries.
0.5 keeps a substantial residual slab (closer to row 4's unetched extreme); 0.7 leaves only a thin
slab (closer to row 1's fully-etched ridge) -- brackets the "partially etched" space without
trying every fraction in between on a first pass.

sh_absorption_calibrated=True set from launch, per the 2026-10-12 standing SH-loss assumption.
"""

from survey_config import SETTINGS  # noqa: F401

T_FILM_VALUES = (300.0, 400.0, 500.0, 600.0, 700.0)
ETCH_FRACTION_VALUES = (0.5, 0.7)
W_RIB = 500.0

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': frac * t, 'w_rib': W_RIB,
                          'sh_absorption_calibrated': True})
              for t in T_FILM_VALUES for frac in ETCH_FRACTION_VALUES]

SMOKE = [GEOMETRIES[len(GEOMETRIES) // 2]]
