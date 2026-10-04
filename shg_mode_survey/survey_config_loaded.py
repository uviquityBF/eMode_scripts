"""First loaded-family sweep (John Carlson deck slides 10-15). Same settings as survey_config.py.

Before the full sweep, run ONE geometry and check em.plot(component='Index') / the field plots:
the partial-etch and mask_offset conventions in geometry.Loaded are not yet verified, and the
strip material must exist in EMode's database ('TiO2') or be given as strip_eq (n + k j).
"""

from survey_config import SETTINGS  # noqa: F401

GEOMETRIES = [('loaded', {'t_film': t, 'etch_depth': 0.0, 'strip_material': 'TiO2',
                          'h_s': hs, 'w_s': ws})
              for t in (354.0, 600.0) for hs in (70.0, 150.0) for ws in (500.0, 1000.0)]

SMOKE = GEOMETRIES[:1]
