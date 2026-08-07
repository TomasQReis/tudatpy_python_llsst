### Imports for self-made functions
from environment.low_fidelity import *
from environment.common_functions import *
from obs_models.ll_sst import *
from vehicles.vehicles_common import *
from vehicles.roci_ab import *
from visualization.plotting import *

### External library imports.
import numpy as np

### Tudat imports
from tudatpy.util import result2array
from tudatpy import dynamics
from tudatpy.estimation.estimation_analysis import Estimator

if __name__ == "__main__":

    # Data directory. 
    dataDir = "data/"

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
        spacecrafts = rociList

        # Set up true environment bodies. 
        simulationBodies = environment_bodies_low_fidelity_true_model( 
            spacecrafts= spacecrafts 
        )

        # Set up propagator settings. 
        propagatorSettings = environment_prop_settings_low_fidelity(
            spacecrafts= spacecrafts,
            bodies= simulationBodies,
            simStartEpoch= simStartEpoch,
            simEndEpoch= simEndEpoch,
            timeStep= propTimeStep,
            trueModel= True,
            harmonicCoeffOrder= 0,
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

        # Extract cosine and sine coefficients from propagated model. 
        cosineCoefficients, sineCoefficients = return_sh_coefficients(
            bodyName= "Moon",
            systemOfBodies= simulationBodies,
            maxDegree= 5,
            maxOrder= 5
        )

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

        # Create observation links.
        observationLinkDefinition = link_creation_owr(
            transmitter= spacecrafts[0],
            receiver= spacecrafts[1]
        )

        # Create observation model simulator.
        observationModelSimulator, observationModelSettings = observation_model_simulator_owr(
            owrLinkDefinition= observationLinkDefinition,
            bodies= simulationBodies
        )
        # TODO: Need to add complete list of links here in order to include
        # the doppler and range observations. 

        # Simulate observations. 
        simulatedObservationsNoisy = simulate_observations_owr(
            observationTimes= observationTimes.tolist(),
            owrLinkDefinition= observationLinkDefinition,
            owrObservationSimulator= observationModelSimulator,
            bodies= simulationBodies,
            noiseAmplitude= noiseAmplitude
        )

        # Simulate clean observations. 
        simulatedObservationsClean = simulate_observations_owr(
            observationTimes= observationTimes.tolist(),
            owrLinkDefinition= observationLinkDefinition,
            owrObservationSimulator= observationModelSimulator,
            bodies= simulationBodies,
            noiseAmplitude= 0.0
        )

        # Extract simulated observation data. 
        simulatedObservationValuesNoisy, simulatedObservationTimes = extract_data_observations_owr(
            observationCollection= simulatedObservationsNoisy
        )
        simulatedObservationValuesClean, simulatedObservationTimes = extract_data_observations_owr(
            observationCollection= simulatedObservationsClean
        )

    ### -----------------------------------------------------------------------
    ### Estimating parameters.
    ### -----------------------------------------------------------------------

    if estimateParameters:= True:
        ### Estimation Parameters. 
        # Sets up estimation step time. 
        estimationStep = observationsStep
        # Sets up maximum order of estimated SH parameters. 
        estimationMaxOrder = 0
        # Estimation maximum number of iterations. 
        estimationMaxIterations = 20

        ### Estimation creation. 
        # Set up estimation environment bodies. 
        """ estimationBodies = environment_bodies_low_fidelity_estimation_model(
            spacecrafts= spacecrafts,
            harmonicCoeffOrder= estimationMaxOrder
        ) """
        estimationBodies = simulationBodies

        # Set up estimation propagation settings. 
        estimationPropSettings = environment_prop_settings_low_fidelity(
            spacecrafts= spacecrafts,
            bodies= estimationBodies,
            simStartEpoch= observationStartEpoch,
            simEndEpoch= observationEndEpoch,
            timeStep= observationsStep,
            trueModel= False,
            harmonicCoeffOrder= estimationMaxOrder,
            stateOffset = np.array([10,10,10,1,1,1])
        )

        # Create observation model for estimator.
        observationModelSimulatorEstimator, observationModelSettingsEstimator = observation_model_simulator_owr(
            owrLinkDefinition= observationLinkDefinition,
            bodies= estimationBodies
        )

        # Set up desired estimation parameters.
        parameterSettings = dynamics.parameters_setup.initial_states( 
            estimationPropSettings, estimationBodies 
            )
        """ parameterSettings.append( 
            dynamics.parameters_setup.spherical_harmonics_c_coefficients(
                body= "Moon",
                maximum_degree= estimationMaxOrder,
                maximum_order= estimationMaxOrder,
                minimum_degree= 1,
                minimum_order= 0
            )
        )
        parameterSettings.append(
            dynamics.parameters_setup.spherical_harmonics_s_coefficients(
                body= "Moon",
                maximum_degree= estimationMaxOrder,
                maximum_order= estimationMaxOrder,
                minimum_degree= 1,
                minimum_order= 1
            )
        ) """

        # Create parameters set. 
        parameterSet = dynamics.parameters_setup.create_parameter_set(
            parameter_settings= parameterSettings,
            bodies= estimationBodies
            )
        
        # Creating estimator. 
        estimator = Estimator(
            bodies= estimationBodies,
            estimated_parameters= parameterSet,
            observation_settings= observationModelSettingsEstimator,
            propagator_settings= estimationPropSettings,
            integrate_on_creation= True
        )

        # Estimation settings. 
        estimationSettings = estimation.estimation_analysis.EstimationInput(
            observations_and_times= simulatedObservationsClean,
            convergence_checker= estimation.estimation_analysis.estimation_convergence_checker(
                maximum_iterations= estimationMaxIterations
            )
        )
        estimationSettings.define_estimation_settings(
            reintegrate_variational_equations= False
        )

        # Perform parameter estimation.
        estimationOutput = estimator.perform_estimation(
            estimation_input= estimationSettings
        )

    ### -----------------------------------------------------------------------
    ### Data processing and visualization.
    ### -----------------------------------------------------------------------

    if coeffDifference := False:
        # Saved file title.
        fileTitle = f"estimated_coefficient_residuals_noiseAmp{noiseAmplitude}_sampleTime{observationsStep}.txt"

        # Flattens the non-zero cosine coefficients from the parameter estimation. 
        flattenedCosineCoefficients = cosineCoefficients[1:,0:].flatten()[cosineCoefficients[1:,0:].flatten() != 0]
        nonZeroEstimatedCosineCoefficients = estimationOutput.final_parameters[14:]

        # Adds zero coefficients for non-estimated higher degrees.
        nonEstimatedDegrees = np.size(flattenedCosineCoefficients) - np.size(nonZeroEstimatedCosineCoefficients)
        paddedEstimatedCosineCoefficients = np.pad(nonZeroEstimatedCosineCoefficients, (0, nonEstimatedDegrees), mode= "constant")

        # Prints the difference between the cosine coefficients used in the propagation (Reality)
        # and those estimated by the code. 
        print(f"Estimation residuals:{flattenedCosineCoefficients - paddedEstimatedCosineCoefficients}")
        np.savetxt(
            dataDir + fileTitle, 
            flattenedCosineCoefficients - paddedEstimatedCosineCoefficients
            )

    # Print initial state estimate vs reality
    if printInitialState := True:
        print("========== Difference in state ==========")
        print("Roci A: ")
        print(f":{np.abs(estimationOutput.final_parameters[:6] - rociA.find_cartesian_state( stateEpoch= observationStartEpoch ))}") 
        print("Roci B: ")
        print(f":{np.abs(estimationOutput.final_parameters[6:12] - rociB.find_cartesian_state( stateEpoch= observationStartEpoch ))}") 

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
            "Range Measurement": simulatedObservationValuesClean
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
