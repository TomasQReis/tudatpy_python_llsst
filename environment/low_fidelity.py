###
# This file contains all code pertaining to defining the low fidelity 
# bodies and dynamics used for simulated observations and parameter estimation. 
# This environment consists of an Earth-Moon system with low-degree (10)
# spherical harmonic gravity field for the Moon and point mass for the Earth.
# Basically just for me to get to know the program bit by bit and play around.
### 

### External library imports.
import numpy as np

### Tudat imports.
from tudatpy.interface import spice
from tudatpy import dynamics
from tudatpy.dynamics import environment_setup, propagation_setup, simulator
from tudatpy.astro import element_conversion
from tudatpy import constants
from tudatpy.util import result2array
from tudatpy.astro.time_representation import DateTime

# TODO: Put this in a common functions file. 
def load_spice(startEpoch: list, endEpoch: list, longEpoch: bool= False):
    """
    Loads NAIF SPICE kernels with the given start and end epochs, returns 
    given epochs in seconds since J2000.
    Args:
        startEpoch (list): List of int. Represents a date written as [year, month, 
        day, hour, minute, seconds]. 
        endEpoch (list): list of int. Same representation as start epoch. 
        longEpoch (bool): 
    Returns:
        simStartEpoch (float): Time in seconds since J2000.
        simEndEpoch (float): Time in seconds since J2000.
    """
    # Load kernels
    spice.load_standard_kernels()

    # Convert given epochs to seconds since J2000.
    if longEpoch:
        simStartEpoch = DateTime(
            startEpoch[0], startEpoch[1], startEpoch[2],
            startEpoch[3], startEpoch[4], startEpoch[5]
        ).to_epoch()
        simEndEpoch = DateTime(
            endEpoch[0], endEpoch[1], endEpoch[2],
            endEpoch[3], endEpoch[4], endEpoch[5]
        ).to_epoch()
    else:
        simStartEpoch = DateTime(
            startEpoch[0], startEpoch[1], startEpoch[2]
        ).to_epoch()
        simEndEpoch = DateTime(
            endEpoch[0], endEpoch[1], endEpoch[2],
        ).to_epoch()

    return simStartEpoch, simEndEpoch

def environment_bodies_low_fidelity(spacecrafts: list):
    """
    Sets up low-fidelity simulation environment bodies.

    Args:
        spacecraft (list): List of strings of spacecraft included in simulation.

    Returns:
        bodies ( SystemOfBodies ): Object containing the objects for bodies and 
        environment models constituting the physical environment.
    
    """
    # Default body settings for Earth and Moon.
    bodiesToCreate              = ["Earth", "Moon"]

    # Global frame origin set to Moon. Orientation to J2000.
    globalFrameOrigin           = "Moon"
    globalFrameOrientation      = "J2000"

    # Body settings.
    bodySettings              = environment_setup.get_default_body_settings(
        bodiesToCreate, globalFrameOrigin, globalFrameOrientation
    )

    # Add spacecraft to body settings. 
    for spacecraft in spacecrafts:
        bodySettings.add_empty_settings( spacecraft )

    # Create system of bodies. 
    bodies = environment_setup.create_system_of_bodies( bodySettings )

    return bodies


