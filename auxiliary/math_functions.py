# This file contains auxiliary math functions. 
import numpy as np
from numpy.typing import NDArray

def law_cosines_anomaly_spacing( orbitRadius: float, desiredSpacing: float ):
    """
    Returns the required true anomaly difference between two satellites with
    a desired spacing value. Assumes a perfectly circular orbit in order
    to use law of cosines. 
    
    Args:
        orbitRadius (float): Orbit radius.
        desiredSpacing (float): Desired spacing between satellites. Must be 
        given in the same units as orbitRadius.
    Returns:
        trueAnomalySpacing (float): [rads] true anomaly spacing. 
    """

    return np.arccos( 
        (2*orbitRadius**2 - desiredSpacing**2) / (2*orbitRadius**2) 
    )


def linear_interpolation( yValues1:NDArray , yValues2:NDArray , 
                          xValues: NDArray , xInterpol: float):
    """
    Linearly interpolates two (or two sets) of y values, whose corresponding
    x-values are given in a 2-element array. The function assumes the two
    sets of y-values are given such that x[0] is associated to the yValues1 array
    and x[1] to the yValues2 array. 
    """

    frac = (xInterpol - xValues[0]) / (xValues[1] - xValues[0])

    interpolatedArr = yValues1 + frac * ( yValues2 - yValues1)

    return interpolatedArr 