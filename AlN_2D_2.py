import emodeconnection as emc
import numpy as np
import matplotlib.pyplot as plt
import time


## --- 1. Sweep Parameters ---
# Sweep thickness from 300nm to 800nm (adjust based on your growth capability)
thicknesses = np.arange(300, 400, 10)
neff_fund = []
neff_shg = []

# Fixed parameters
wavelength_fund = 450.0
w_core = 400.0  # [nm] Fixed width
dx, dy = 10.0, 10.0
target_mode_shg = None  # We will define this via prompt on the first run

em = emc.EMode()

# Sellmeier Material Definition
# Use double asterisks for power, ensure no spaces in the inner math, 
# and verify the negative B3/C3 values are handled cleanly.
eq_o = '(1+2.8032/(1-0.015287/x**2)+0.36335/(1-0.036095/x**2)-33508000/(1+367200000/x**2))**0.5'
eq_e = '(1+0.017061/(1-0.043855/x**2)+3.1976/(1-0.022642/x**2)-57269000/(1-74226000/x**2))**0.5'
anisotropic_equation = f"[{eq_o},{eq_e},{eq_o}]"
em.add_material(name='custom_AlN', refractive_index_equation=anisotropic_equation, wavelength_unit='um')

print(f"{'Thick (nm)':<12} | {'n_eff 450':<12} | {'n_eff 225':<12} | {'Delta N'}")
print("-" * 60)
 
h = 350
em.settings(wavelength=wavelength_fund, x_resolution=dx, y_resolution=dy,
            window_width=2000, window_height=h+2000, num_modes=3,
            boundary_condition='TM') # Using your 'TM' preference)
    
em.shape(name='Substrate', material='Al2O3', height=1000)
em.shape(name='core', material='custom_AlN', height=h, mask=w_core, sidewall_angle=5)
em.shape(name='TopClad', material='SiO2', height=800, shape_type='conformal')
em.FDM()
em.report()




for h in thicknesses:
    # --- Solve Fundamental (450nm) ---
 #   em.settings(wavelength=wavelength_fund, x_resolution=dx, y_resolution=dy,
 #                window_width=2000, window_height=h+2000, num_modes=3)
    
 #   em.shape(name='Substrate', material='Al2O3', height=1000)
#    em.shape(name='core', material='custom_AlN', height=h, mask=w_core, sidewall_angle=5)
    em.shape(name='core', height=h)
 #   em.shape(name='TopClad', material='SiO2', height=800, shape_type='conformal')
    
    # Check if modes actually exist before calling get_neff
    em.FDM()
    
    # Use get_report instead of get_neff to bypass potential API naming bugs
    try:
        n450 = em.get('effective_index')[0] # This is just to check if the report is available
        print(f"Success: n_eff = {n450}")
    except KeyError:
        print("Error: 'neff' not found in report. Did the solver converge?")
        n450 = np.nan
    except Exception as e:
        print(f"Unexpected connection error: {e}")
        n450 = np.nan

    neff_fund.append(n450)

    # --- Solve SHG (225nm) ---
    # Bumping num_modes because TM04 will be deep in the list
    em.settings(wavelength=wavelength_fund/2, x_resolution=dx/2, y_resolution=dy/2,
                window_width=2000, window_height=h+2000, num_modes=40)
    
    em.shape(name='Substrate', material='Al2O3', height=1000)
    em.shape(name='core', material='custom_AlN', height=h, mask=w_core, etch_depth = h, sidewall_angle=5)

    em.shape(name='TopClad', material='SiO2', height=800, shape_type='conformal')
    
    em.FDM()

    # --- Mode Selection Logic ---
    if target_mode_shg is None:
        em.report()
        em.plot() # Show the modes so you can find the TM04  **** can specify a file name to save the plot for reference ***
        user_input = input(f"\n[First Run at h={h}nm] Which mode number is the TM04? ")
        target_mode_shg = int(user_input)

    try:
        data = em.get_report()
        n225 = data['neff'][target_mode_shg] # Index 0 is the first mode
        print(f"Success: n_eff = {n225}")
    except KeyError:
        print("Error: 'neff' not found in report. Did the solver converge?")
        n225 = np.nan
    except Exception as e:
        print(f"Unexpected connection error: {e}")
        n225 = np.nan    

    # n225 = em.get_neff(mode_number=target_mode_shg)
    neff_shg.append(n225)

    delta_n = n450 - n225
    print(f"{h:<12.1f} | {n450:<12.5f} | {n225:<12.5f} | {delta_n:<12.5f}")

em.close()

## --- Plotting ---
plt.figure(figsize=(10,6))
plt.plot(thicknesses, neff_fund, 'b-o', label='Fundamental (450nm, Mode 1)')
plt.plot(thicknesses, neff_shg, 'r-s', label=f'SHG (225nm, Mode {target_mode_shg})')
plt.axhline(0, color='black', linestyle='--', alpha=0.3)
plt.xlabel('Waveguide Thickness (nm)')
plt.ylabel('Effective Index')
plt.title('Phase Matching Sweep: Fundamental vs. TM04')
plt.legend()
plt.grid(True)
plt.show()