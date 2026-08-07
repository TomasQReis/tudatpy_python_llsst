### Imports for self-made functions 
from auxiliary.math_functions import *

### External library imports.
import numpy as np
from numpy.typing import NDArray

### Spacecraft class.
class spacecraft:
    # Stored simulation cartesian states. 
    cartesianStates = np.array([])

    def __init__(
            self, 
            name: str,
            mass: float, 
            keplerianElems: NDArray):
        
        self.name = name
        self.mass = mass
        self.keplerianElems = keplerianElems

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




