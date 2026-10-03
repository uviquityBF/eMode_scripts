"""One-off probe: EMode timings + boundary-condition/symmetry behaviour for the SHG survey design.

Answers, for one ridge geometry (h=350, w=400):
  - how long a pump solve (450 nm) and an SH solve (225 nm, n_eff window) take, at 10 and 5 nm
  - what the symmetry boundary conditions '0A' / '0S' actually return (which modes, which half
    of the window the grid covers) -- '0A' should hold TM00 (Ey even in x)
  - whether pump and SH solves in one session share a grid (needed for overlap integrals)
  - effect of PML on N/S/E (leakage + leaky modes)
Prints a report and writes probe_timing_report.txt next to this script.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 '..', 'phase_matching_pipeline'))
import emode_helpers as pmh  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EQ_O = ('(1+2.8032/(1-0.015287/x**2)+0.36335/(1-0.036095/x**2)'
        '-33508000/(1+367200000/x**2))**0.5')
EQ_E = ('(1+0.017061/(1-0.043855/x**2)+3.1976/(1-0.022642/x**2)'
        '-57269000/(1-74226000/x**2))**0.5')
ANISO = f"[{EQ_O},{EQ_E},{EQ_O}]"
H, W = 350.0, 400.0

lines = []


def log(msg=''):
    print(msg, flush=True)
    lines.append(str(msg))


def ey_parity(Ey, x):
    """+1 if |Ey| is mirror-even about x=0 in the solved grid, -1 if odd, 0 if unclear (half grid)."""
    if x.min() > -1:  # half-domain grid: parity is set by the boundary condition, not visible
        return 0
    flipped = Ey[:, ::-1]
    num = np.sum(Ey * flipped)
    den = np.sum(Ey * Ey) + 1e-30
    return float(np.real(num / den))


def summarize(em, label, res, t_solve, wavelength):
    n = np.asarray(res['n_eff_tilde'])
    te = np.asarray(res.get('TE_fraction', [np.nan] * len(n)))
    t0 = time.time()
    keys = ['Ex', 'Ey', 'Ez', 'Hx', 'Hy', 'Hz', 'Sx', 'Sy', 'Sz']
    fields = em.get_fields(key=keys)
    t_fields = time.time() - t0
    fo = fields if hasattr(fields, 'field') else next(iter(fields.values()))
    x = np.asarray(fo.grid.x)
    y = np.asarray(fo.grid.y)
    raw = np.asarray(fo.field)
    log(f"--- {label}: solve {t_solve:.1f}s, get_fields {t_fields:.1f}s, field array {raw.shape} "
        f"{raw.dtype}, names {fo.field_names}, grid flags pml={fo.grid.is_pml} "
        f"exp={fo.grid.is_expanded} bc={fo.grid.is_bc}")
    log(f"   x [{x.min():.1f},{x.max():.1f}] n={len(x)} first={x[:3]}, "
        f"y [{y.min():.1f},{y.max():.1f}] n={len(y)}")
    f = {k: raw[fo.field_names.index(k), 0].T for k in keys}
    dA = np.gradient(x)[None, :] * np.gradient(y)[:, None] * 1e-18  # m^2
    eta0 = 376.730313
    n0 = np.real(np.asarray(res['n_eff_tilde'])[0])
    p_sz = np.sum(np.real(f['Sz']) * dA)
    p_eh = 0.5 * np.sum(np.real(f['Ex'] * np.conj(f['Hy']) - f['Ey'] * np.conj(f['Hx'])) * dA)
    p_paraxial = n0 / (2 * eta0) * np.sum((np.abs(f['Ex'])**2 + np.abs(f['Ey'])**2) * dA)
    log(f"   mode0 power conventions: intSz={p_sz:.4e}  0.5Re(ExH*)={p_eh:.4e}  "
        f"paraxial n|Et|^2/2eta0={p_paraxial:.4e}  ratios Sz/EH={p_sz / p_eh:.4f} "
        f"Sz/parax={p_sz / p_paraxial:.4f}  max|Ey|={np.abs(f['Ey']).max():.3e} "
        f"phase(Ez/Ey) at max={np.angle(f['Ez'].flat[np.abs(f['Ez']).argmax()] / (f['Ey'].flat[np.abs(f['Ez']).argmax()] + 1e-30)):.2f}")
    iy = fo.field_names.index('Ey')
    for m in range(len(n)):
        par = ey_parity(raw[iy, m].T, x)
        log(f"   mode {m:2d}: n_eff={n[m].real:.5f}{n[m].imag:+.2e}j  TE_frac={te[m]:.3f}  Ey-parity={par:+.2f}")
    return x, y


def main():
    log(f"Probe: ridge h={H} w={W}, AlN on sapphire, SiO2 clad")
    em = pmh.launch_session('probe_timing')
    try:
        pmh.setup_waveguide(em, ANISO, H, W, boundary_condition='0A')

        grids = {}
        for bc in ('0A', '0S', '00'):
            em.settings(boundary_condition=bc)
            t0 = time.time()
            r = pmh.solve_modes(em, f'pump_{bc}', wavelength=450.0, num_modes=6,
                                x_resolution=10.0, y_resolution=10.0, max_effective_index=0)
            grids[bc] = summarize(em, f'pump 450nm bc={bc} res=10', r, time.time() - t0, 450.0)
            if bc == '0A':
                n_pump = float(np.real(r['n_eff_tilde'][0]))

        em.settings(boundary_condition='0A')
        for res_nm in (10.0, 5.0):
            for nm in (15, 30):
                t0 = time.time()
                r = pmh.solve_modes(em, f'sh_r{int(res_nm)}_n{nm}', wavelength=225.0, num_modes=nm,
                                    x_resolution=res_nm, y_resolution=res_nm,
                                    max_effective_index=n_pump + 0.10)
                n = np.real(np.asarray(r['n_eff_tilde']))
                log(f"--- SH 225nm bc=0A res={res_nm} num_modes={nm} max_n={n_pump + 0.1:.4f}: "
                    f"solve {time.time() - t0:.1f}s, n_eff range [{n.min():.4f}, {n.max():.4f}]")
                if res_nm == 10.0 and nm == 15:
                    gx, gy = summarize(em, 'SH detail', r, 0.0, 225.0)
                    same = (len(gx) == len(grids['0A'][0]) and np.allclose(gx, grids['0A'][0])
                            and len(gy) == len(grids['0A'][1]) and np.allclose(gy, grids['0A'][1]))
                    log(f"   SH grid identical to pump '0A' grid: {same}")

        for k in (['permittivity'], ['eps'], ['Index']):
            try:
                pf = em.get_fields(key=k)
                po = pf if hasattr(pf, 'field') else next(iter(pf.values()))
                log(f"--- get_fields({k}) OK: {np.asarray(po.field).shape} names={po.field_names}")
                break
            except Exception as e:  # noqa: BLE001
                log(f"--- get_fields({k}) failed: {e!r}")
        t0 = time.time()
        ea = em.effective_area()
        log(f"--- effective_area(): {time.time() - t0:.1f}s -> {ea}")

        em.settings(boundary_condition='0A', pml_NSEW_bool=[1, 1, 1, 0], num_pml_layers=10,
                    remove_pml_modes_bool=True)
        t0 = time.time()
        r = pmh.solve_modes(em, 'pump_pml', wavelength=450.0, num_modes=4,
                            x_resolution=10.0, y_resolution=10.0, max_effective_index=0)
        summarize(em, 'pump 450nm bc=0A + PML(N,S,E)', r, time.time() - t0, 450.0)
        t0 = time.time()
        r = pmh.solve_modes(em, 'sh_pml', wavelength=225.0, num_modes=15,
                            x_resolution=10.0, y_resolution=10.0, max_effective_index=n_pump + 0.10)
        summarize(em, 'SH 225nm bc=0A + PML(N,S,E)', r, time.time() - t0, 225.0)
    finally:
        em.close(save=False)
        with open(os.path.join(HERE, 'probe_timing_report.txt'), 'w') as f:
            f.write('\n'.join(lines))


if __name__ == '__main__':
    main()
