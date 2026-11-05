###
# This file contains all data defining the spacecraft Roci A and B.
# Basically just for me to get to know the program bit by bit and play around.
# "Donnager class"
### 

### Imports for self-made functions 
from bodies.bodies import spacecraft
from auxiliary.math_functions import *

### External library imports.
import numpy as np

### Roci A and B dictionaries. 
# Contain vehicle characteristics and initial keplerian states. 
rociADict = {
    "name": "rociA",
    "mass": 313,        # kg
    # Ordered as [semiMajorAxis, eccentricity, inclination, argOfPeriapsis,
    # longOfAscending, trueAnom]
    "keplerianElems": [     
        1737.4e3 + 200e3,        # [m]. For reference lunar radius = 1737.4 km 
        0.001,
        np.deg2rad(89),
        np.deg2rad(0),
        np.deg2rad(0),
        np.deg2rad(0)
    ]
}

rociBDict = {
    "name": "rociB",
    "mass": 313,        # kg
    "keplerianElems": [     
        rociADict["keplerianElems"][0],        
        rociADict["keplerianElems"][1],
        rociADict["keplerianElems"][2],
        rociADict["keplerianElems"][3],
        rociADict["keplerianElems"][4],
        rociADict["keplerianElems"][5] + law_cosines_anomaly_spacing(
            orbitRadius= rociADict["keplerianElems"][0],
            desiredSpacing= 150e3    # Separation between rociA and rociB [m].
        )
    ]
}

### Spacecraft class objects. 
rociA = spacecraft(
    name= "rociA",
    mass= rociADict["mass"],
    keplerianElems= rociADict["keplerianElems"]
)

rociB = spacecraft(
    name= "rociB",
    mass= rociBDict["mass"],
    keplerianElems= rociBDict["keplerianElems"]
)

# List of dictionaries for use in creating body settings. 
rociList = [rociA, rociB]
