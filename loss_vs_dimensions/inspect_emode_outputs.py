"""One-off diagnostic: run this ONCE before trusting sweep_loss_vs_dimensions.py.

It solves a single lossless TM00 mode, calls confinement()/scattering() and the various
get_* accessors, and prints the concrete shape/type/keys of everything the sweep script
needs to extract (native scattering loss value + units, and the field/grid data used for the
post-processed absorption model). emodeconnection's docs don't specify these return shapes
precisely (see EMode_Function_Reference.md), so this fills that gap empirically instead of
guessing -- share this script's printed output so the extraction code in
sweep_loss_vs_dimensions.py can be finalized against what your installed EMode version
actually returns.

Uses clear='all' (kills any other EMode session on THIS machine) since it's meant to be a
quick isolated check -- don't run this if you have another notebook's EMode session open that
you want to keep (see the single-seat-license gotcha in CLAUDE.md re: the OTHER machine too).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 '..', 'phase_matching_pipeline'))
import emode_helpers as pmh  # noqa: E402

import numpy as np  # noqa: E402


def describe(name, obj, depth=0):
    indent = '  ' * depth
    if hasattr(obj, 'model_dump'):
        print(f"{indent}{name}: pydantic model {type(obj).__name__}")
        for k, v in obj.model_dump().items():
            describe(f".{k}", getattr(obj, k, v), depth + 1)
    elif isinstance(obj, dict):
        print(f"{indent}{name}: dict, keys={list(obj.keys())}")
        for k, v in obj.items():
            describe(f"[{k!r}]", v, depth + 1)
    elif isinstance(obj, np.ndarray):
        print(f"{indent}{name}: ndarray shape={obj.shape} dtype={obj.dtype} "
              f"sample={np.asarray(obj).ravel()[:3]}")
    elif isinstance(obj, (list, tuple)):
        print(f"{indent}{name}: {type(obj).__name__} len={len(obj)} "
              f"first_item_type={type(obj[0]).__name__ if obj else None}")
        if obj and not isinstance(obj[0], (int, float, str, complex)):
            describe(f"[0]", obj[0], depth + 1)
    else:
        print(f"{indent}{name}: {type(obj).__name__} = {obj!r}"[:200])


def main():
    h_core, w_core = 340.0, 400.0
    wavelength = 450.0
    eq_o = ('(1+2.8032/(1-0.015287/x**2)+0.36335/(1-0.036095/x**2)'
            '-33508000/(1+367200000/x**2))**0.5')
    eq_e = ('(1+0.017061/(1-0.043855/x**2)+3.1976/(1-0.022642/x**2)'
            '-57269000/(1-74226000/x**2))**0.5')
    anisotropic_equation = f"[{eq_o},{eq_e},{eq_o}]"

    em = pmh.launch_session('inspect_loss_outputs', clear='all')
    try:
        pmh.setup_waveguide(em, anisotropic_equation, h_core, w_core)
        em.shape(name='core', roughness_rms=[2.0, 2.0], correlation_length=[50.0, 50.0])

        em.settings(wavelength=wavelength, num_modes=2, x_resolution=10.0, y_resolution=10.0,
                    max_effective_index=2.6)

        print("\n=== FDM() ===")
        fdm = em.FDM()
        describe('FDM_result', fdm)

        print("\n=== confinement() ===")
        conf = em.confinement(shape_list='core')
        describe('confinement_result', conf)

        print("\n=== scattering() ===")
        scat = em.scattering(shape='core')
        describe('scattering_result', scat)

        print("\n=== get_shape('core') (after scattering) ===")
        shp = em.get_shape(key='core')
        describe('shape_core', shp)

        print("\n=== get_fields(['Ex','Ey','Ez','Sx','Sy','Sz']) ===")
        fields = em.get_fields(key=['Ex', 'Ey', 'Ez', 'Sx', 'Sy', 'Sz'])
        describe('fields', fields)

        print("\n=== get_grid() ===")
        grid = em.get_grid()
        describe('grid', grid)

        print("\n=== report() ===")
        em.report()

        # get_profile() returns the full profile (all field data, unfolded/PML-included) --
        # not needed for this pipeline (the core mask is built analytically, not from EMode's
        # permittivity export) and has been observed to hang/take a very long time to return.
        # Left out of the default run; uncomment only if you specifically want to inspect it,
        # and be ready to Ctrl+C -- the `finally` below still closes the session cleanly on
        # KeyboardInterrupt.
        # print("\n=== get_profile() ===")
        # profile = em.get_profile()
        # describe('profile', profile)
    finally:
        em.close(save=False)


if __name__ == '__main__':
    main()
