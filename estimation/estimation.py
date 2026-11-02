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

        referenceArcLength: float= 0.0,      # TODO: Generalize
        estimationArcLength: float= 0.0,

        referenceHarmonicsDegree: int= 5,
        estimationHarmonicsDegree: int= 5
    ) -> None:

        
        self.referenceEnvironment   = referenceEnvironment
        self.estimationEnvironment  = estimationEnvironment

        self.referenceArcLength     = referenceArcLength
        self.estimationArcLength    = estimationArcLength

        # NOTE: reference environment harmonics degree is currently unused. 
        self.referenceHarmonicsDegree = referenceHarmonicsDegree
        self.estimationHarmonicsDegree = estimationHarmonicsDegree

    def propagate_reality ( self ):

        ### Propagate reality 
        self.referenceEnvironment.make_propagation_settings(
            arcTimeLength= self.referenceArcLength,
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

    def get_final_estimates( self ):
        """Isolates final parameters from estimation. Splits into initial states,
        cosine coefficients and sine coefficients (...)."""

        finalParameters = self.estimationOutput.final_parameters

        # Number of arcs. 
        if self.estimationArcLength == 0.0:
            numArcs = 1
        else:
            numArcs = float( self.estimationEnvironment.simEndEpoch - 
                self.estimationEnvironment.simStartEpoch ) // float( 
                self.estimationArcLength ) 

        # Index of last estimated state element.
        initialStateIdx = 6 * (len(self.estimationEnvironment.spacecrafts) * 
                               numArcs)

        # Index for last cosine and sine coefficients. 
        cosineCoeffIdx = initialStateIdx + int ( 
            ( (self.estimationHarmonicsDegree - 1) * 
              (self.estimationHarmonicsDegree + 4) 
            ) / 2 ) 
        sineCoeffIdx = cosineCoeffIdx + int ( (
            self.estimationHarmonicsDegree ** 2 + self.estimationHarmonicsDegree
            - 2 ) / 2 ) 

        # Isolates specific estimate results. 
        initialStates = np.array(finalParameters[:initialStateIdx])
        estimatedCosineCoeffs = np.array(finalParameters[initialStateIdx:cosineCoeffIdx])
        estimatedSineCoefffs = np.array(finalParameters[cosineCoeffIdx:sineCoeffIdx])

        return initialStates, estimatedCosineCoeffs, estimatedSineCoefffs


class shModelClass (): 
    def __init__(
        self,
        inputHarmonics: environmentClass | estimator | None= None,
        harmonicsDegree: int= 2,

        cosCoeffs = [],
        sinCoeffs = [],

        gravityParameter: float= 0,
        referenceRadius: float= 0,
        ) -> None:

        self.inputHarmonics = inputHarmonics

        if isinstance ( inputHarmonics, environmentClass ): self.make_harmonics_from_environment()
        elif isinstance ( inputHarmonics, estimator ): self.make_harmonics_from_estimate()
        elif ( cosCoeffs.any() and sinCoeffs.any() and gravityParameter and referenceRadius ):
            self.cosCoeffs = np.array( cosCoeffs )
            self.sinCoeffs = np.array( sinCoeffs )
            self.gravityParameter = gravityParameter
            self.referenceRadius = referenceRadius
            self.harmonicsDegree = harmonicsDegree
        else: raise RuntimeError(
            f"Input Harmonics of wrong type: {type(inputHarmonics)}"
        )

    def make_harmonics_from_environment( self ):
        """Takes spherical harmonic coefficient data from environment."""

        if not isinstance( self.inputHarmonics, environmentClass):
            raise TypeError(
                f"Input not environmentClass: {type(self.inputHarmonics)}"
            )

        self.cosCoeffs, self.sinCoeffs, self.gravityParameter, self.referenceRadius\
            = self.inputHarmonics.get_harmonic_coefficients()

        self.harmonicsDegree = self.inputHarmonics.harmonicsMaxDegree
        
    def make_harmonics_from_estimate( self ):
        """Takes spherical harmonic coefficient data from estimator. Note, 
        assumes estimation has already been completed for this estimator."""

        if not isinstance( self.inputHarmonics, estimator):
            raise TypeError(
                f"Input not environmentClass: {type(self.inputHarmonics)}"
            )

        # Extracts coefficients from estimation results. 
        _, self.cosCoeffs, self.sinCoeffs = self.inputHarmonics.get_final_estimates()

        ### TODO: Remove if you end up adding gravitational parameter and
        # or reference radius to estimation outputs. 
        # Extracts estimation environment. 
        estimationEnvironment = self.inputHarmonics.estimationEnvironment

        # Extracts gravity parameter and reference radius. 
        _, _, self.gravityParameter, self.referenceRadius = \
            estimationEnvironment.get_harmonic_coefficients()

        self.harmonicsDegree = self.inputHarmonics.estimationHarmonicsDegree

    def get_coefficient_index ( self, degree: int ):
        # Coefficient max indices. 
        cosIdx = int( ( (degree - 1) * (degree + 4) ) / 2 )
        sinIdx = int( ( degree**2 + degree - 2) / 2 )

        return cosIdx, sinIdx

    def __sub__( self, other: shModelClass ) -> shModelClass:
        """Outputs difference between two shModelClass harmonics coefficients.
        Args: ---
        - other (shModelClass): SH model being subtracted from self model. 
        Returns: --- 
        - resultSHModel (shModelClass): "self" minus "other" SH model class."""
        
        # Checks which shModel has higher max degree. 
        if self.harmonicsDegree <= other.harmonicsDegree:
            # Maximum idices for larger model (Other)
            cosIdx, sinIdx = self.get_coefficient_index ( self.harmonicsDegree )

            # Subtracts coefficients. 
            resultCosCoeffs = self.cosCoeffs - other.cosCoeffs[:cosIdx]
            resultSinCoeffs = self.sinCoeffs - other.sinCoeffs[:sinIdx]

            # Output harmonics degree.
            resultDegree = self.harmonicsDegree
        else:
            # Maximum idices for larger model (Self)
            cosIdx, sinIdx = self.get_coefficient_index ( other.harmonicsDegree )

            # Subtracts coefficients. 
            resultCosCoeffs = self.cosCoeffs[:cosIdx] - other.cosCoeffs
            resultSinCoeffs = self.sinCoeffs[:sinIdx] - other.sinCoeffs     

            # Output harmonics degree.
            resultDegree = other.harmonicsDegree   

        # Creates SH object from results. 
        resultSHModel = shModelClass(
            inputHarmonics= None, # type: ignore
            cosCoeffs= resultCosCoeffs,
            sinCoeffs= resultSinCoeffs,
            gravityParameter= self.gravityParameter,
            referenceRadius= self.referenceRadius,
            harmonicsDegree= resultDegree
        )

        return resultSHModel

    def rms_per_degree( self ):
        """Calculates the rms (And additionallity the 1-sigma value) of the self 
        harmonics coefficients. 
        Args: ---
        - Self.
        Returns: ---
        - degrees (NDArray): Array of degrees used in rms calculation.
        - rmsPerDegrees (NDArray): RMS value per degree. """

        # Degrees.
        degrees = np.arange( 2, step= 1, stop= self.harmonicsDegree)
        # Empty rms list.
        self.rmsPerDegrees = []

        # Previous indices. 
        prevCosIdx = 0
        prevSinIdx = 0

        for degree in range( self.harmonicsDegree + 1 )[2:]:
            # Coefficient max indices. 
            cosIdx, sinIdx = self.get_coefficient_index( degree )

            # RMS of degree.
            sumOfCosCoeffsSqrd = np.sum( self.cosCoeffs[prevCosIdx:cosIdx]**2 )
            sumOfSinCoeffsSqrd = np.sum( self.sinCoeffs[prevSinIdx:sinIdx]**2 )

            # Calculates rms for degree. 
            rms = np.sqrt ( ( sumOfCosCoeffsSqrd + sumOfSinCoeffsSqrd ) / ( 2*degree + 1 ) )

            # Appends to list. 
            self.rmsPerDegrees.append( rms )

            # Resets previous indices. 
            prevCosIdx = cosIdx
            prevSinIdx = sinIdx

        self.rmsPerDegrees = np.array( self.rmsPerDegrees )

        return degrees, self.rmsPerDegrees


def kaula_power_rule ( maxDegree: int,
                       kaulaCoefficient: float= 10**-5 ):
    """Calculates the rms per degree according to the Kaula power rule."""
    
    # Degrees (X-axis)
    degrees = np.arange( 2, step= 1, stop= maxDegree+1 )

    # Kaula rule rms. (Y-axis)
    rmsPerKaula = [ kaulaCoefficient/degree**2 for degree in range(
        maxDegree + 1 )[2:] ]

    return degrees, rmsPerKaula
