
# External Imports
import numpy as np

# Tudat imports.

# Local imports. 
from environment.environment import environmentClass
from estimation.estimation import estimatorClass


class shModelClass (): 
    def __init__(
        self,
        inputHarmonics: environmentClass | estimatorClass | None= None,
        harmonicsDegree: int= 2,

        cosCoeffs = [],
        sinCoeffs = [],

        gravityParameter: float= 0,
        referenceRadius: float= 0,
        ) -> None:

        self.inputHarmonics = inputHarmonics

        if isinstance ( inputHarmonics, environmentClass ): self.make_harmonics_from_environment()
        elif isinstance ( inputHarmonics, estimatorClass ): self.make_harmonics_from_estimate()
        elif ( np.isfinite(cosCoeffs).all() and np.isfinite(sinCoeffs).all() and gravityParameter and referenceRadius ):
            # NOTE: This option is extremely sensitive to well-formatted inputs. 
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

        # TODO: Find a way to avoid the environment needing to be propagated 
        # to extract the harmonic coefficients. 

        self.cosCoeffs, self.sinCoeffs, self.gravityParameter, self.referenceRadius\
            = self.inputHarmonics.get_harmonic_coefficients()

        self.harmonicsDegree = self.inputHarmonics.harmonicsMaxDegree
        
    def make_harmonics_from_estimate( self ):
        """Takes spherical harmonic coefficient data from estimator. Note, 
        assumes estimation has already been completed for this estimator."""

        if not isinstance( self.inputHarmonics, estimatorClass):
            raise TypeError(
                f"Input not environmentClass: {type(self.inputHarmonics)}"
            )

        # Extracts coefficients from estimation results. 
        _, self.cosCoeffs, self.sinCoeffs = self.inputHarmonics.get_final_estimates()

        ### TODO: Remove if you end up adding gravitational parameter and
        # or reference radius to estimation outputs. 
        # Extracts estimation environment. 
        estimationEnvironment = self.inputHarmonics.environmentReference

        # Extracts gravity parameter and reference radius. 
        _, _, self.gravityParameter, self.referenceRadius = \
            estimationEnvironment.get_harmonic_coefficients()

        self.harmonicsDegree = self.inputHarmonics.harmonicsDegreeReference

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
        degrees = np.arange( 2, step= 1, stop= self.harmonicsDegree + 1)
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

    def save_coefficients( 
        self,
        filePath: str= "" ):

        # Degree and order of every coefficient, in storage order
        # (degree 2 orders 0..2, degree 3 orders 0..3, ...).
        degrees = np.array( [ degree for degree in range( 2, self.harmonicsDegree + 1 )
                              for _ in range( degree + 1 ) ] )
        orders  = np.array( [ order for degree in range( 2, self.harmonicsDegree + 1 )
                              for order in range( degree + 1 ) ] )

        # Checks that the stored coefficients match the expected layout.
        cosIdx, sinIdx = self.get_coefficient_index( self.harmonicsDegree )
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
        # comments="" stops numpy prefixing the header with "# ".
        header = f"{self.gravityParameter:.15e},{self.referenceRadius:.15e}"

        np.savetxt( filePath, saveData, header= header, comments= "",
                    fmt= [ "%i", "%i", "%.15e", "%.15e" ], delimiter= "," )



def kaula_power_rule ( maxDegree: int,
                       kaulaCoefficient: float= 10**-5 ):
    """Calculates the rms per degree according to the Kaula power rule."""
    
    # Degrees (X-axis)
    degrees = np.arange( 2, step= 1, stop= maxDegree+1 )

    # Kaula rule rms. (Y-axis)
    rmsPerKaula = [ kaulaCoefficient/degree**2 for degree in range(
        maxDegree + 1 )[2:] ]

    return degrees, rmsPerKaula
