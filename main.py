### Imports for self-made functions
from environment.low_fidelity import *
from obs_models.ll_sst import *
from vehicles.roci_ab import *
from visualization.plotting import *

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

    # Choose list of spacecraft for simulation. 
    spacecraftDicts = rociABList

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
    stateHistory, dependentVarsHistory = environment_propagate_low_fidelity(
        bodies= simulationBodies,
        propagationSettings= propagatorSettings
    )

    # Create observation links.
    observationLinkDefinition = link_creation_owr(
        transmitterDict= spacecraftDicts[0],
        receiverDict= spacecraftDicts[1]
    )

    # Create observation model simulator.
    observationModelSimulator = observation_model_simulator_owr(
        owrLinkDefinition= observationLinkDefinition,
        bodies= simulationBodies
    )


    if plot1 := False:
        # Relative distance plot. 
        dependentVarsHistoryArray = result2array(dependentVarsHistory)
        # Makes times into time since start of propagation. 
        times = dependentVarsHistoryArray[:,0] - dependentVarsHistoryArray[0,0]
        # Assembles data dictionary for use in plotting. 
        dataDict = {
            "Relative Distance": dependentVarsHistoryArray[:,1]
        }

        generalized_plot_2d(
            yVariables= dataDict,
            xVariables= times,
            title= "Relative Distance Plot",
            xAxisLabel= "Time since start of Simulation [s]",
            yAxisLabel= "Relative Distance [m]"
        )


    