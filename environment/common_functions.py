# Functions shared by all environment files. 

### Tudat imports.
from tudatpy.interface import spice
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