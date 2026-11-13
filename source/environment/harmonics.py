
# External Imports
import numpy as np
from numpy.typing import NDArray

# Tudat imports.

# Local imports. 
from source.environment.environment import environmentClass
from source.estimation.estimation import estimatorClass, get_coefficient_index



class shModelClass ():  
    def __init__(
        self,
        cosCoeffs: NDArray[ np.float64 ],
        sinCoeffs: NDArray[ np.float64 ],
        gravityParameter: float,
        referenceRadius: float,
        harmonicsDegree: int,
    ) -> None:
        
        # Store coefficients directly. 
        self.cosCoeffs = np.asarray( cosCoeffs )
        self.sinCoeffs = np.asarray( sinCoeffs )
        self.gravityParameter = gravityParameter
        self.referenceRadius = referenceRadius
        self.harmonicsDegree = harmonicsDegree

    @classmethod
    def make_from_environment( cls, environment: environmentClass ):
        """Takes spherical harmonic coefficient data from environment."""

        # TODO: Find a way to avoid the environment needing to be propagated 
        # to extract the harmonic coefficients. 

        cosCoeffs, sinCoeffs, gravityParameter, referenceRadius\
            = environment.get_harmonic_coefficients()
        harmonicsDegree= environment.harmonicsMaxDegree

        return cls( cosCoeffs, sinCoeffs, gravityParameter, referenceRadius,
                    harmonicsDegree)

    @classmethod
    def make_from_estimate( cls, estimator: estimatorClass ):
        """Takes spherical harmonic coefficient data from estimator. Note, 
        assumes estimation has already been completed for this estimator."""

        # Extracts coefficients from estimation results. 
        _, cosCoeffs, sinCoeffs = estimator.get_final_estimates()

        ### TODO: Remove if you end up adding gravitational parameter and
        # or reference radius to estimation outputs. 
        # Extracts estimation environment.

        # Extracts gravity parameter, reference radius and max degree. 
        _, _, gravityParameter, referenceRadius = \
            estimator.environmentReference.get_harmonic_coefficients()
        harmonicsDegree = estimator.harmonicsDegreeEstimated

        return cls( cosCoeffs, sinCoeffs, gravityParameter, referenceRadius,
                    harmonicsDegree)

    @classmethod
    def make_from_file( cls, filePath: str ):
        """Generates an shModelClass from a given csv file. Assumes the same
        file structure as used in the save_coefficients method and the tudat
        from_file_spherical_harmonics function.
        Args:
        - filePath (str): relative filepath of harmonics file."""

        # Load data from file. 
        header = np.genfromtxt( filePath, delimiter= ",", max_rows= 1)
        data = np.genfromtxt( filePath, delimiter= ",", skip_header= 1)

        # Gravity parameter and reference radius from header. 
        gravityParameter, referenceRadius = header
        # Coefficients from 3rd and 4th columns.
        cosCoeffs = data[ :,2 ]
        sinCoeffs = data[ :,3 ]
        # Removes zero sine coefficients to match the used structure. 
        # NOTE: Probably more complicated than it needs to be...
        nonZeroSinCoeffs = sinCoeffs[ sinCoeffs != 0 ]
        # Maximum degree from final value of first column. 
        harmonicsDegree = data[ -1,0 ]

        return cls( cosCoeffs, nonZeroSinCoeffs, gravityParameter, referenceRadius,
                    harmonicsDegree)
        
    def __sub__( self, other: shModelClass ) -> shModelClass:
        """Outputs difference between two shModelClass harmonics coefficients.
        Args: ---
        - other (shModelClass): SH model being subtracted from self model. 
        Returns: --- 
        - resultSHModel (shModelClass): "self" minus "other" SH model class."""
        
        # Checks which shModel has higher max degree. 
        if self.harmonicsDegree <= other.harmonicsDegree:
            # Maximum idices for larger model (Other)
            cosIdx, sinIdx = get_coefficient_index ( self.harmonicsDegree )

            # Subtracts coefficients. 
            resultCosCoeffs = self.cosCoeffs - other.cosCoeffs[:cosIdx]
            resultSinCoeffs = self.sinCoeffs - other.sinCoeffs[:sinIdx]

            # Output harmonics degree.
            resultDegree = self.harmonicsDegree
        else:
            # Maximum indices for larger model (Self)
            cosIdx, sinIdx = get_coefficient_index ( other.harmonicsDegree )

            # Subtracts coefficients. 
            resultCosCoeffs = self.cosCoeffs[:cosIdx] - other.cosCoeffs
            resultSinCoeffs = self.sinCoeffs[:sinIdx] - other.sinCoeffs     

            # Output harmonics degree.
            resultDegree = other.harmonicsDegree   

        # Creates SH object from results. 
        resultSHModel = shModelClass(
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
        degrees = np.arange( 2, step= 1, stop= self.harmonicsDegree + 1)
        # Empty rms list.
        self.rmsPerDegrees = []

        # Previous indices. 
        prevCosIdx = 0
        prevSinIdx = 0

        for degree in range( self.harmonicsDegree + 1 )[2:]:
            # Coefficient max indices. 
            cosIdx, sinIdx = get_coefficient_index( degree )

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

    def save_coefficients( 
        self,
        fileDir: str= "",
        fileName: str= "" ):
        """Saves harmonic coefficients in a csv format. The header containts the
        gravitational parameter and reference radius in SI units. The columns contain
        the degree, order, cosine and sine coefficient in that order.
        Args:
        - fileDir (str): directory where the file is saved.
        - fileName (str): filename without type extension."""

        # Degree and order of every coefficient, in storage order
        # (degree 2 orders 0..2, degree 3 orders 0..3, ...).
        degrees = np.array( [ degree for degree in range( 2, self.harmonicsDegree + 1 )
                              for _ in range( degree + 1 ) ] )
        orders  = np.array( [ order for degree in range( 2, self.harmonicsDegree + 1 )
                              for order in range( degree + 1 ) ] )

        # Checks that the stored coefficients match the expected layout.
        cosIdx, sinIdx = get_coefficient_index( self.harmonicsDegree )
        if len( self.cosCoeffs ) != cosIdx or len( self.sinCoeffs ) != sinIdx:
            raise ValueError(
                f"Coefficient count does not match degree {self.harmonicsDegree}:\n"
                f"Cosine: {len( self.cosCoeffs )} -- Expected: {cosIdx}\n"
                f"Sine: {len( self.sinCoeffs )} -- Expected: {sinIdx}"
            )

        # Sine coefficients have no order 0 term. Inserts zeros there so
        # every row has a cosine and a sine value.
        sinCoeffsAllOrders = np.zeros( cosIdx )
        sinCoeffsAllOrders[ orders != 0 ] = self.sinCoeffs

        # Column stack: degree, order, C, S.
        saveData = np.column_stack( [ degrees, orders, self.cosCoeffs, sinCoeffsAllOrders ] )

        # Header line with gravitational parameter and reference radius.
        # "" stops numpy prefixing the header with "# ".
        header = f"{self.gravityParameter:24.16e},{self.referenceRadius:24.17e}"

        # Final filepath.
        filePath = fileDir + fileName + ".csv"

        np.savetxt( filePath, saveData, header= header, comments= "",
                    fmt= [ "%5i", "%5i", "%26.16e", "%26.16e" ], delimiter= "," )

def kaula_power_rule ( maxDegree: int,
                       kaulaCoefficient: float= 10**-5 ):
    """Calculates the rms per degree according to the Kaula power rule."""
    
    # Degrees (X-axis)
    degrees = np.arange( 2, step= 1, stop= maxDegree+1 )

    # Kaula rule rms. (Y-axis)
    rmsPerKaula = [ kaulaCoefficient/degree**2 for degree in range(
        maxDegree + 1 )[2:] ]

    return degrees, rmsPerKaula
