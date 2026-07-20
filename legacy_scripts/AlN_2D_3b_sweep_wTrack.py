import emodeconnection as emc
import numpy as np
import matplotlib.pyplot as plt
import time


# Fixed parameters of Geometry
wavelength_fund = 450.0
w_core = 340.0  # [nm] Fixed width
h_core = 340.0  # [nm] Fixed height
dx, dy = 10.0, 10.0


# Sellmeier Material Definition
# Use double asterisks for power, ensure no spaces in the inner math, and verify the negative B3/C3 values are handled cleanly.
eq_o = '(1+2.8032/(1-0.015287/x**2)+0.36335/(1-0.036095/x**2)-33508000/(1+367200000/x**2))**0.5'
eq_e = '(1+0.017061/(1-0.043855/x**2)+3.1976/(1-0.022642/x**2)-57269000/(1-74226000/x**2))**0.5'
anisotropic_equation = f"[{eq_o},{eq_e},{eq_o}]"

# Launch EMode 
em = emc.EMode(simulation_name='example_AlN_waveguide_sweep1')

# Set Up Simulation
em.add_material(name='custom_AlN',                                  
                refractive_index_equation=anisotropic_equation, 
                wavelength_unit='um')
em.settings(window_width=2000,window_height=h_core+2000, boundary_condition='TM') # Using your 'TM' preference)
em.shape(name='Substrate', material='Al2O3', height=1000)
em.shape(name='core', material='custom_AlN', height=h_core, mask=w_core, etch_depth=h_core, sidewall_angle=5)
em.shape(name='TopClad', material='SiO2', height=800, shape_type='conformal')
em.plot()

# Calculate Modes for FUNDAMENTAL WAVELENGTH
Nmodes_to_calculate = 2
em.settings(wavelength=wavelength_fund, x_resolution=dx, y_resolution=dy,window_width=2000,
            window_height=h_core+2000, num_modes=Nmodes_to_calculate, boundary_condition='TM') # Using your 'TM' preference)
em.FDM()                            #run the finite difference mode solver to find the modes of the structure
em.confinement(shape_list='core')   #calculate the confinement factor for each mode
em.report()                         #print information about the calculation results to command line
em.label_profile(name = 'dataset1') #store this set of results under label '0'
em.plot()

## Run wavelength sweep:  FUNDAMENTAL WAVELENGTH
wav_nm = np.arange(440, 460, 2)
data = em.sweep(key = 'wavelength', values = wav_nm,
    result = ['effective_index'])

em.save(simulation_name='example_AlN_waveguide_sweep1.eph')  # Save the simulation state to a fileem.save(simulation_name='example_AlN_waveguide_copy.eph')  # Save the simulation state to a file

neff_matrix = np.array(data['effective_index'])

#Create the plot
plt.figure(figsize=(10, 6), dpi=100)

# Option A: Plot all modes found in the sweep
num_modes_found = neff_matrix.shape[1]
for i in range(num_modes_found):
    plt.plot(wav_nm, neff_matrix[:, i], '-o', label=f'Mode {i+1}')

# 3. Formatting the chart
plt.title(f'Wavelength Sweep: Effective Index vs. Wavelength\n({w_core}nm x {h_core}nm AlN Core)', fontsize=12)
plt.xlabel('Wavelength (nm)', fontsize=11)
plt.ylabel('Effective Index (n_eff)', fontsize=11)
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.legend(loc='best')

# 4. Display or save
plt.tight_layout()
plt.show()



# Calculate Modes for SECOND HARMONIC WAVELENGTH
Nmodes_to_calculate = 40

## --- Step 1 & 2: Custom Tracking Sweep with Overlap ---
wav2_nm = np.arange(460, 440, -2) / 2
num_wavs = len(wav2_nm)

# Storage for results
tracked_neff = np.zeros(num_wavs)
tracked_overlaps_with_fund = np.zeros(num_wavs)
tracked_mode_indices = np.zeros(num_wavs, dtype=int)

# 1. Initialization: Get the "Target" mode from the first WL
# Assuming you've already run FDM at wav2_nm[0] and identified the mode
em.settings(wavelength=wav2_nm[0], num_modes=40)
em.FDM()
em.plot() # Visual check
target_idx = int(input(f"At {wav2_nm[0]}nm, which mode index is the TM04? "))

# We label this initial mode to use for the first overlap check
em.label_profile(name='reference_sh_mode', mode_number=target_idx)

# We also need the fundamental TM00 profile for the SHG overlap calculation
# (Assumes 'dataset1' was saved earlier with the 450nm results)
# Note: EMode usually handles the wavelength difference in overlap automatically

print(f"\n{'Wavelength':<12} | {'Mode Index':<10} | {'n_eff':<10} | {'Fund Overlap'}")
print("-" * 55)

for i, wl in enumerate(wav2_nm):
    # Update settings and solve
    em.settings(wavelength=wl, num_modes=40, x_resolution=dx/2, y_resolution=dy/2)
    em.FDM()
    
    # A. Find which of the 40 new modes matches our 'reference_sh_mode' best
    # em.overlap returns a list of overlap values between a labeled profile and current modes
    overlap_list = em.overlap(name='reference_sh_mode')
    best_match_idx = np.argmax(np.abs(overlap_list)) + 1 # +1 for 1-based indexing
    
    # B. Calculate spatial overlap with the Fundamental TM00 (saved as 'dataset1')
    # This is useful for SHG efficiency tracking
    fund_overlap_list = em.overlap(name='dataset1')
    fund_overlap_val = fund_overlap_list[best_match_idx - 1]

    # C. Store Data
    current_neff = em.get_neff(mode_number=best_match_idx)
    tracked_neff[i] = current_neff
    tracked_overlaps_with_fund[i] = fund_overlap_val
    tracked_mode_indices[i] = best_match_idx
    
    # D. UPDATE REFERENCE: The current best match becomes the reference for the NEXT step
    # This "walking" reference is what allows tracking through geometry shifts
    em.label_profile(name='reference_sh_mode', mode_number=best_match_idx)

    print(f"{wl:<12.2f} | {best_match_idx:<10} | {current_neff:<10.5f} | {fund_overlap_val:<10.5f}")


## --- Save Results ---
em.save(simulation_name='AlN_2D_3__SweepTrack_Results_tmp.eph')  # Save the simulation state to a fileem.save(simulation_name='example_AlN_waveguide_copy.eph')  # Save the simulation state to a file

## --- Export Results ---
export_data = np.column_stack((wav2_nm, tracked_neff, tracked_overlaps_with_fund, tracked_mode_indices))
header = 'Wavelength_nm,n_eff,Overlap_with_Fund,Original_Mode_Index'
np.savetxt('Tracked_SHG_Modes.csv', export_data, delimiter=',', header=header, comments='')





