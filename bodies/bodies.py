### Imports for self-made functions 
from auxiliary.math_functions import *

### External library imports.
import numpy as np
from numpy.typing import NDArray

### Tudat imports. 
import tudatpy.dynamics as dynamics
from tudatpy.dynamics.environment_setup.ground_station import GroundStationSettings

### Base bodies class.
class body:
    def __init__(
        self,
        name: str,
    ):
        self.name = name

### Spacecraft class.
class spacecraft (body):
    # Stored simulation cartesian states. 
    cartesianStates = np.array([])

    def __init__(
            self, 
            name: str,
            mass: float, 
            # semiMajorAxis, eccentricity, inclination, argOfPeriapsis,
            # longOfAscending, trueAnom 
            keplerianElems: NDArray):
        
        self.name = name
        self.mass = mass
        self.keplerianElems = keplerianElems

    def set_distance_from_co_orbiting(self, distance):
        """
        Adds the necessary true anomaly spacing to ensure distance to a co-orbiting
        spacecraft. Assumes co-planar orbit for the co-orbiting spacecraft and
        that said spacecraft has a true anomaly of zero as an initial state. 
        Derivation presented in readme file. 
        Args:
            distance (float): desired distance in meters to the co-orbiting spacecraft. 
        """
        # Auxiliary phi variable. 
        phiAuxiliary =  (
            distance**2 / ( self.keplerianElems[0] * (1 - self.keplerianElems[1]**2) )**2 
            - ( 1 / ( 1 + self.keplerianElems[1] ) )**2 )

        # Sets up elements of required for solving quadratic equation.
        c = ( 1 + self.keplerianElems[1] ) * ( 1 - phiAuxiliary )
        b = -2 - phiAuxiliary*( 2*self.keplerianElems[1] + 2*self.keplerianElems[1]**2 )
        a = -2*self.keplerianElems[1] - phiAuxiliary*( self.keplerianElems[1]**2 + self.keplerianElems[1]**3 )

        # Solve quadratic. 
        quadraticResults = np.roots( [ a, b, c ] )
        # Filters results that are valid for x = cos(theta). 
        validQuadraticResults = quadraticResults[ abs(quadraticResults) < 1 ]
        # Checks if list of valid results is empty. 
        if validQuadraticResults.size == 0:
            raise ValueError(
                f"Quadratic solve did not output valid results: {quadraticResults}"
            )

        # Arccos of results.
        trueAnomalyResults = np.arccos( validQuadraticResults )[0]

        # Adds to initial true anomaly 
        # (Assumed same as reference spacecraft before this function is called)
        self.keplerianElems[5] = trueAnomalyResults

    def save_cartesian_state(self, cartesianStates: NDArray) -> None:

        self.cartesianStates = cartesianStates

    def find_cartesian_state(self, stateEpoch: float) -> NDArray:

        # Checks whether given epoch is within the limits of the saved states. 
        if (stateEpoch < self.cartesianStates[0,0] or 
            stateEpoch > self.cartesianStates[-1,0]):
            # If outside limits, returns error. 
            raise ValueError(
                f"Given epoch outside of stored propagation.\n" +
                f"Given {stateEpoch}, start: {self.cartesianStates[0,0]}, end:{self.cartesianStates[-1,0]}"
            )
        else: 
            # Checks where first column (Epoch) matches requested epoch. 
            stateIndex = np.where(self.cartesianStates[:,0] == stateEpoch)[0]

            # Checks if epoch doesn't match any stored one exactly. 
            if stateIndex.size == 0: 
                ### If so, linearly interpolates between two nearest epochs. 

                # Extracts nearest smaller-than values index. 
                nearestSmallerThanIndex = (np.abs(np.where(
                    (self.cartesianStates[:,0] - stateEpoch) < 0))).argmin()

                # Linearly interpolates between nearest states. 
                cartesianState = linear_interpolation(
                    yValues1= self.cartesianStates[nearestSmallerThanIndex, 1:],
                    yValues2= self.cartesianStates[nearestSmallerThanIndex+1, 1:],
                    xValues= self.cartesianStates[nearestSmallerThanIndex:nearestSmallerThanIndex+2, 0],
                    xInterpol= stateEpoch
                )

            else: 
                ### Else, returns matching state. 
                cartesianState = self.cartesianStates[stateIndex, 1:].flatten()

        return cartesianState

    def print_initial_state(self) -> None:

        print(f"{self.name} initial state: {self.cartesianStates[0,:]}")

### Ground station class. 
class groundStation (body):
    def __init__(
        self, 
        name: str,
        position: list,
        parentBody: str
        ):

        self.name = name
        self.position = position
        self.parentBody = parentBody

    def ground_station_settings(self) -> GroundStationSettings:
        """
        Returns settings for the given ground station.
        Args:
            None
        Returns:
            groundStationSettings (GroundStationSettings) : Object containing ground station settings.
        """
        return dynamics.environment_setup.ground_station.basic_station(
            self.name,
            self.position
        )

        
        