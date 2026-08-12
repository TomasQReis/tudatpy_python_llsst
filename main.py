### Imports for self-made functions
from environment.low_fidelity import *
from environment.common_functions import *
from obs_models.ll_sst import *
from bodies.common import *
from bodies.roci_ab import *
from bodies.ground_stations import *
from visualization.plotting import *

### External library imports.
import numpy as np
from pathlib import Path

### Tudat imports
from tudatpy.util import result2array
from tudatpy import dynamics
from tudatpy.estimation.estimation_analysis import Estimator

### LIST OF TODO's ###
# TODO: Implement noise and bias in low_fidelity.
# TODO: Test functionality with other celestial bodies. 
# TODO: Function for converting an altitude into a basic set of kepler 
# elements for a given planet. (Args: Altitude and Planet)

if __name__ == "__main__":

    # Data directory. 
    resultsDir = "data/results/"

    ### -----------------------------------------------------------------------
    ### Propagation of "reality".
    ### -----------------------------------------------------------------------

    if propagateReality:= True:
        # Propagation start and end dates. 
        # Given as [Year, Month, Day]
        simStartDate    = [2026, 7, 30]
        simEndDate      = [2026, 8, 2]

        # Propagation time step size. 
        propTimeStep = 10.0

        # Load SPICE kernels and return J2000 formatted epochs. 
        simStartEpoch, simEndEpoch = load_spice( 
            startEpoch= simStartDate, endEpoch= simEndDate 
            )

        # Choose list of spacecraft for simulation. 
        spacecrafts = [ rociA, rociB ]
        # Choose list of ground stations for simulation.
        groundStations = [ grazStation ]

        # Set up true environment bodies. 
        simulationBodies = environment_bodies_low_fidelity_true_model( 
            spacecrafts= spacecrafts,
            groundStations= groundStations
        )

        # Set up propagator settings. 
        propagatorSettings = environment_prop_settings_low_fidelity(
            spacecrafts= spacecrafts,
            bodies= simulationBodies,
            simStartEpoch= simStartEpoch,
            simEndEpoch= simEndEpoch,
            timeStep= propTimeStep,
            trueModel= True,
            harmonicCoeffOrder= 5,
            keepEnvironment= True
        )

        # Propagate orbit. 
        stateHistory, dependentVarsHistory = environment_propagate_low_fidelity(
            bodies= simulationBodies,
            propagationSettings= propagatorSettings
        )

        # Convert reality propagation output into NDArrays. 
        dependentVarsHistoryArray = result2array(dependentVarsHistory)
        stateHistoryArr = result2array(stateHistory)

        # Saves cartesian states to spacecraft. 
        rociA.save_cartesian_state( cartesianStates= stateHistoryArr[:,:7] )
        rociB.save_cartesian_state( cartesianStates= np.hstack([stateHistoryArr[:,0:1], stateHistoryArr[:,7:]]) )
        
    ### -----------------------------------------------------------------------
    ### Simulating observations.
    ### -----------------------------------------------------------------------

    if simulateObservations:= True:
        # Create observation times. 
        observStartDate    = [2026, 7, 31]
        observEndDate      = [2026, 8, 1]

        # Load SPICE kernels and return J2000 formatted epochs. 
        observationStartEpoch, observationEndEpoch = convert_time( 
            startEpoch= observStartDate, endEpoch= observEndDate 
            )

        # Create set of observation times. 
        observationsStep = 30.0
        observationTimes = np.arange( observationStartEpoch, 
                                    step= observationsStep,
                                    stop= observationEndEpoch)

        # Define noise amplitude for observations. 
        noiseAmplitude = 0.5

        # Define transmitters and receivers for one way range observations.
        # Order of elements matters. Receivers[0] corresponds to transmitters[0].
        owrReceivers = [ rociB, rociA, grazStation, grazStation ]
        owrTransmitters = [ rociA, rociB, rociA, rociB ]

        # Create observation links.
        owrObservationType, owrObservationLinkDefinitions = link_creation_one_way(
            transmitters= owrTransmitters,
            receivers= owrReceivers
        )

        # Create observation model simulator.
        observationModelSimulator, observationModelSettings = observation_model_simulator_owr(
            owrLinkDefinitions= owrObservationLinkDefinitions,
            bodies= simulationBodies,
        )

        # Dictionary of observation types and their respective link definitions. 
        linkEndsPerObservable = {
            owrObservationType: owrObservationLinkDefinitions
        }

        # Simulate observations. 
        simulatedObservationsNoisy = simulate_observations_owr(
            observationTimes= observationTimes.tolist(),
            linkEndsPerObservatble= linkEndsPerObservable,
            owrObservationSimulator= observationModelSimulator,
            bodies= simulationBodies,
            noiseAmplitude= noiseAmplitude
        )

    
        # Simulate clean observations. 
        simulatedObservationsClean = simulate_observations_owr(
            observationTimes= observationTimes.tolist(),
            linkEndsPerObservatble= linkEndsPerObservable,
            owrObservationSimulator= observationModelSimulator,
            bodies= simulationBodies,
            noiseAmplitude= 0.0
        )

        # Extract simulated observation data. 
        simulatedRociObservationsClean, simulatedObservationTimes = extract_data_observations_owr(
            observationCollection= simulatedObservationsClean,
            transmitter= rociA
        )
        simulatedGrazObservationsClean, simulatedObservationTimes = extract_data_observations_owr(
            observationCollection= simulatedObservationsClean,
            transmitter= grazStation
        )

    ### -----------------------------------------------------------------------
    ### Estimating parameters.
    ### -----------------------------------------------------------------------

    # Estimates file name.
    estimationFile = "estimates.txt"

    # Sets up maximum order of estimated/read SH parameters. 
    estimationMaxOrder = 5

    # Sets whether the estimation process will be conducted...
    # and new results saved. 
    newEstimates = False

    if not Path(resultsDir + estimationFile).exists() or newEstimates:
        ### Estimation Parameters. 
        # Sets up estimation step time. 
        estimationStep = observationsStep
        
        # Estimation maximum number of iterations. 
        estimationMaxIterations = 10

        # Initial State offset. 
        stateOffset = np.array([10,10,10,0.1,0.1,0.1])
        # SH Coefficient offset. 
        coefficientOffset = 1e-5

        # Extract cosine and sine coefficients from reference model. 
        cosineCoefficientsReference, sineCoefficientsReference, referenceRadius, graviationalParameterReference = return_sh_coefficients(
            bodyName= "Moon",
            systemOfBodies= simulationBodies,
            maxDegree= estimationMaxOrder,
            maxOrder= estimationMaxOrder
        )

        ### Estimation creation. 
        # Set up estimation environment bodies. 
        estimationBodies = environment_bodies_low_fidelity_estimation_model(
            spacecrafts= spacecrafts,
            groundStations= groundStations,
            cosineCoefficients= cosineCoefficientsReference,
            sineCoefficients= sineCoefficientsReference,
            gravitationalParameter= graviationalParameterReference,
            referenceRadius= referenceRadius,
            coefficientOffset = coefficientOffset
        )

        # Extract cosine and sine coefficients from forecast model. 
        cosineCoefficientsForecast, sineCoefficientsForecast, _, _ = return_sh_coefficients(
            bodyName= "Moon",
            systemOfBodies= estimationBodies,
            maxDegree= estimationMaxOrder,
            maxOrder= estimationMaxOrder
        )

        # Set up estimation propagation settings. 
        estimationPropSettings = environment_prop_settings_low_fidelity(
            spacecrafts= spacecrafts,
            bodies= estimationBodies,
            simStartEpoch= observationStartEpoch,
            simEndEpoch= observationEndEpoch,
            timeStep= estimationStep,
            trueModel= False,
            harmonicCoeffOrder= estimationMaxOrder,
            stateOffset = stateOffset,
        )

        # Create observation model for estimator.
        observationModelSimulatorEstimator, observationModelSettingsEstimator = observation_model_simulator_owr(
            owrLinkDefinitions= owrObservationLinkDefinitions,
            bodies= estimationBodies
        )

        # Set up desired estimation parameters.
        parameterSettings = dynamics.parameters_setup.initial_states( 
            estimationPropSettings, estimationBodies 
            )
        parameterSettings.append( 
            dynamics.parameters_setup.spherical_harmonics_c_coefficients(
                body= "Moon",
                maximum_degree= estimationMaxOrder,
                maximum_order= estimationMaxOrder,
                minimum_degree= 2,
                minimum_order= 0
            )
        )
        parameterSettings.append(
            dynamics.parameters_setup.spherical_harmonics_s_coefficients(
                body= "Moon",
                maximum_degree= estimationMaxOrder,
                maximum_order= estimationMaxOrder,
                minimum_degree= 2,
                minimum_order= 1
            )
        )

        # Create parameters set. 
        parameterSet = dynamics.parameters_setup.create_parameter_set(
            parameter_settings= parameterSettings,
            bodies= estimationBodies
            )
        
        # Creating estimator. 
        estimator = Estimator(
            bodies= estimationBodies,
            estimated_parameters= parameterSet,
            observation_settings= observationModelSettings,
            propagator_settings= estimationPropSettings,
            integrate_on_creation= False
        )

        # Estimation settings. 
        estimationSettings = estimation.estimation_analysis.EstimationInput(
            observations_and_times= simulatedObservationsClean,
            convergence_checker= estimation.estimation_analysis.estimation_convergence_checker(
                maximum_iterations= estimationMaxIterations
            )
        )
                    
        # Perform parameter estimation.
        estimationOutput = estimator.perform_estimation(
            estimation_input= estimationSettings
        )
        
        # Save farameters to file. 
        finalParameters = estimationOutput.final_parameters
        np.savetxt( 
            resultsDir + estimationFile, 
            finalParameters
            )
                
    else:
        # Use existing parameters. 
        finalParameters = np.loadtxt(
            resultsDir + estimationFile
            )
                
    ### -----------------------------------------------------------------------
    ### Data processing and visualization.
    ### -----------------------------------------------------------------------

    if coeffDifference := False:
        # Comparison filename.
        comparisonFile = "processed_results.txt"

        # Compares coefficients. 
        print()
        print("===== SH Coefficient Estimation Results =====")

        # Flattens the non-zero cosine coefficients from the parameter estimation. 
        flattenedCosineCoefficients = cosineCoefficientsReference[1:,0:].flatten()[cosineCoefficientsReference[1:,0:].flatten() != 0]
        flattenedSineCoefficients = sineCoefficientsReference[1:,0:].flatten()[sineCoefficientsReference[1:,0:].flatten() != 0]

        flattenedReferenceCoefficients = np.append(flattenedCosineCoefficients, flattenedSineCoefficients)

        # Extracts estimated coefficients. 
        estimatedCoefficients = finalParameters[12:]

        # Absolute error between mismatched coefficients:
        # Degree >= 2 and Order >= 0 ( >= 1 for sine coefficients )
        absoluteError = abs(estimatedCoefficients - flattenedReferenceCoefficients)

        # Relative Error. 
        relativeError = absoluteError / flattenedReferenceCoefficients

        print("Absolute Error: -----")
        print(absoluteError)

        print("Relative Error: -----")
        print(relativeError)

        # Creates coefficient indices. 
        degreeRange = np.arange(2, estimationMaxOrder +1)
        degrees = np.repeat(degreeRange, degreeRange + 1).astype(int)
        orders = np.concatenate([np.arange(d + 1) for d in degreeRange]).astype(int)

        # Splits estimated coefficients into cosine and sine coefficients. 
        estimatedCosineCoefficients = estimatedCoefficients[:np.size(degrees)]
        reducedEstimatedSineCoefficients = estimatedCoefficients[np.size(degrees):]

        # Same split for errors. 
        cosineCoefficientAbsoluteErrors = absoluteError[:np.size(degrees)]
        sineCoefficientReducedAbsoluteErrors = absoluteError[np.size(degrees):]

        cosineCoefficientRelativeErrors = relativeError[:np.size(degrees)]
        sineCoefficientReducedRelativeErrors = relativeError[np.size(degrees):]

        # Mask for indices where order is zero. 
        zeroOrderMask = np.ones( np.size( degrees ), dtype= bool )
        zeroOrderMask[ np.where( orders == 0 )[0] ] = False

        estimatedSineCoefficients = np.zeros( np.size( degrees ) )
        sineCoefficientAbsoluteErrors = np.zeros( np.size( degrees ) )
        sineCoefficientRelativeErrors = np.zeros( np.size( degrees ) )

        # Inserts zeros into order 0 sine coefficients. 
        estimatedSineCoefficients[zeroOrderMask] = reducedEstimatedSineCoefficients
        sineCoefficientAbsoluteErrors[zeroOrderMask] = sineCoefficientReducedAbsoluteErrors
        sineCoefficientRelativeErrors[zeroOrderMask] = sineCoefficientReducedRelativeErrors

        # Header. 
        header = "Degree - Order -    C    -    S    - Absolute Error (C - S) - Relative Error (C - S)"

        # Column stacks.
        saveData = np.column_stack([
            degrees, orders, estimatedCosineCoefficients, estimatedSineCoefficients, 
            cosineCoefficientAbsoluteErrors, sineCoefficientAbsoluteErrors,
            cosineCoefficientRelativeErrors, sineCoefficientRelativeErrors])

        # Save indexed values. 
        np.savetxt( resultsDir + comparisonFile, saveData, header= header,
                    fmt= ["%2i", "%2i", "% .10e", "% .10e", "% .10e", 
                          "% .10e", "% .10e", "% .10e"],
                    delimiter= ",")

    # Print initial state estimate vs reality
    if printInitialState := False:
        # Extract final initial state estimates.
        finalStates = finalParameters[:12]

        # Compares initial states. 
        print("========== Difference in state ==========")
        print("Roci A: ")
        print(f":{np.abs(finalStates[:6] - rociA.find_cartesian_state( stateEpoch= observationStartEpoch ))}") 
        print("Roci B: ")
        print(f":{np.abs(finalStates[6:12] - rociB.find_cartesian_state( stateEpoch= observationStartEpoch ))}") 

    # Relative distance plot. 
    if plotRange := False:
        
        # Assembles times dictionary
        epochDict = {
            "Relative Distance": dependentVarsHistoryArray[:,0] - simStartEpoch,
            "Range Measurement": np.array(observationTimes) - simStartEpoch,
        }
        # Assembles data dictionary for use in plotting. 
        dataDict = {
            "Relative Distance": dependentVarsHistoryArray[:,1],
            "Range Measurement": simulatedRociObservationsClean,
        }

        generalized_plot_2d(
            yVariables= dataDict,
            xVariables= epochDict,
            title= "Relative Distance Plot",
            xAxisLabel= "Time since start of Simulation [s]",
            yAxisLabel= "Relative Distance [m]"
        )

    # Observations plot.
    if plotObservations := False:
        plotTitle = "Observations Plot"
         
        plot1Name = "ll-SST Range rociA"
        plot2Name = "Graz Station Range"

        plot3Name = "True rociA-Earth Distance"

        # Check where epochs match between propagation and observations.
        matchedIndexes = np.where( np.isin( 
            dependentVarsHistoryArray[:,0], np.array(observationTimes) ) )[0]
        
        # Assembles times dictionary
        epochDict = {
            plot1Name: np.array(observationTimes) - simStartEpoch,
            plot2Name: np.array(observationTimes) - simStartEpoch,
            plot3Name: dependentVarsHistoryArray[matchedIndexes,0] - simStartEpoch
        }
        # Assembles data dictionary for use in plotting. 
        dataDict = {
            plot1Name: simulatedRociObservationsClean,
            plot2Name: simulatedGrazObservationsClean/1e3,
            plot3Name: dependentVarsHistoryArray[matchedIndexes,2]/1e3
        }

        generalized_plot_2d(
            yVariables= dataDict,
            xVariables= epochDict,
            title= plotTitle,
            xAxisLabel= "Time since start of Simulation [s]",
            yAxisLabel= "Relative Distance [m]",
            secondaryAxisKeys= [ plot2Name, plot3Name ],
            secondaryAxisLabel= "Relative Distance [km]"
        )

    # Plots the difference between "real" range and simulated observations. 
    if plotRangeDifference := False :
        # Check where epochs match between propagation and observations.
        matchedIndexes = np.where( np.isin( 
            dependentVarsHistoryArray[:,0], np.array(simulatedObservationTimes) ) )[0]

        # Extract propagation range for matching indices
        propRange = dependentVarsHistoryArray[matchedIndexes,1]

        # Calculate difference.
        rangeDifference = abs(propRange - simulatedObservationValuesNoisy)

        # Data and epoch dictionaries 
        yVariables = { "Range Difference": rangeDifference}
        xVariables = { "Range Difference": np.array(simulatedObservationTimes) - simStartEpoch}
        # Plots
        generalized_plot_2d(
            yVariables= yVariables,
            xVariables= xVariables,
            title= "Range Difference: Real vs Simulated Observations",
            xAxisLabel= "Time since start of propagation [s]",
            yAxisLabel= "Range [m]"
        )

    # Plot clean vs noisy observations. 
    if plotRangeDifference := False :
        # Check where epochs match between propagation and observations.
        matchedIndexes = np.where( np.isin( 
            dependentVarsHistoryArray[:,0], np.array(simulatedObservationTimes) ) )[0]

        # Extract propagation range for matching indices
        propRange = dependentVarsHistoryArray[matchedIndexes,1]

        # Calculate difference.
        rangeDifference = abs(propRange - simulatedObservationValuesNoisy)

        # Data and epoch dictionaries 
        yVariables = { f"Range Observations With Noise Amplitude {noiseAmplitude}": simulatedObservationValuesNoisy,
                        "Range Observations Ideal": simulatedObservationValuesClean
                    }
        xVariables = { f"Range Observations With Noise Amplitude {noiseAmplitude}": np.array(simulatedObservationTimes) - simStartEpoch,
                        "Range Observations Ideal": np.array(simulatedObservationTimes) - simStartEpoch
                    }

        # Plots
        generalized_plot_2d(
            yVariables= yVariables,
            xVariables= xVariables,
            title= "Simulated range observations",
            xAxisLabel= "Time since start of propagation [s]",
            yAxisLabel= "Range [m]"
        )

    # Plot trajectories. 
    if plotTrajectories := False:

        trajectory_plot_3d(
            spacecrafts= spacecrafts,
            stateHistoryArray= stateHistoryArr,
            title= "Roci A and B trajectories."
        )