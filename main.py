### Imports for self-made functions
from environment.low_fidelity import *
from obs_models.ll_sst import *
from vehicles.roci_ab import *

### External library imports.
import numpy as np






if __name__ == "__main__":
    # Simulation start and end dates. 
    # Given as [Year, Month, Day]
    simStartDate    = [2026, 7, 30]
    simEndDate      = [2026, 8, 20]

    # Load SPICE kernels and return J2000 formatted epochs. 
    simStartEpoch, simEndEpoch = load_spice( 
        startEpoch= simStartDate, endEpoch= simEndDate 
        )

    # Set up environment bodies. 
    environment_bodies_low_fidelity( spacecrafts= spacecraftNames )

    

