# Functions shared by all environment files. 

### Tudat imports.
from tudatpy.interface import spice
from tudatpy.astro.time_representation import DateTime
from tudatpy.dynamics import environment

# Load spice kernels and convert time epochs to seconds since J2000. 
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


def return_sh_coefficients(
    bodyName: str,
    systemOfBodies: environment.SystemOfBodies,
    maxDegree: int,
    maxOrder: int,
):
    """
    Returns the spherical harmonics coefficients for a body. 
    Args:
        bodyName (str): Name of body.
        systemOfBodies (SystemOfBodies): System of bodies used. 
        maxDegree (int): maximum desired degree for returned coefficients. 
        maxOrder (int): maximum desired order for returned coefficients.
    Returns:
        cosineCoefficients (NDArray): Array of cosine coefficients following the (i,j)=(degree,order) indexing format.
        sineCoefficients (NDArray): Array of sine coefficients following the (i,j)=(degree,order) indexing format.
    """

    # Extract singular body from system of bodies.  
    body = systemOfBodies.get(
        body_name= bodyName
    )

    # Extract gravity field model. 
    gravityFieldModel =  body.gravity_field_model

    # Check whether extracted model is a spherical harmonics model. 
    if type(gravityFieldModel) is environment.SphericalHarmonicsGravityField:
        # Extracts coefficients, keeping the (i,j) = (degree,order) entry order. 
        cosineCoefficients = gravityFieldModel.cosine_coefficients[:maxDegree+1, :maxOrder+1]
        sineCoefficients = gravityFieldModel.sine_coefficients[:maxDegree+1, :maxOrder+1]
    else:
        print("ERROR: Provided body does not have a spherical harmonics model associated with it.")
        return 0,0

    return cosineCoefficients, sineCoefficients

