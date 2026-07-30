# This file contains auxiliary math functions. 
import numpy as np

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
