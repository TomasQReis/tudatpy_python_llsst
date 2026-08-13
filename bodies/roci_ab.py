###
# This file contains all data pertaining to deifning the test vehicles
# used in low-fidelity simulated observations and parameter estimation.
# Basically just for me to get to know the program bit by bit and play around.
# "Donnager class"
### 

### Imports for self-made functions 
from bodies.common import spacecraft
from auxiliary.math_functions import *

### External library imports.
import numpy as np
from copy import deepcopy

### Roci A and B dictionaries. 
# Contain vehicle characteristics and initial keplerian states. 
rociADict = {
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
    ]
}

rociBDict = deepcopy(rociADict)

### Spacecraft class objects. 
rociA = spacecraft(
    name= "rociA",
    mass= 100.0,
    keplerianElems= rociADict["keplerianElems"]
)

rociB = spacecraft(
    name= "rociB",
    mass= 100.0,
    keplerianElems= rociBDict["keplerianElems"]
)


