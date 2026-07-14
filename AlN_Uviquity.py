import emodeconnection as emc

## Set simulation parameters
wavelength = 450 # [nm] wavelength
dx, dy = 10, 10 # [nm] resolution
w_core = 400 # [nm] waveguide core width
w_trench = 800 # [nm] waveguide side trench width
h_core = 340 # [nm] waveguide core height
h_clad = 800 # [nm] waveguide top and bottom clad
window_width = w_core + w_trench*2 # [nm]
window_height = h_core + h_clad*2 # [nm]
num_modes = 10 # [-] number of modes
boundary = '0S' # boundary condition

## Connect and initialize EMode
em = emc.EMode()

## Settings
em.settings(
    wavelength = wavelength, x_resolution = dx, y_resolution = dy,
    window_width = window_width, window_height = window_height,
    num_modes = num_modes, background_material = 'Air',
    boundary_condition = boundary,
)

equation = '2.0884' # see the SiN example for how to write a Sellmeier equation
em.add_material(name = 'custom_AlN',
    refractive_index_equation = equation, wavelength_unit = 'um')

## Draw shapes
em.shape(name = 'BOX', material = 'SiO2', height = h_clad)
em.shape(name = 'core', material = 'custom_AlN', height = h_core,
    etch_depth = h_core*1, mask = w_core, sidewall_angle = 15)

## View the refractive index profile
# em.plot()

## Solve the first mode
em.FDM()
em.confinement()
em.scattering()
em.report()
em.label_profile(name = '0') # save the data from the first mode

## Solve the second mode
em.shape(name = 'core', mask = w_core + 100)
em.FDM()
em.confinement()
em.scattering()
em.report()
em.label_profile(name = '1') # save the data from the first mode

## Calculate the overlap integral
overlap = em.overlap(label_a = '0', mode_a = 0,
    label_b = '1', mode_b = 0)
print('Power overlap: %0.3f %%' % (overlap*100))

## Plot the fields
em.plot()

## Get the refractive index of the core
n_ALN = em.refractive_index(material = 'custom_AlN',
                          wavelength = wavelength)
print('\nRefractive index of ALN:', n_ALN)

## Close EMode
em.close()
