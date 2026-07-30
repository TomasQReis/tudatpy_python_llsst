### Imports for self-made functions
from environment.low_fidelity import *
from obs_models.ll_sst import *
from vehicles.roci_ab import *

### External library imports.
import numpy as np

### Tudat imports
from tudatpy.util import result2array




if __name__ == "__main__":
    # Simulation start and end dates. 
    # Given as [Year, Month, Day]
    simStartDate    = [2026, 7, 30]
    simEndDate      = [2026, 8, 1]

    # Load SPICE kernels and return J2000 formatted epochs. 
    simStartEpoch, simEndEpoch = load_spice( 
        startEpoch= simStartDate, endEpoch= simEndDate 
        )

    # Set up environment bodies. 
    simulationBodies = environment_bodies_low_fidelity( 
        spacecrafts= spacecraftDicts )

    # Set up propagator settings. 
    propagatorSettings = environment_prop_settings_low_fidelity(
        spacecrafts= spacecraftDicts,
        bodies= simulationBodies,
        simStartEpoch= simStartEpoch,
        simEndEpoch= simEndEpoch,
        timeStep= 10.0
    )

    # Propagate orbit. 
    stateHistory = environment_propagate_low_fidelity(
        bodies= simulationBodies,
        propagationSettings= propagatorSettings
    )

    