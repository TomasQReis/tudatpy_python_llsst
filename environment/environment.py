# Functions shared by all environment files. 

### Tudat imports.
from tudatpy.interface import spice
from tudatpy.astro.time_representation import DateTime
from tudatpy.dynamics import environment

### Custom imports. 
from environment.moon_environment import *


def convert_to_j2000(date: list):
    """
    Converts given date to seconds since J2000. 
    Args: 
        date (list): Formatted as [year, month, day] or [year, month, day, hour
        minute, seconds].
        longEpoch (bool): True if long date list. 
    Returns:
        dateJ2000 (Time): Seconds since J2000. 
    """

    if len(date) == 6:
        dateJ2000 = DateTime(
            date[0], date[1], date[2],
            date[3], date[4], date[5]
        ).to_epoch()
    elif len(date) == 3:
        dateJ2000 = DateTime(
            date[0], date[1], date[2]
        ).to_epoch()
    else: 
        raise ValueError(
            f"Date is given outside of required format."
        )

    return dateJ2000


def check_timespan_limit(simStartEpoch: float, simEndEpoch: float):
        """
        Checks whether timespan is within R3-1 limits (1 day to 5 years). 
        Returns True if timespan is within limits. 
        Args:
            simStartEpoch (float): seconds since J2000 for start of simulation timespan.
            simEndEpoch (float): seconds since J2000 for end of simulation timespan. 
        """
        # Uses seconds between 1st Jan 2000 and 1st Jan 2005 as approximation for 5 year limit.
        maxSpan = 157766400.0
        # 1 day as minimum timespan.
        minSpan = 24*60**2

        timeSpan = simEndEpoch - simStartEpoch
         
        if timeSpan > maxSpan:
            raise RuntimeError(
                f"Timespan larger than maximum:\n"
                f"User: {timeSpan} -- Max: {maxSpan}"
            )
        elif timeSpan < minSpan:
            raise RuntimeError(
                f"Timespan smaller than minimum:\n"
                f"User: {timeSpan} -- Min: {minSpan}"
            )
        else:
            return True


# Load spice kernels and convert time epochs to seconds since J2000. 
def load_spice(simStartDate: list, simEndDate: list):
    """
    Loads NAIF SPICE kernels with the given start and end epochs, returns 
    given epochs in seconds since J2000.
    Args:
        startEpoch (list): List of int. Represents a date written as [year, month, 
        day, hour, minute, seconds]. 
        endEpoch (list): list of int. Same representation as start epoch. 
    Returns:
        simStartEpoch (float): Time in seconds since J2000.
        simEndEpoch (float): Time in seconds since J2000.
    """
    # Load kernels
    spice.load_standard_kernels()

    # Convert given epochs to seconds since J2000.
    simStartEpoch = convert_to_j2000(
        date= simStartDate
    )
    simEndEpoch = convert_to_j2000(
        date= simEndDate
    )

    if check_timespan_limit(
            simStartEpoch= simStartEpoch,
            simEndEpoch= simEndEpoch
        ):  print("Timespan Within Limits")


    return simStartEpoch, simEndEpoch

# Extract spherical harmonic coefficients from a desired body. 
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

    # Check whether extracted model is not a spherical harmonics model. 
    if type(gravityFieldModel) is not environment.SphericalHarmonicsGravityField:
        raise TypeError(
            f"ERROR: Body:{bodyName} does not have a spherical harmonics model associated with it."
        )
    
    # Extracts coefficients, keeping the (i,j) = (degree,order) entry order. 
    cosineCoefficients = gravityFieldModel.cosine_coefficients[:maxDegree+1, :maxOrder+1]
    sineCoefficients = gravityFieldModel.sine_coefficients[:maxDegree+1, :maxOrder+1]

    # Extract gravitational parameter.
    gravitationalParameter = body.gravitational_parameter 

    # Extract reference radius. 
    referenceRadius = gravityFieldModel.reference_radius
    
    return cosineCoefficients, sineCoefficients, referenceRadius, gravitationalParameter

# Environment selector
"""def environment_selector(
    centralBody: str= "Moon",
    level: int= 1,
    harmonicsMaxDegree: int= 10,
    harmonicsCustomFieldFile: str= "",
    # Will require additional inputs for higher levels. 
): 
    match centralBody:
        case "Moon":
            match level:
                case 1:
                    
                case 2:

                case 3:
    
    return simulationEnvironment
"""

