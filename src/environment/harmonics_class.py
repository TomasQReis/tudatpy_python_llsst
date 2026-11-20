
# External Imports
import numpy as np
from numpy.typing import NDArray

import pyshtools as pysh
import matplotlib.pyplot as plt

# Tudat imports.

# Local imports. 
from src.environment.environment import environmentClass
from src.estimation.estimator_class import \
    estimatorClass, get_coefficient_index, get_error_block_lines



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
        - filePath (str): relative filepath of harmonics file. (Csv file)
        Example:
        With a harmonics.csv file saved in the relative directory sourceDirector.
        >>> filePath = 'sourceDirectory/harmonics.csv'
        >>> loadedHarmonics = harmonics.make_from_file( filePath= filePath )
        """

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
        harmonicsDegree = int( data[ -1,0 ] )

        return cls( cosCoeffs, nonZeroSinCoeffs, gravityParameter, referenceRadius,
                    harmonicsDegree)

    @classmethod
    def make_from_formal_errors( cls, filePath: str, blockName: str= "Block B" ):
        """Generates an shModelClass from one block of a divided output file.
        The block must use the save_coefficients layout: Columns with degree, 
        order, cosine value, sine value. NOTE: Currently assigns zero to reference
        radius and gravitational parameter. Change if these become estimated values.

        Args:
            filePath (str): Path of the file.
            blockName (str): Block containing the harmonics. Defaults to "Block B".

        Returns:
            shModelClass: SH model built from the block."""

        print( "Creating shModelClass from formal error...")
        print( "NOTE: This does not correspond to an actual harmonics model.")

        # Reads lines from target file. 
        lines= get_error_block_lines( filePath= filePath, blockName= blockName )

        # Sets gravity parameter and radius to zero. 
        # NOTE: Change if these become estimated parameters. 
        gravityParam, referenceRadius = 0.0 , 0.0

        # Loads data array from lines.  
        data = np.loadtxt( lines, delimiter= ",", ndmin= 2 )

        # Orders of harmonics for sorting sinCoefficients. 
        orders = data[ :, 1 ].astype( int )

        # Harmonic coefficients. 
        cosCoeffs = data[ :, 2 ]
        sinCoeffs = data[ orders != 0, 3 ]
        harmonicsDegree = int( data[ -1, 0 ] ) 

        # Initialize class. 
        return cls( cosCoeffs, sinCoeffs, gravityParam, 
                   referenceRadius, harmonicsDegree )
        
    def make_from_difference( self, other: shModelClass ) -> shModelClass:
        """Outputs difference between two shModelClass harmonics coefficients.
        Args:
            other (shModelClass): SH model being subtracted from self model. 

        Returns:
            resultSHModel (shModelClass): "self" minus "other" SH model class."""
        
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

    def rms_per_degree( self ) -> tuple[ NDArray, NDArray ]:
        """Outputs the degrees and corresponding normalized rms amplited value 
        of the shModel.  

        Returns: 
            degrees (NDArray): Array of degrees used in rms calculation.
            rmsPerDegrees (NDArray): RMS value per degree. 
        """

        # Degrees.
        degrees = np.arange( 2, step= 1, stop= self.harmonicsDegree + 1)
        # Empty rms list.
        rmsPerDegrees = []

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
            rmsPerDegrees.append( rms )

            # Resets previous indices. 
            prevCosIdx = cosIdx
            prevSinIdx = sinIdx

        rmsPerDegrees = np.array( rmsPerDegrees )

        return degrees, rmsPerDegrees

    def save_coefficients( 
        self,
        fileDir: str= "",
        fileName: str= "" ):
        """Saves harmonic coefficients in a csv format. The header containts the
        gravitational parameter and reference radius in SI units. The columns contain
        the degree, order, cosine and sine coefficient in that order.
        Args:
        - fileDir (str): directory where the file is saved.
        - fileName (str): filename with type extension. (csv)"""

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
        filePath = fileDir + fileName

        np.savetxt( filePath, saveData, header= header, comments= "",
                    fmt= [ "%5i", "%5i", "%26.16e", "%26.16e" ], delimiter= "," )

    def truncate( self, newMaxDegree: int ):
        """Truncates harmonics class to a specified degree. Will raise a value
        error if given new maximum is higher than the current one. 
        
        Args:
            newMaxDegree (int): New maximum degree. 
        """

        if newMaxDegree > self.harmonicsDegree:
            raise ValueError(
                "ERROR: Given truncation degree is higher than current maximum." \
                f"Current: {self.harmonicsDegree} -- New: {newMaxDegree}"
            )

        self.harmonicsDegree = newMaxDegree

        # Coefficient indices for input maximum.
        newCosIdx, newSinIdx = get_coefficient_index( newMaxDegree )

        # Truncate coefficients.
        self.cosCoeffs = self.cosCoeffs[:newCosIdx]
        self.sinCoeffs = self.sinCoeffs[:newSinIdx]

    def plot_rms( 
        self, 
        title: str,
        format: str= "dimensionless",
        show: bool= True ):

        # Obtain dimensionless rms. 
        degrees, rms = self.rms_per_degree()
        unNormalizationArr = np.array( [ np.sqrt( 2*degree + 1 ) for
        degree in degrees ] )

        # Formats rms. 
        match format:
            case "dimensionless":  # Dimensionless.
                plotVals = rms
                yLabel = "RMS [-]"
            case "geoid":       # Geoid Height 
                
                plotVals = self.referenceRadius * rms * unNormalizationArr
                yLabel = "Geoid Height Amplitude [m]"
            case "radial":      # Radial acceleration
                plotVals = ( 
                    self.gravityParameter / self.referenceRadius**2 ) \
                    * rms * unNormalizationArr * 1e5
                yLabel = "Acceleration Amplitude [mGal]"
            case _:
                raise ValueError(
                    "ERROR: Given format not recognized." \
                    "Valid formats: dimensionless, geoid, radial "
                )

        fig, ax = plt.subplots( figsize= ( 9, 4.5 ) )

        ax.plot( degrees, plotVals )
        
        # Set axis limits to show the extremes.
        ax.grid()

        # Labels
        ax.set_xlabel( "Harmonic Degree" )
        ax.set_xlim( left= -1, right= self.harmonicsDegree+1 )
        ax.set_ylabel( ylabel= yLabel )
        ax.set_yscale( "log" )
        ax.set_title( title )
        

        self.rmsFig, self.rmsAx = fig, ax

        if show: plt.show()

class shPyshClass ():

    def __init__(
        self,
        shGravCoeffs: pysh.SHGravCoeffs,

        gravityParameter: float,
        referenceRadius: float,
        harmonicDegree: int) -> None:

        self.shGrav = shGravCoeffs

        self.gm = gravityParameter
        self.r0 = referenceRadius
        self.harmonicDegree = harmonicDegree

    @classmethod
    def from_shModelClass (cls, shModelClass: shModelClass):
        """Initializes shPyshClass from an existing shModelClass. Existing class 
        must be given with non-zero reference radius and gravity parameter.

        Args:
            shModelClass (shModelClass): Existing shModelClass. """

        if shModelClass.gravityParameter == 0 or shModelClass.referenceRadius == 0:
            raise ValueError(
                "ERROR: Existing shModelClass must be given with a non-zero" \
                "gravity parameter and reference radius."
            )

        # Reshape shModelClass coefficients into pyshtools compatible array. 
        coeffsArr = np.zeros( ( 2, shModelClass.harmonicsDegree+1, 
                               shModelClass.harmonicsDegree+1) )
        
        cosIdx = sinIdx = 0 
        for n in range( 2, shModelClass.harmonicsDegree + 1 ):
            coeffsArr[ 0, n, :n + 1 ]   = shModelClass.cosCoeffs[ cosIdx:cosIdx + n + 1 ]
            coeffsArr[ 1, n, 1:n + 1 ]  = shModelClass.sinCoeffs[ sinIdx:sinIdx + n ]
            cosIdx += n + 1
            sinIdx += n

        # Create grav coefficients class. 
        shGravCoeffs = pysh.SHGravCoeffs.from_array( 
            coeffsArr,
            gm= shModelClass.gravityParameter,
            r0= shModelClass.referenceRadius,
            normalization= "4pi")

        return cls( shGravCoeffs, shModelClass.gravityParameter, shModelClass.referenceRadius,
                    shModelClass.harmonicsDegree )

    def plot_gravity_anomaly( 
            self, 
            title: str, 
            
            show: bool= False,
            save: bool= False,
            fileDir: str= "",
            fileName: str= "" ) -> None:
        """Plots a flat gravity anomaly map. Saves the figure and axis as class
        attributes for later use in savefig.

        Args:
            title (str): Title of plot. 
            show (bool): Boolean, true if the plot should be shown at the end of 
            the process.
        """

        # Initialize grid with maximum degree higher than current for finer resolution. 
        grid = self.shGrav.expand( lmax= 4* self.harmonicDegree )
        assert grid.rad is not None

        # Subtracts point-mass contribution from field to get anomaly. 
        pointPull   = self.gm / self.r0**2
        anomaly     = - ( grid.rad.to_array() + pointPull ) * 1e5

        # Limit set by maximum anomaly.
        limit = np.max( np.abs( anomaly ) )

        # Plotting
        fig, ax = plt.subplots( figsize= ( 9, 4.5 ) )
        mesh = ax.pcolormesh( grid.rad.lons(), grid.rad.lats(), anomaly,
                                cmap= "RdBu_r", vmin= -limit, vmax= limit, shading= "auto" )
        fig.colorbar( mesh, ax= ax, label= "Radial gravity anomaly [mGal]" )

        # Set axis limits to show the extremes.
        ax.set_ylim( bottom= -90, top= 90 )
        ax.set_yticks( np.arange( -90, 90 + 15, 15 ) )
        ax.set_xlim( left= 0, right= 360 )
        ax.set_xticks( np.arange( 0, 360 + 30, 30 ) )

        # Labels
        ax.set_xlabel( "Longitude [deg]" )
        ax.set_ylabel( "Latitude [deg]" )
        ax.set_aspect( "equal" )
        ax.set_title( title )

        self.gravAnomFig, self.gravAnomAx = fig, ax

        # Saves figure. 
        if save: 
            if not fileDir or not fileName:
                raise ValueError(
                    "no input file directory or name given."
                )
            fig.savefig( fileDir + fileName )
        # Shows figure. 
        if show: plt.show()


def kaula_power_rule ( maxDegree: int,
                       kaulaCoefficient: float= 10**-5 ):
    """Calculates the rms per degree according to the Kaula power rule."""
    
    # Degrees (X-axis)
    degrees = np.arange( 2, step= 1, stop= maxDegree+1 )

    # Kaula rule rms. (Y-axis)
    rmsPerKaula = [ kaulaCoefficient/degree**2 for degree in range(
        maxDegree + 1 )[2:] ]

    return degrees, rmsPerKaula
