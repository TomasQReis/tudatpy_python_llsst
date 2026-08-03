### Imports for self-made functions
from environment.low_fidelity import *
from environment.common_functions import *
from obs_models.ll_sst import *
from vehicles.roci_ab import *
from visualization.plotting import *

### External library imports.
import numpy as np

### Tudat imports
from tudatpy.util import result2array
from tudatpy import dynamics
from tudatpy.estimation.estimation_analysis import Estimator

if __name__ == "__main__":

    # Simulation start and end dates. 
    # Given as [Year, Month, Day]
    simStartDate    = [2026, 7, 31]
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
        timeStep= 10.0,
        sHMoon= True
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
    observationModelSimulator, observationModelSettings = observation_model_simulator_owr(
        owrLinkDefinition= observationLinkDefinition,
        bodies= simulationBodies
    )

    # Create set of observation times. 
    observationsStep = 10.0
    observationTimes = np.arange( simStartEpoch+observationsStep, 
                                step= observationsStep,
                                stop= simEndEpoch)

    ### -----------------------------------------------------------------------
    ### TODO: Put this into its own observations file

    ### Same physical environment as simulated observations.
    parameterSettings = dynamics.parameters_setup.initial_states( 
        propagatorSettings, simulationBodies )
    
    
    estimator = Estimator(
        bodies= simulationBodies,
        estimated_parameters= dynamics.parameters_setup.create_parameter_set(
            parameter_settings= parameterSettings,
            bodies= simulationBodies),
        observation_settings= observationModelSettings,
        propagator_settings= propagatorSettings
    )

    # Simulate observations. 
    simulatedObservations, simulatedObservationsDependentVars = simulate_observations_owr(
        observationTimes= observationTimes,
        owrLinkDefinition= observationLinkDefinition,
        owrObservationSimulator= estimator.observation_simulators,
        bodies= simulationBodies
    )

    # Estimation settings. 
    estimationSettings = estimation.estimation_analysis.EstimationInput(
        observations_and_times= simulatedObservations
    )

    # Perform initial state estimation.
    estimationOutput = estimator.perform_estimation(
        estimation_input= estimationSettings
    )
    

    # Extract simulated observation data. 
    rangeParser = estimation.observations.observations_processing.observation_parser(
        estimation.observable_models_setup.model_settings.one_way_range_type
    )
    simulatedObservationValues, simulatedObservationTimes = simulatedObservations.get_concatenated_observations_and_times(
        rangeParser
    )

    ### -----------------------------------------------------------------------
    dependentVarsHistoryArray = result2array(dependentVarsHistory)
    stateHistoryArr = result2array(stateHistory)

    # Print initial state estimate vs reality
    if printInitialState := False:
        print("Initial position: ==========")
        print(f"Estimated:{estimationOutput.final_parameters[:3]}") 
        print(f"Reality:{stateHistoryArr[0,1:4]}") 
        print("Initial velocity: ==========")
        print(f"Estimated:{estimationOutput.final_parameters[3:6]}") 
        print(f"Reality:{stateHistoryArr[0,4:7]}") 

    # Relative distance plot. 
    if plotRange := False:
        
        # Assembles times dictionary
        epochDict = {
            "Relative Distance": dependentVarsHistoryArray[:,0] - simStartEpoch,
            "Range Measurement": np.array(observationTimes) - simStartEpoch
        }
        # Assembles data dictionary for use in plotting. 
        dataDict = {
            "Relative Distance": dependentVarsHistoryArray[:,1],
            "Range Measurement": simulatedObservationValues
        }

        generalized_plot_2d(
            yVariables= dataDict,
            xVariables= epochDict,
            title= "Relative Distance Plot",
            xAxisLabel= "Time since start of Simulation [s]",
            yAxisLabel= "Relative Distance [m]"
        )

    # Plots the difference between "real" range and simulated observations. 
    if plotRangeDifference := False :
        # Check where epochs match between propagation and observations.
        matchedIndexes = np.where( np.isin( 
            dependentVarsHistoryArray[:,0], np.array(simulatedObservationTimes) ) )[0]

        # Extract propagation range for matching indices
        propRange = dependentVarsHistoryArray[matchedIndexes,1]

        # Calculate difference.
        rangeDifference = abs(propRange - simulatedObservationValues)

        # Data and epoch dictionaries 
        yVariables = { "Range Difference": rangeDifference,
                    }
        xVariables = { "Range Difference": np.array(simulatedObservationTimes) - simStartEpoch
                    }

        # Plots
        generalized_plot_2d(
            yVariables= yVariables,
            xVariables= xVariables,
            title= "Isolated Propagation and Estimator Propagation Range Difference",
            xAxisLabel= "Time since start of propagation [s]",
            yAxisLabel= "Range Difference [m]"
        )

    # 