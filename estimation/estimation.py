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
from numpy.typing import NDArray


class estimatorClass ():
    def __init__(
        self,
        environmentReal: environmentClass,
        environmentReference: environmentClass,

        arcLengthReal: float= 0.0,      # TODO: Generalize
        arcLengthReference: float= 0.0,

        harmonicsDegreeReal: int= 5,
        harmonicsDegreeReference: int= 5
    ) -> None:

        
        self.environmentReal   = environmentReal
        self.environmentReference  = environmentReference

        self.arcLengthReal     = arcLengthReal
        self.arcLengthReference    = arcLengthReference

        # NOTE: reference environment harmonics degree is currently unused. 
        self.harmonicsDegreeReal = harmonicsDegreeReal
        self.harmonicsDegreeReference = harmonicsDegreeReference

    def propagate_reality ( 
        self,
        initialStateOffset: NDArray= np.array([0,0,0,0,0,0]),
        ):

        ### Propagate reality 
        self.environmentReal.make_propagation_settings(
            arcTimeLength= self.arcLengthReal,
            keepEnvironment= True, 
            skipArcCheck= True      # TODO: Remove after testing. 
        )

        # Save propagation results. 
        self.referencePropagationResults = self.environmentReal.propagate()

        # Match initial state offset to number of spacecraft. 
        initialStateOffset = np.tile( initialStateOffset, 
                                        len( self.environmentReal.spacecrafts ) )
        
        # Offset reality initial states for initial guess values. 
        initialStatesArray = self.environmentReal.get_initial_states() + initialStateOffset

        ### Estimation environment settings. 
        self.environmentReference.make_propagation_settings(
            arcTimeLength= self.arcLengthReference,

            importInitialStates= True,
            initialStatesArray= initialStatesArray,

            skipArcCheck= True      # TODO: Remove when done testing. 
        )
    def make_observations ( 
        self,
        observationEpochMargin: float= 1*60**2,
        ):
        ### Simulate observations. 
        # Observation epoch. 
        observationEpochStart = self.environmentReal.simStartEpoch + observationEpochMargin
        observationEpochEnd = self.environmentReal.simEndEpoch - observationEpochMargin

        observationEpochs = np.arange( observationEpochStart,                       # type: ignore
                                      step= self.environmentReal.timeStep ,    # type: ignore
                                      stop= observationEpochEnd )                   # type: ignore

        # Link definition. One way range. 
        # TODO: Make a modular way for selecting observation pairs. 
        receivers = [self.environmentReal.spacecrafts[0],
                     self.environmentReal.spacecrafts[1]]
        transmitters = [self.environmentReal.groundStations[0], 
                        self.environmentReal.spacecrafts[0]]

        # Create observation links.
        self.observationType, self.observationLinkDefintions = link_creation_one_way(
            transmitters= transmitters,
            receivers= receivers
        )

        # Create observation model simulator.
        self.observationSimulator, self.observationSettings = observation_model_simulator_owr(
            owrLinkDefinitions= self.observationLinkDefintions,
            bodies= self.environmentReal.systemOfBodies
        )

        # Dictionary of observation types and their respective link definitions. 
        linkEndsPerObservable = {
            self.observationType: self.observationLinkDefintions
        }

        # TODO: Generalize noise input for observations. 
        noiseAmplitude = 0.0

        # Simulate observations.
        self.observationCollection = simulate_observations_owr(
            observationTimes= observationEpochs.tolist(),
            linkEndsPerObservatble= linkEndsPerObservable,
            owrObservationSimulator= self.observationSimulator,
            bodies= self.environmentReal.systemOfBodies,
            noiseAmplitude= noiseAmplitude
        )

        ### Save observations. 
        # TODO: Generalize for all transmitters. 
        self.observations, self.observationTimes = extract_data_observations_owr(
            observationCollection= self.observationCollection,
            transmitter= self.environmentReal.spacecrafts[0]
        )

    def make_estimation ( 
            self,
            maximumIterations: int= 10,
            
            
            printEstimationOutput: bool= True,
    ):

        ### Estimation parameters.
        # Initial state.
        estimationParameters = dynamics.parameters_setup.initial_states(
            propagator_settings= self.environmentReference.arcPropagationSettings,
            bodies= self.environmentReference.systemOfBodies
        )

        # Harmonic coefficients. 
        estimationParameters.append( dynamics.parameters_setup.spherical_harmonics_c_coefficients (
            body= self.environmentReference.frameOriginBody,
            maximum_degree= self.harmonicsDegreeReference,
            maximum_order= self.harmonicsDegreeReference,
            minimum_degree= 2,
            minimum_order= 0 
        ) )
        estimationParameters.append( dynamics.parameters_setup.spherical_harmonics_s_coefficients (
            body= self.environmentReference.frameOriginBody,
            maximum_degree= self.harmonicsDegreeReference,
            maximum_order= self.harmonicsDegreeReference,
            minimum_degree= 2,
            minimum_order= 1 
        ) )

        ### Create parameter set. 
        parameterSet = dynamics.parameters_setup.create_parameter_set(
            parameter_settings= estimationParameters,
            bodies= self.environmentReference.systemOfBodies
        )

        ### Create estimator.
        estimator = estimation.estimation_analysis.Estimator(
            bodies= self.environmentReference.systemOfBodies,
            estimated_parameters= parameterSet,
            observation_settings= self.observationSettings,
            propagator_settings= self.environmentReference.arcPropagationSettings,
            integrate_on_creation= False
        )

        # Estimator settings.
        estimatorSettings = estimation.estimation_analysis.EstimationInput(
            observations_and_times= self.observationCollection,
            convergence_checker= estimation.estimation_analysis.estimation_convergence_checker(
                maximum_iterations= maximumIterations
            )
        )

        estimatorSettings.define_estimation_settings(
            print_output_to_terminal= printEstimationOutput,
            condition_number_warning_each_iteration= printEstimationOutput
        )

        ### Perform estimation.
        self.estimationOutput = estimator.perform_estimation(
            estimation_input= estimatorSettings
        )

    def get_final_estimates( self ):
        """Isolates final parameters from estimation. Splits into initial states,
        cosine coefficients and sine coefficients (...)."""

        finalParameters = self.estimationOutput.final_parameters

        # Number of arcs. 
        if self.arcLengthReference == 0.0:
            numArcs = 1
        else:
            numArcs = int ( float( self.environmentReference.simEndEpoch - 
                self.environmentReference.simStartEpoch ) // float( 
                self.arcLengthReference ) )

        # Index of last estimated state element.
        initialStateIdx = 6 * ( len(self.environmentReference.spacecrafts) * 
                               numArcs )

        # Index for last cosine and sine coefficients. 
        cosineCoeffIdx = initialStateIdx + int ( 
            ( (self.harmonicsDegreeReference - 1) * 
              (self.harmonicsDegreeReference + 4) 
            ) / 2 ) 
        sineCoeffIdx = cosineCoeffIdx + int ( (
            self.harmonicsDegreeReference ** 2 + self.harmonicsDegreeReference
            - 2 ) / 2 ) 

        # Isolates specific estimate results. 
        initialStates = finalParameters[:initialStateIdx]
        estimatedCosineCoeffs = finalParameters[initialStateIdx:cosineCoeffIdx]
        estimatedSineCoefffs = finalParameters[cosineCoeffIdx:sineCoeffIdx]

        # Re-formats initial states into a per-arc format.
        # (Each arc is a row of the array)
        nSC = len( self.environmentReal.spacecrafts )
        nArcs = self.environmentReference.arcNumber
        initialStateInRows = np.reshape( initialStates, (nSC * nArcs, 6) )
        initialStatePerArc = np.hstack( [initialStateInRows[i*nArcs:(i+1)*nArcs] for i in range(nSC)] )


        return initialStatePerArc, estimatedCosineCoeffs, estimatedSineCoefffs

def estimate_with_observation_noise(
    estimator: estimatorClass, 
    initialStateOffset: NDArray= np.array( [0,0,0,0,0,0] ),

    dopplerNoiseSigmaList: NDArray = np.zeros(1),
    sstRangeSigmaList: NDArray = np.zeros(1)
    ) -> NDArray:
    """Performs a set of estimates that vary the observations noise. NOTE this
    does not apply noise on acceleration values, only DSN doppler and sst range
    observations. Returns two arrays with the stored noise combinations and 

    Args:
    - estimator (estimatorClass): Estimator with which the estimation will be \
    performed. 
    
    """
    # Create index array for tested noise sigmas. 
    testValuesArr = np.empty( (
        len(dopplerNoiseSigmaList)*len(sstRangeSigmaList),2 
        ) )
    
    # Propagate reality once.
    estimator.propagate_reality(
        initialStateOffset= initialStateOffset
    )

    ### Nested for loops
    # NOTE: this likely the part that would benefit from multithreading. 
    for dopplerIdx, dopplerNoiseSigma in enumerate(dopplerNoiseSigmaList):
        for sstIdx, sstRangeSigma in enumerate(sstRangeSigmaList):
            # Save tested values. 
            testValuesArr[dopplerIdx *len(sstRangeSigmaList) + sstIdx] = \
                np.array( [dopplerNoiseSigma, sstRangeSigma] )
            
            # Create observations using noise values. 
            estimator.make_observations(
                dopplerNoiseSigma = dopplerNoiseSigma,
                sstRangeSigma = sstRangeSigma
            )

            # Estimate
            estimator.make_estimation(
                maximumIterations= 10,
                printEstimationOutput= False
            )

            # Save to array

    # Output array

