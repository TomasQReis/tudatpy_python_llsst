### Tudat imports. 
from tudatpy import dynamics
from tudatpy import estimation

### Self-made imports. 
from environment.environment import environmentClass 
from bodies.roci_ab import rociA, rociB

# TODO: Would be nice to have these in the estimator class or part of their own class. 
# Just make them modular and easy to access...
from obs_models.ll_sst import link_creation_one_way, observation_model_simulator_owr,\
    simulate_observations_owr, extract_data_observations_owr

### External imports.
import numpy as np


class estimator ():
    def __init__(
        self,
        referenceEnvironment: environmentClass,
        estimationEnvironment: environmentClass,

        estimationArcLength: float= 0.0,      # TODO: Generalize

        referenceHarmonicsDegree: int= 5,
        estimationHarmonicsDegree: int= 5
    ) -> None:

        self.referenceEnvironment   = referenceEnvironment
        self.estimationEnvironment  = estimationEnvironment

        self.estimationArcLength    = estimationArcLength

        self.referenceHarmonicsDegree = referenceHarmonicsDegree
        self.estimationHarmonicsDegree = estimationHarmonicsDegree


    def propagate_reality ( self ):

        ### Propagate reality 
        self.referenceEnvironment.make_propagation_settings(
            harmonicsDegree= self.referenceHarmonicsDegree,
            arcTimeLength= self.estimationArcLength,
            keepEnvironment= True, 
            skipArcCheck= True      # TODO: Remove after testing. 
        )

        # Save propagation results. 
        self.referencePropagationResults = self.referenceEnvironment.propagate()

    def make_observations ( self ):
        ### Propagate reference. 
        self.propagate_reality()

        ### Simulate observations. 
        # Observation epoch. 
        # TODO: Generalize epoch margin for light-time. 
        observationEpochMargin = 12 * 60**2
        observationEpochStart = self.referenceEnvironment.simStartEpoch + observationEpochMargin
        observationEpochEnd = self.referenceEnvironment.simEndEpoch - observationEpochMargin

        observationEpochs = np.arange( observationEpochStart,                       # type: ignore
                                      step= self.referenceEnvironment.timeStep ,    # type: ignore
                                      stop= observationEpochEnd )                   # type: ignore

        # Link definition. One way range. 
        # TODO: Make a modular way for selecting observation pairs. 
        receivers = [self.referenceEnvironment.spacecrafts[0],
                     self.referenceEnvironment.spacecrafts[1]]
        transmitters = [self.referenceEnvironment.groundStations[0], 
                        self.referenceEnvironment.spacecrafts[0]]

        # Create observation links.
        self.observationType, self.observationLinkDefintions = link_creation_one_way(
            transmitters= transmitters,
            receivers= receivers
        )

        # Create observation model simulator.
        self.observationSimulator, self.observationSettings = observation_model_simulator_owr(
            owrLinkDefinitions= self.observationLinkDefintions,
            bodies= self.referenceEnvironment.systemOfBodies
        )

        # Dictionary of observation types and their respective link definitions. 
        linkEndsPerObservable = {
            self.observationType: self.observationLinkDefintions
        }

        # TODO: Generalize noise input for observations. 
        noiseAmplitude = 0.0

        # Simulate observations.
        self.simulatedObservations = simulate_observations_owr(
            observationTimes= observationEpochs.tolist(),
            linkEndsPerObservatble= linkEndsPerObservable,
            owrObservationSimulator= self.observationSimulator,
            bodies= self.referenceEnvironment.systemOfBodies,
            noiseAmplitude= noiseAmplitude
        )

        ### Save observations. 
        # TODO: Generalize for all transmitters. 
        self.observations, self.observationTimes = extract_data_observations_owr(
            observationCollection= self.simulatedObservations,
            transmitter= self.referenceEnvironment.spacecrafts[0]
        )

    def make_estimation ( 
            self,
            maximumIterations: int= 10 ):
        
        ### Estimation environment settings. 
        self.estimationEnvironment.make_propagation_settings(
            harmonicsDegree= self.estimationHarmonicsDegree,
            arcTimeLength= self.estimationArcLength,
            skipArcCheck= True      # TODO: Remove when done testing. 
        )

        ### Estimation parameters.
        # Initial state.
        estimationParameters = dynamics.parameters_setup.initial_states(
            propagator_settings= self.estimationEnvironment.arcPropagationSettings,
            arc_initial_times= self.estimationEnvironment.arcInitialEpochs,
            bodies= self.estimationEnvironment.systemOfBodies
        )

        # Harmonic coefficients. 
        estimationParameters.append( dynamics.parameters_setup.spherical_harmonics_c_coefficients (
            body= self.estimationEnvironment.frameOriginBody,
            maximum_degree= self.estimationHarmonicsDegree,
            maximum_order= self.estimationHarmonicsDegree,
            minimum_degree= 2,
            minimum_order= 0 
        ) )
        estimationParameters.append( dynamics.parameters_setup.spherical_harmonics_s_coefficients (
            body= self.estimationEnvironment.frameOriginBody,
            maximum_degree= self.estimationHarmonicsDegree,
            maximum_order= self.estimationHarmonicsDegree,
            minimum_degree= 2,
            minimum_order= 1 
        ) )

        print("Check1")

        ### Create parameter set. 
        parameterSet = dynamics.parameters_setup.create_parameter_set(
            parameter_settings= estimationParameters,
            bodies= self.estimationEnvironment.systemOfBodies
        )

        print("Check2")

        ### Create estimator.
        estimator = estimation.estimation_analysis.Estimator(
            bodies= self.estimationEnvironment.systemOfBodies,
            estimated_parameters= parameterSet,
            observation_settings= self.observationSettings,
            propagator_settings= self.estimationEnvironment.arcPropagationSettings,
            integrate_on_creation= False
        )

        print("Check3")

        # Estimator settings.
        estimatorSettings = estimation.estimation_analysis.EstimationInput(
            observations_and_times= self.simulatedObservations,
            convergence_checker= estimation.estimation_analysis.estimation_convergence_checker(
                maximum_iterations= maximumIterations
            )
        )

        print("Check4")

        ### Perform estimation.
        self.estimationOutput = estimator.perform_estimation(
            estimation_input= estimatorSettings
        )


