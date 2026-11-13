### Tudat imports. 
from tudatpy import dynamics
from tudatpy import estimation

from tudatpy.estimation.observable_models_setup.model_settings import \
    one_way_range_type, one_way_averaged_doppler_type, n_way_averaged_doppler_type
from tudatpy.estimation.observations_setup.ancillary_settings import \
    n_way_doppler_ancillary_settings, doppler_ancillary_settings, FrequencyBands

from tudatpy.util import result2array

### Local imports. 
from source.environment.environment import environmentClass 
from source.bodies.bodies import body

from source.observations.observation_class import merge_observations, observationsClass

# TODO: Would be nice to have these in the estimator class or part of their own class. 
# Just make them modular and easy to access...
from source.observations.ll_sst import one_way_range_link_definitions, one_way_range_observation_simulator,\
    one_way_range_observations, one_way_range_get

### External imports.
import numpy as np
from numpy.typing import NDArray
from itertools import product


def get_coefficient_index ( degree: int ):
    """For a tudat-concatenated harmonics coefficient list, returns the index
    of the passed degree harmonics coefficient, including all orders. NOTE: Assumes
    an order-up-to-degree coefficient list. (I.e maxDegree = maxOrder).

    Args:
    - degree (int): Degree of desired harmonic coefficients. """
    # Coefficient max indices. 
    cosIdx = int( ( (degree - 1) * (degree + 4) ) / 2 )
    sinIdx = int( ( degree**2 + degree - 2) / 2 )

    return cosIdx, sinIdx

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
        self.harmonicsDegreeEstimated = harmonicsDegreeReference

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
        self.realPropagationResults = self.environmentReal.propagate()

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
        observationsList: list[ observationsClass ],
        ):

        ### Simulate observations. 
        # Converts to merged observations class.
        self.observations = merge_observations(
            observationList = observationsList
            )

        # Simulates observations. 
        self.observationCollection = self.observations.simulate_observation()

    def make_estimation ( 
            self,
            maximumIterations: int= 10,
            printEstimationOutput: bool= True,
            estimationDegree: int= 0,
    ):

        ### Estimation parameters.
        # Initial state. 
        estimationParameters = dynamics.parameters_setup.initial_states(
            propagator_settings= self.environmentReference.arcPropagationSettings,
            bodies= self.environmentReference.systemOfBodies
        )

        # Uses input max degree if passed.
        if estimationDegree: 
            # Checks that input degree is not higher than available in environment. 
            if estimationDegree > self.harmonicsDegreeReference:
                print("WARNING!: Input max degree larger than environment.\n"\
                "Using environment degree instead...")
                maximumDegreeOrder = self.harmonicsDegreeReference
            else: 
                maximumDegreeOrder = estimationDegree
                self.harmonicsDegreeEstimated = estimationDegree
        else: maximumDegreeOrder = self.harmonicsDegreeReference

        # Harmonic coefficients. 
        estimationParameters.append( dynamics.parameters_setup.spherical_harmonics_c_coefficients (
            body= self.environmentReference.frameOriginBody,
            maximum_degree= maximumDegreeOrder,
            maximum_order= maximumDegreeOrder,
            minimum_degree= 2,
            minimum_order= 0 
        ) )
        estimationParameters.append( dynamics.parameters_setup.spherical_harmonics_s_coefficients (
            body= self.environmentReference.frameOriginBody,
            maximum_degree= maximumDegreeOrder,
            maximum_order= maximumDegreeOrder,
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

    def get_observations(
            self,
            observations: observationsClass,
    ) -> tuple:
        """Returns simulated observations for the requested transmitter.
        Args:
        - observations (observationsClass): Observations object.
        Returns: 
        - values (NDArray): Array with observation values.
        - epochs (NDArray): Array with observation epochs. """

        # Checks if observations have been produced.
        if not hasattr( observations, "simulatedObservations"):
            print(" WARNING: No observations simulated for this object!\n")
            return None, None

        values, epochs = observations.get_observations() 

        return values, epochs 

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
            cosIdxSolo, sinIdxSolo = get_coefficient_index ( degree= self.harmonicsDegreeEstimated )
            cosineCoeffIdx = initialStateIdx + cosIdxSolo
            sineCoeffIdx = cosineCoeffIdx + sinIdxSolo
    
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
    

    def save_observations(
        self,
        fileDir: str,
        fileName: str,
    ):
        # Saves to file. 
        self.observations.simulatedObservations.save_to_binary(
            path= fileDir + fileName
        )
        
    def save_real_propagation( self, fileDir: str, fileName: str ):
        """Saves the real states to a binary file using the tudat function."""

        self.realPropagationResults.save_to_binary(
            path= fileDir + fileName
        )


def estimate_with_observation_noise(
    estimator: estimatorClass, 
    observationsList: list[ observationsClass ], 

    initialStateOffset: NDArray= np.array( [0,0,0,0,0,0] ),

    noiseDict:dict = {}
    ) -> None:
    """Performs a set of estimates that vary the observations noise. NOTE this
    does not apply noise on acceleration values, only DSN doppler and sst range
    observations. Returns two arrays with the stored noise combinations and 

    Args:
    - estimator (estimatorClass): Estimator with which the estimation will be \
    performed. 
    - observationsList (list[observationsClass]): List with observationClasses 
    for this estimation.
    - initialStateOffset (NDArray): Initial state offset for each arc. 
    - noiseDict (dict): Dictionary of noise values. The keys indicating the name 
    of the observationClass they apply to and the value its standard deviation. 
    
    """
    # Create index array for tested noise sigmas. 
    testValues = np.empty( (len( noiseDict.values() ), 2) )
    
    # Propagate reality once.
    estimator.propagate_reality(
        initialStateOffset= initialStateOffset
    )

    ### Nested for loops
    # NOTE: this is likely the part that would benefit from multithreading. 
    # Iterates through all combinations of noise values. 
    i = 0
    for combination in product( *noiseDict.values() ):
        # Save combination.
        testValues[i,:] = combination
        i+=1

        currentCombination = dict( zip( noiseDict.keys(), combination ) )


        # Set new noise values. 
        for observation in observationsList: 
            observation.set_noise_sigma( noiseSigma= currentCombination[ observation.name ] )
        
        # Create observations using noise values. 
        estimator.make_observations()
            
        # Estimate
        estimator.make_estimation(
            maximumIterations= 10,
            printEstimationOutput= False
        )

        # Save to array

# Output array

