###
# This file contains all code pertaining to deifning the test vehicles
# used in low-fidelity simulated observations and parameter estimation.
# Basically just for me to get to know the program bit by bit and play around.
# "Donnager class"
### 

# Roci A and B dictionaries. 
# Contain vehicle characteristics and initial keplerian states. 

import numpy as np

from auxiliary.math import law_cosines_anomaly_spacing

rociA = {
    "name": "rociA",
    "mass": 100,        # kg
    # Ordered as [semiMajorAxis, eccentricity, inclination, argOfPeriapsis,
    # longOfAscending, trueAnom]
    "keplerianElems": [     
        1.7474e6,        # [m]. For reference lunar radius = 1737.4 km 
        0.001,
        np.deg2rad(89),
        np.deg2rad(5),
        np.deg2rad(10),
        np.deg2rad(0)
    ],
    # Initial cartesian state list. 
    "cartesianInitial": []
}


rociB = {
    "name": "rociB",
    "mass": 100,        # kg
    "keplerianElems": [     
        rociA["keplerianElems"][0],        
        rociA["keplerianElems"][1],
        rociA["keplerianElems"][2],
        rociA["keplerianElems"][3],
        rociA["keplerianElems"][4],
        rociA["keplerianElems"][5] + law_cosines_anomaly_spacing(
            orbitRadius= rociA["keplerianElems"][0],
            desiredSpacing= 1000    # Separation between rociA and rociB [m].
        )
    ],
    "cartesianInitial": np.array([])
}

# List of dictionaries for use in creating body settings. 
spacecraftDicts = [rociA, rociB]
