import emodeconnection as emc
import numpy as np

## --- 1. Simulation Setup ---
wavelength_fund = 450.0  # [nm]
dx_base, dy_base = 10.0, 10.0 

w_core = 400.0
h_core = 340.0
w_trench = 800.0
h_clad_top = 800.0
h_clad_bottom = 1000.0

window_width = w_core + w_trench * 2
window_height = h_core + h_clad_top + h_clad_bottom
angleofsidewall = 5.0

## --- 2. Advanced Sellmeier Definitions ---
# Note: Ensure 'x' (wavelength) is in microns as per wavelength_unit='um'
# Formatting as x**2 is generally more robust in Python-based parsers
eq_o = '(1 + 2.8032/(1 - 0.015287/x**2) + 0.36335/(1 - 0.036095/x**2) + -33508000/(1 + 367200000/x**2))**0.5'
eq_e = '(1 + 0.017061/(1 - 0.043855/x**2) + 3.1976/(1 - 0.022642/x**2) + -57269000/(1 - 74226000/x**2))**0.5'
anisotropic_eq = f"[{eq_o}, {eq_e}, {eq_o}]"

## --- 3. Initialize EMode ---
em = emc.EMode()

# Add Material once (it stays in the session database)
em.add_material(name='custom_AlN', refractive_index_equation=anisotropic_eq, wavelength_unit='um')

## --- 4. Loop Through Wavelengths (Fundamental & SHG) ---
wavelengths = [wavelength_fund, wavelength_fund / 2]

for wl in wavelengths:
    print(f"\n--- Solving for Wavelength: {wl} nm ---")
    
    # Scale resolution for the shorter wavelength to maintain accuracy
    res_scale = wl / wavelength_fund
    current_dx = dx_base * res_scale
    current_dy = dy_base * res_scale
    
    # For 225nm, we usually need to look for more modes as the V-number increases
    current_num_modes = 10 if wl == 450 else 30 

    em.settings(
        wavelength=wl, 
        x_resolution=current_dx, 
        y_resolution=current_dy,
        window_width=window_width, 
        window_height=window_height,
        num_modes=current_num_modes, 
        background_material='Air',
        boundary_condition='TM' # Using your 'TM' preference
    )

    ## --- 5. Build Geometry ---
    em.shape(name='Substrate', material='Al2O3', height=h_clad_bottom)
    
    # Trapezoidal Core
    em.shape(name='core', material='custom_AlN', height=h_core,
             etch_depth=h_core, mask=w_core, sidewall_angle=angleofsidewall)
    
    # Conformal Top Cladding
    em.shape(name='TopClad', material='SiO2', height=h_clad_top, shape_type='conformal')

    ## --- 6. Solve and Report ---
    em.FDM()
    em.confinement(shape_list='core')
    em.scattering(shape='core')
    
    # Print results to console
    em.report()
    
    # Optional: Save image for each wavelength
    # em.plot(save_path=f"Mode_Profile_{int(wl)}nm.png")
    em.plot()

## Close Connection
em.close()