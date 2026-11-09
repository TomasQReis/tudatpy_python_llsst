###
# This file contains all data pertaining to defining the GRAIL-A and -B spacecraft.
# Used in the validation case (Park et al. 2012). 
### 

### Imports for self-made functions 
from bodies.bodies import spacecraft
from auxiliary.math_functions import law_cosines_anomaly_spacing

### External library imports.
import numpy as np

### Grail A and B dictionaries
# Contain vehicle characteristics and initial keplerian states. 
# NOTE: Last three elements are marked zero since no a-priori values known. 
grailADict = {
    "name": "grailA",
    "mass": 313,        # kg
    # For reference lunar radius = 1737.4 km 
    "keplerianElems": [     
        1737.4e3,               # Semi-major Axis [m]. 
        0.001,                  # Eccentricity [-]
        np.deg2rad(89.2),       # Inclination [rads]
        np.deg2rad(0),          # Arg of Periapsis [rads]
        np.deg2rad(0),          # Longitude of Ascending Node [rads]
        np.deg2rad(0)           # True Anomaly [rads]
    ]
}

grailBDict = {
    "name": "grailB",
    "mass": 313,        # kg
    "keplerianElems": [     
        grailADict["keplerianElems"][0],        
        grailADict["keplerianElems"][1],
        grailADict["keplerianElems"][2],
        grailADict["keplerianElems"][3],
        grailADict["keplerianElems"][4],
        grailADict["keplerianElems"][5] + law_cosines_anomaly_spacing(
            orbitRadius= grailADict["keplerianElems"][0],
            desiredSpacing= 150e3    # Separation between A and B [m].
        )
    ]
}

### Create spacecraft objects and save to list.  
grailA = spacecraft(
    name= grailADict["name"],
    mass= grailADict["mass"],
    keplerianElems= grailADict["keplerianElems"]
)
grailB = spacecraft(
    name= grailBDict["name"],
    mass= grailBDict["mass"],
    keplerianElems= grailBDict["keplerianElems"]
)
grailList = [grailA, grailB]
