### Tudat imports. 
from tudatpy import dynamics
from tudatpy import estimation
from tudatpy.estimation.observable_models_setup.model_settings import \
    one_way_range_type, one_way_averaged_doppler_type, n_way_averaged_doppler_type
from tudatpy.estimation.observations_setup.ancillary_settings import \
    n_way_doppler_ancillary_settings, doppler_ancillary_settings, FrequencyBands

### Local imports. 
from environment.environment import environmentClass 
from bodies.bodies import body

from observations.observation_class import merge_observations
from observations.one_way_range import oneWayRangeObservationsClass
from observations.n_way_doppler import \
    oneWayDopplerObservationsClass, twoWayDopplerObservationsClass

# TODO: Would be nice to have these in the estimator class or part of their own class. 
# Just make them modular and easy to access...
from observations.ll_sst import one_way_range_link_definitions, one_way_range_observation_simulator,\
    one_way_range_observations, one_way_range_get

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

        rangeNoiseSigma: float= 0.0,
        dopplerNoiseOneWaySigma: float= 0.0,
        dopplerNoiseTwoWaySigma: float= 0.0,

        noiseSettingsSwitch: bool= False,
        ancillarySettingsSwitch: bool= False
        ):
        ### Simulate observations. 
        # Observation epoch. 
        observationEpochStart = self.environmentReal.simStartEpoch + observationEpochMargin
        observationEpochEnd = self.environmentReal.simEndEpoch - observationEpochMargin

        observationEpochs = np.arange( observationEpochStart,                       # type: ignore
                                      step= self.environmentReal.timeStep ,         # type: ignore
                                      stop= observationEpochEnd )                   # type: ignore

        # TODO: Make a modular way for selecting observation pairs. 
        # Link ends for range observations. 
        rangeLinks1 = [self.environmentReal.spacecrafts[1],
                       self.environmentReal.spacecrafts[0]]
        rangeLinks2 = [self.environmentReal.spacecrafts[0],
                       self.environmentReal.spacecrafts[1]]
        rangeLinkGroups = [rangeLinks1, rangeLinks2]

        # Link ends for 1-way doppler.
        doppLinksOW1 = [self.environmentReal.spacecrafts[0],
                        self.environmentReal.groundStations[0]]
        doppLinksOW2 = [self.environmentReal.spacecrafts[1],
                        self.environmentReal.groundStations[0]]
        doppXBandGroups = [doppLinksOW1, doppLinksOW2]

        # Link ends for 2-way doppler
        doppLinks1 = [self.environmentReal.groundStations[0],
                      self.environmentReal.spacecrafts[0],
                      self.environmentReal.groundStations[0],]
        doppLinks2 = [self.environmentReal.groundStations[0],
                      self.environmentReal.spacecrafts[1],
                      self.environmentReal.groundStations[0],]
        doppSBandGroups = [ doppLinks1, doppLinks2 ]

        ### Observations creation.
        # One-way range observations. 
        observationsIntersat = oneWayDopplerObservationsClass(
            linkGroups= rangeLinkGroups, 
            times= observationEpochs,
            environmentReal= self.environmentReal
        )
        # Doppler observations one-way.
        observationsGround = oneWayDopplerObservationsClass(
            linkGroups= doppXBandGroups,
            times= observationEpochs,
            environmentReal= self.environmentReal
        )
        # Doppler observations two-way.
        """ observationsGround = twoWayDopplerObservationsClass(
            linkGroups= doppSBandGroups,
            times= observationEpochs,
            environmentReal= self.environmentReal
        ) """

        # Converts to merged observations class.
        self.observations = merge_observations(
            observationList = [observationsIntersat, observationsGround],
            observationTimes= observationEpochs)

        self.observations.make_simulation_settings()

        ### SWITCH FOR NOISE SETTINGS ###
        if noiseSettingsSwitch:
        # Adds noise to range observations.  
            if rangeNoiseSigma:
                print("Range Noise Added")
                self.observations.set_simulator_settings_noise(
                    observationType= one_way_range_type,
                    noiseSigma= rangeNoiseSigma
                ) 
            # Adds noise to doppler observations. 
            if dopplerNoiseOneWaySigma or dopplerNoiseOneWaySigma:
                print("Doppler Noise Added")
                self.observations.set_simulator_settings_noise(
                    observationType= one_way_averaged_doppler_type,
                    noiseSigma= dopplerNoiseOneWaySigma
                )
                self.observations.set_simulator_settings_noise(
                    observationType= n_way_averaged_doppler_type,
                    noiseSigma= dopplerNoiseTwoWaySigma
                )
        else:
            print("Clean Observations")

        ### SWITCH FOR ANCILLARY SETTINGS ###
        if ancillarySettingsSwitch: 
            # Adds ancillary settings.
            self.observations.set_simulator_settings_ancillary(
                ancillaryObsType= one_way_averaged_doppler_type,
                ancillarySettings= n_way_doppler_ancillary_settings(
                    integration_time= 10.0,  # Integration time of 10s (DSN) 
                    frequency_bands= [FrequencyBands.x_band]
                )
            )
            self.observations.set_simulator_settings_ancillary(
                ancillaryObsType= n_way_averaged_doppler_type,
                ancillarySettings= n_way_doppler_ancillary_settings(
                    integration_time= 10.0,  # Integration time of 10s (DSN) 
                    frequency_bands= [FrequencyBands.s_band]
                )
            )
        

        # Simulates observations. 
        self.observationCollection = self.observations.simulate_observation()

    def get_observations(
            self,
            transmitter: body,
    ):
        """Returns simulated observations for the requested transmitter.
        Args:
        - transmitter (body): Transmitter for desired observations.
        Returns: 
        - observations (NDArray): Array with observations.
        - observationTimes (NDArray): Array with observation epochs. """

        observations, observationTimes = one_way_range_get(
            observationCollection= self.observationCollection,
            transmitter= transmitter 
        )

        return observations, observationTimes 

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
            observation_settings= self.observations.observationModelSettings,
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
    ) -> None:
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
    # NOTE: this is likely the part that would benefit from multithreading. 
    for dopplerIdx, dopplerNoiseSigma in enumerate(dopplerNoiseSigmaList):
        for sstIdx, sstRangeSigma in enumerate(sstRangeSigmaList):
            # Save tested values. 
            testValuesArr[dopplerIdx *len(sstRangeSigmaList) + sstIdx] = \
                np.array( [dopplerNoiseSigma, sstRangeSigma] )
            
            # Create observations using noise values. 
            estimator.make_observations(
                #dopplerNoiseSigma = dopplerNoiseSigma,
                #sstRangeSigma = sstRangeSigma
            )

            # Estimate
            estimator.make_estimation(
                maximumIterations= 10,
                printEstimationOutput= False
            )

            # Save to array

    # Output array

