### Tudat imports. 
from tudatpy import dynamics
from tudatpy import estimation

from tudatpy.estimation.estimation_analysis import CovarianceAnalysisInput
from tudatpy.estimation.observations.observations_processing import observation_parser



### Local imports. 
from src.environment.environment import environmentClass 
from src.observations.observation_class import \
    merge_observations, observationsClass

### External imports.
import numpy as np
from numpy.typing import NDArray


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

def get_error_block_lines( filePath: str, blockName: str= "Block B",
                           divider: str= "#--- ") -> list[str] :
    """Returns the data lines of one block in a file with '# --- <name> ---' dividers.

    Args:
        filePath (str): Path of the file.
        blockName (str): Text identifying the block's divider line. Defaults to "Block B".
        divider (str): Start of every divider line. Defaults to "# ---".

    Returns:
        list[str]: Data lines of the block, without comments or blank lines.

    Raises:
        ValueError: If the block is missing or empty."""
    
    lines, inBlock = [], False
    with open( filePath ) as file:
        # Line by line. 
        for line in file:
            # Check when divider occurs. 
            if line.startswith( divider ):
                # Check if we're in the requested block. 
                if inBlock:                       
                    break
                # Check if requested block starts. 
                inBlock = blockName in line      
                continue
            # If no divider, checks if in desired block and takes line.
            if inBlock and line.strip() and not line.startswith( "#" ):
                lines.append( line )
    # Error for no lines available. 
    if not lines:
        raise ValueError( f"No data found for '{blockName}' in {filePath}" )
    return lines



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

        # Avoids conflicting systemOfBodies between environments. 
        if environmentReal is environmentReference:
            raise ValueError( "environmentReal and environmentReference must be separate instances." )
        
        self.environmentReal   = environmentReal
        self.environmentReference  = environmentReference

        self.arcLengthReal     = arcLengthReal
        self.arcLengthReference    = arcLengthReference
 
        self.harmonicsDegreeReal = harmonicsDegreeReal
        self.harmonicsDegreeReference = harmonicsDegreeReference
        self.harmonicsDegreeEstimated = harmonicsDegreeReference

    def propagate_reality ( 
        self,
        initialStateOffset: NDArray= np.array([0,0,0,0,0,0]),

        dependentVariables: list= []
        ):

        ### Propagate reality 
        self.environmentReal.make_propagation_settings(
            arcTimeLength= self.arcLengthReal,

            dependentVariables= dependentVariables,

            keepEnvironment= True, 
            skipArcCheck= True      # TODO: Remove after testing. 
        )

        # Save propagation results. 
        self.environmentReal.propagate()

        # Match initial state offset to number of spacecraft. 
        initialStateOffset = np.tile( initialStateOffset, 
                                        len( self.environmentReal.spacecrafts ) )
        
        # Offset reality initial states for initial guess values. 
        initialStatesArray = self.environmentReal.get_initial_states() + initialStateOffset

        ### Estimation environment settings. 
        self.environmentReference.make_propagation_settings(
            arcTimeLength= self.arcLengthReference,

            dependentVariables= dependentVariables,

            importInitialStates= True,
            initialStatesArray= initialStatesArray,

            skipArcCheck= True      # TODO: Remove when done testing. 
        )

    def make_observations ( 
        self,
        observationsList: list[ observationsClass ],

        weighObservations: bool= False,
        ):

        ### Simulate observations. 
        # Converts to merged observations class.
        self.observations = merge_observations(
            observationList = observationsList
            )


        # Simulates observations. 
        self.observationCollection = self.observations.simulate_observation()

        if weighObservations:
            # Iterates through observation objects 
            for observations in observationsList:
                # Sets observation weight from class attributes. 
                self.observationCollection.set_constant_weight(
                    weight= 1 / (observations.noiseSigma)**2,
                    observation_parser= observation_parser(
                        link_ends= observations.linkEndsDict
                    )
                )

            # Adds weight to observation collection using links as parser.

    def make_estimation ( 
            self,
            maximumIterations: int= 10,
            printEstimationOutput: bool= True,
            estimationDegree: int= 0,

            covarianceAnalysis: bool= False
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

        ### Perform covariance analysis. 
        if covarianceAnalysis: 
            # TODO: Still need to add weights to this operation. 
            self.estimationCovarianceOutput = estimator.compute_covariance(
                CovarianceAnalysisInput( self.observationCollection )
            )

        ### Perform parameter estimation.
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

    def get_formal_error( self ):

        return self.estimationOutput.formal_errors
    
    def save_observations( self, fileDir: str, fileName: str ):
        # Saves to file. 
        self.observations.simulatedObservations.save_to_binary( # type: ignore
            path= fileDir + fileName
        )
        
    def save_real_propagation( self, fileDir: str, fileName: str ):
        """Saves the real states to a binary file using the tudat function."""

        self.environmentReal.save_propagation(
            fileDir= fileDir,
            fileName= fileName
        )

    def save_formal_error( 
            self, 
            fileDir: str, 
            fileName: str= "formal_errors.csv" ) -> None:
        """Saves formal errors resulting from propagation. Takes in file directory
        and (Optional) file name.
        Args:
            fileDir (str):    String containing individual run results file directory.
            fileName (str):   OPTIONAL. File name, defaults to "formal_errors.csv". Requires file extension.
        """
        
        print( "Saving formal errors...")
        # Get formal errors.
        formalErrors = self.get_formal_error()

        ### Separate errors ( State - Harmonics - etc. )
        ### Add additional splits here when estimating additional parameters.
        # Auxiliary values.
        spacecraftNum   = len( self.environmentReference.spacecrafts )
        arcNum          = self.environmentReference.arcNumber
        cosIndx, sinIndx= get_coefficient_index( self.harmonicsDegreeEstimated )
        harmonicsIndx   = sum( [ cosIndx, sinIndx ] )

        # Number of individual estimated parameters. 
        initialStateEstimatedParams = spacecraftNum * arcNum * 6
        # Separated initial state estimate error. 
        initialStateError = np.reshape( 
            formalErrors[:initialStateEstimatedParams], 
            ( arcNum, 6*spacecraftNum ) )

        # Harmonic estimate error. 
        harmonicsError  = formalErrors[ 
            initialStateEstimatedParams:
            (initialStateEstimatedParams + harmonicsIndx) 
        ]
        # Cosine formal errors. 
        cosineErrors    = harmonicsError[ :cosIndx ]
        # Sine formal errors ( =0 where not estimated )
        sineErrors      = np.zeros( cosIndx )
        orders  = np.array( [ order for degree in range( 
                            2, self.harmonicsDegreeEstimated + 1 )
                            for order in range( degree + 1 ) ] )
        degrees = np.array( [ degree for degree in range( 
                            2, self.harmonicsDegreeEstimated + 1 )
                            for _ in range( degree + 1 ) ] )
        sineErrors[ orders != 0 ] = harmonicsError[cosIndx:]
        # Match data format for saved harmonics.
        harmonicsData = np.column_stack(
            [ degrees, orders, cosineErrors, sineErrors ]
        )

        ### Save values to file.
        description = (
            "----- Estimation formal errors. -----\n"
            "Block A: Initial state formal error. Each row corresponds to a \n"
            "single arc's initial estimate. The values are ordered by a \n"
            "spacecraft-by-spacecraft arrangement. For n-spacecrafts \n"
            "Columns: x_1, y_1, z_1, Vx_1, Vy_1, Vz_1, x_2, (...), Vy_n, Vz_n\n\n"
            "Block B: Harmonic coefficient formal error. Columns:\n " 
            "1: Degree, 2: Order, 3: Cosine coeff. formal error\n "
            "4: Sine coeff. formal error.\n"
        )
        with open( fileDir + fileName, "w" ) as file:
            # Write description
            for line in description.splitlines():
                file.write( f"#{line}\n")

            # Write state errors.
            file.write("#--- Block A ---\n")
            np.savetxt( file, initialStateError, fmt= "%23.16e", 
                       delimiter= ",")

            # Write harmonics errors.
            file.write("#--- Block B ---\n")
            np.savetxt( file, harmonicsData, fmt= [ "%5i", "%5i", "%26.16e", "%26.16e" ], 
                       delimiter= ",")


