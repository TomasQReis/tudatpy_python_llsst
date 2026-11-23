# Contains functions pertaining to producing plots and maps for easier analysis 
# of results. 

### Library imports
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure as fig
import matplotlib.axes as ax
import numpy as np
from numpy.typing import NDArray

### Tudat imports.
from tudatpy.dynamics.propagation import \
    SimulationResults, MultiArcSimulationResults, SingleArcSimulationResults
from tudatpy.util import result2array


### File paths. 
# Run paths. 
SETPREFIX       = "set_"
RUNPREFIX       = "run_"

# Estimates paths.
ESTIMATEFILE    = "estimated_harmonics.csv"
ESTIMATEMAPFILE = "estimated_map.png"

# Noise paths. 
NOISEVALSFILE   = "noise_values.csv"
OBSERVATIONSFILE ="observations"

# Reality paths. 
REALSTATESFILE  = "reality_states"
REALMAPFILE     = "real_map.png"
INTEGRATIONFILE = "integration_parameters"

# Estimation analysis paths 
ANALYSISFILE    = "estimate_analysis.csv"
ERRORMAPFILE    = "error_map.png"
CORRMATXFILE    = "correlation"
CORRPLOTFILE    = 'correlation.png'
CORRMATXFLAG    = 'FCORRMATX'


# NOTE: AI-made but verified. 
def cartesian_to_spherical(
    positions: NDArray[ np.float64 ],
    degrees: bool = True,
    lonRange360: bool = True,
) -> NDArray[ np.float64 ]:
    """Converts Cartesian positions to spherical coordinates, row by row.

    Args:
        positions (NDArray[np.float64]): Positions, shape (N, 3), columns x, y, z.
        degrees (bool): Return latitude and longitude in degrees. Defaults to True.
        lonRange360 (bool): Longitude in [0, 360) instead of (-180, 180]. Defaults to False.

    Returns:
        NDArray[np.float64]: Shape (N, 3), columns radius, latitude, longitude.
            Radius in the units of the input.

    Raises:
        ValueError: If positions does not have shape (N, 3).

    Examples:
        >>> cartesian_to_spherical( np.array( [ [ 0.0, 1738e3, 0.0 ] ] ) )
        array([[1.738e+06, 0.000e+00, 9.000e+01]])
    """
    positions = np.asarray( positions, dtype= float )
    if positions.ndim != 2 or positions.shape[ 1 ] != 3:
        raise ValueError( f"positions must have shape (N, 3), got {positions.shape}" )

    x, y, z = positions[ :, 0 ], positions[ :, 1 ], positions[ :, 2 ]

    radius    = np.sqrt( x**2 + y**2 + z**2 )
    latitude  = np.arctan2( z, np.hypot( x, y ) )    # -90° to 90°
    longitude = np.arctan2( y, x )                   # -180° to 180°

    if lonRange360:
        longitude = np.mod( longitude, 2 * np.pi )   # 0° to 360°
    if degrees:
        latitude, longitude =  np.rad2deg( latitude ) , np.rad2deg( longitude )

    return np.column_stack( [ radius, latitude, longitude ] )

# Slice size for desired degree of analysis. 
def get_slice_size( degree: int, coordinate: str ):
    """Returns the largest whole-degree slice for the desired coordinate given
    a harmonic degree up to 420. If degree would only result in fractional (<1) 
    slices returns 0.25 or 0.5.
    
    Args:
        degree (int): Harmonic degree that limits slice. 
        coordinate (str): Spherical coordinate of slice. Accepts latitude 'lat' or longitude 'lon'.
        
    Returns:
        float: Slice size in degrees. 
        
    Examples:
        >>> get_slice_size( 6, "lon" )
        60
        >>> get_slice_size( 6, "lat" )
        20
    """

    # Input check.
    if not isinstance( degree, int ) or isinstance( degree, bool ) or degree < 0:
        raise ValueError( f"degree must be a non-negative integer. Got {degree!r}" )
    if degree > 420:
        raise ValueError( f"degree must be smaller than or equal to 420. Got {degree}")

    # Match target slice to coordinate. 
    match coordinate:
        case "lat":
            totalAngle = 180
            targetSlice = totalAngle / ( degree+1 )
        case "lon":
            totalAngle = 360
            targetSlice = totalAngle / degree
        case _:
            raise ValueError(
                "Coordinate should be either 'lat' or 'lon'."
            )

    # Whole slices. 
    slicesWhole = [ d for d in range( 1, totalAngle+1 ) if totalAngle % d == 0 ]
    # Partial slices.
    slicesSmall = [0.25, 0.5]

    # For target slices smaller than 1 use either 0.5º or 0.25º.
    if targetSlice < 1:
        return max( d for d in slicesSmall if d <= targetSlice)
    else:
        return max( d for d in slicesWhole if d <= targetSlice)

# Position index for given grid slicing. 
def get_position_index( 
        lats: NDArray, 
        lons: NDArray, 
        latSlice: float, 
        lonSlice: float ) -> tuple[ 
            NDArray[ np.int16 ], NDArray[ np.int16 ], int, int 
            ]:
    """Returns the indices of cells for a given spherical grid with latitude and
    longitudinal slices as given in inputs. Latitude must be constrained to -90º 
    +90º and longitude between 0º and 360º. 
    
    If an position is on the border of a cell, it will return as being in the 
    previous cell. If this occurs on the first cell it simply uses the floor
    division.
    
    Args:
        lats (NDArray): array of latitude positions. Given in degrees.
        lons (NDArray): array of longitude positions. Given in degrees. 
        latSlice (float): size of latitudinal grid slice. Given in degrees.
        lonSlice (float): size of longitudinal grid slice. Given in degrees.
        
    Returns:
        latIdx (NDArray): array of indices for the latitudinal position.
        lonIdx (NDArray): array of indices for the longitudinal position. 
        nLat (int): number of latitudinal slices. 
        nLon (int): number of longitudinal slices.
        
    Examples:
        >>> lats= np.array([ -15, 0, 15 ])
        >>> lons= np.array([ 190, 180, 160])
        >>> get_position_cell( lats, lons, 60, 30 )
        (array([2,2,3]), array([3,3,2]), 6, 6)"""

    # Number of cells along each coordinate. 
    nLat, nLon = int( 180 // latSlice ) , int( 360 // lonSlice )

    # Modf division of 
    # Lats +90 to prevent negative indices. 
    latIdxRemainder, latIdx = np.modf( ( np.asarray( lats ) + 90.0 ) / latSlice )
    lonIdxRemainder, lonIdx = np.modf( np.asarray( lons ) / lonSlice )

    # Checks for points at borders (Where fractional part is zero)
    latIdxBorders = np.argwhere( latIdxRemainder == 0 )
    lonIdxBorders = np.argwhere( lonIdxRemainder == 0 )
    # Sets cell of borders as the previous cell. 
    # If first cell disregards. 
    latIdx[ latIdxBorders ] = latIdx[ np.where(
            latIdxBorders - 1 >= 0, latIdxBorders-1, latIdxBorders )
        ]
    lonIdx[ lonIdxBorders ] = lonIdx[ np.where(
            lonIdxBorders - 1 >= 0, lonIdxBorders-1, lonIdxBorders )
        ]
    
    return latIdx.astype( int ) , lonIdx.astype( int ) , nLat, nLon


def get_flags( filePath: str, starter: str= '#- ', flags: list[ str ]= ['FCORRMATX']):

    # TODO: Make this output a dictionary with flag keys and values. 
    # Empty flag value list. 
    flagsVals = []
    with open( filePath ) as file:
        # Read line by line. 
        for line in file:
            # Check when flag starter occurs.
            if line.startswith( starter ):
                for flag in flags:
                    # If flag identifier.
                    if flag in line: 
                        # Reads value and continues to next flag. 
                        flagsVals.append( int( line.strip()[-1] ) ) 
                        continue
    # Error for no flags. 
    if not flagsVals:
        raise ValueError( f"No data found for flags in {filePath}" )
    return flagsVals

class analysisLibrary():
    
    def __init__(
        self,
        runDir: str,
        ) -> None:

        self.runDir = runDir 

        self.epochs = np.empty(0)
        self.lats = np.empty(0)
        self.lons = np.empty(0)

    def load_propagation( self, realStatesPath: str ) -> None:

        propagationPath = realStatesPath
        simulationResults = MultiArcSimulationResults.load_from_binary( # type: ignore
            path= propagationPath ) 

        # Single arc results list.
        self.singleArcs = simulationResults.single_arc_results

        # Save relevant values to NDArrays
        # NOTE: This list should be expanded as necessary. 
        for arc in self.singleArcs:
            dependentArr = result2array( arc.dependent_variable_history )

            self.epochs = np.concat( ( self.epochs, dependentArr[ :,0 ] ) )
            self.lats = np.concat( ( self.lats, np.rad2deg( dependentArr[ :,1 ] ) ) )
            # Convert longitude results to 0º / 360º range by adding 180
            self.lons = np.concat( ( self.lons, np.rad2deg( dependentArr[ :,2 ] ) + 180 ) )

    def load_correlation( 
            self, 
            corrFileName: str= CORRMATXFILE
        ) -> None:

        # Correlation matrix file. 
        corrFilePath = self.runDir + corrFileName + '.npz'

        # Load data. 
        data = np.load( corrFilePath )

        # If full correlation matrix, skip symmetry. 
        if get_flags( filePath= self.runDir + ANALYSISFILE, flags= [CORRMATXFLAG] )[0]:
            # Load full matrix. 
            self.size = data[ 'size' ]
            self.fullMatx = data[ 'halfMatx' ]
        else: 
            # Load size. 
            self.size = data[ 'size' ]

            # Row and column indices for half matrix. 
            rows, cols = np.triu_indices( self.size )

            self.fullMatx = np.zeros( (self.size, self.size) )
            self.fullMatx[ rows, cols ] = data[ 'halfMatx' ]
            self.fullMatx[ cols, rows ] = data[ 'halfMatx' ]


    def plot_ground_track( 
        self,
        latSlice: float,
        lonSlice: float ) -> tuple[ fig.Figure, ax.Axes ]: 

        # Create plot showing trajectory.
        fig, ax = plt.subplots( figsize= ( 9, 4.5 ) )
        ax.plot( self.lons, self.lats, linestyle= "", marker= ".", label= "Trajectory" )

        ax.set_ylim( bottom= -90, top= 90 )
        ax.set_yticks( np.arange( -90, 91, latSlice ) )
        ax.set_ylabel( "Latitude [deg]" )

        ax.set_xlim( left= 0, right= 360 )
        ax.set_xticks( np.arange( 0, 361, lonSlice ) )
        ax.set_xlabel( "Longitude [deg]" )

        ax.set_aspect( "equal" )
        ax.set_title( "Ground track" )

        ax.grid()

        plt.show()

        return fig, ax

    def plot_observation_density( 
        self,

        title: str,

        forceSlice: bool= False,
        lonSlice: float= 0.0,
        latSlice: float= 0.0,
        degreeSlice: int= 0,

        show: bool= False,
        save: bool= False,
        fname: str= "observation_density.png"
        ) -> None:

        # Impose input slice sizes. 
        if forceSlice: 
            maxLongDegree = 360 // ( 2*lonSlice)
            maxLatDegree = 180 // latSlice - 1

            if lonSlice <= 0 or latSlice <= 0:
                raise ValueError(
                    "Slice size cannot be equal or smaller than zero." \
                    f"Long Slice: {lonSlice} - Lat Slice: {latSlice}"
                )
            elif lonSlice >= 360 or latSlice >= 180:
                raise ValueError(
                    "Slice size cannot be equal to, or larger than entire sphere." \
                    "Longitude slice < 360º - Latitude slice < 180º" \
                    f"Long Slice: {lonSlice} - Lat Slice: {latSlice}"
                )
            
            # Warn of degree limitation with given slices. 
            print(f"WARNING: observation density valid up to degree: {min(
                maxLatDegree, maxLongDegree
                ) }")
        else:
            if degreeSlice > 420: 
                raise ValueError(
                    "ERROR: Provided degree must be smaller than 420."
                )
            elif degreeSlice <= 2:
                raise ValueError(
                    "ERROR: Provided degree must be larger than 2."
                )

            print(f"Slicing to ensure validity up to degree {degreeSlice}")

            lonSlice = get_slice_size( degree= degreeSlice, coordinate= "lon" )
            latSlice  = get_slice_size( degree= degreeSlice, coordinate= "lat" )

        # Find gridsize and indices for position
        latIdx, lonIdx, latNum, lonNum = get_position_index(
            lats= self.lats,
            lons= self.lons,
            latSlice= latSlice,
            lonSlice= lonSlice
        )

        # Initialize empty bins.
        bins = np.zeros( ( latNum, lonNum ) )

        # Sweep through states and check number of passes per grid. 
        # Assigns unique ID to each cell.
        cellID = latIdx * latNum + lonIdx
        # Identify where ID changes (New cell entered = Pass).
        passOccurs = np.zeros( len( cellID ), dtype= bool )
        passOccurs[ np.argwhere( cellID[ 1: ] != cellID[ :-1 ] ) ] = True

        # Add to corresponding bin. 
        np.add.at( bins, ( latIdx[ passOccurs ], lonIdx[ passOccurs ] ), 1 )
        # Adds last cell in path as this is not detected as a switch. 
        np.add.at( bins, ( latIdx[ -1 ], lonIdx[ -1 ] ), 1 )

        # Plots. 
        limit = np.max( bins )
        
        fig, ax = plt.subplots( figsize= ( 9, 4.5 ) )
        mesh = ax.pcolormesh( 
            np.arange( 0, 361, lonSlice ), np.arange( -90, 91, latSlice ), 
            bins, cmap= "Blues", vmin= 0, vmax= limit, shading= "auto" )
        
        fig.colorbar( mesh, ax= ax, label= "Number of Passes [-]",
                      format= "%d" )
    
        # Set axis ticks. 
        if latSlice < 15: latGrid = 15 
        else: latGrid = latSlice
        if lonSlice < 30: lonGrid = 30
        else: lonGrid = lonSlice
        ax.set_ylim( bottom= -90, top= 90 )
        ax.set_yticks( np.arange( -90, 91, latGrid ) )
        ax.set_xlim( left= 0, right= 360 )
        ax.set_xticks( np.arange( 0, 361, lonGrid ) )
        ax.grid()
    
        # Labels
        ax.set_xlabel( "Longitude [deg]" )
        ax.set_ylabel( "Latitude [deg]" )

        # Aspect ratio and title
        ax.set_aspect( "equal" )
        ax.set_title( title )

        if save: fig.savefig( fname= self.runDir + fname)
        if show: plt.show()
        
    def plot_correlation( \
        self,
        fileName: str= CORRPLOTFILE,
        title: str= 'Correlation Matrix',
        save: bool= False,
        show: bool= False):


        fig, ax = plt.subplots( figsize= ( 9, 4.5 ) )

        mesh = ax.pcolormesh( 
            np.arange( 0, self.size+1, 1 ), np.arange( 0, self.size+1, 1 ), 
            np.abs( self.fullMatx ), cmap= "RdYlGn", vmin= 0, vmax= 1, shading= "auto" )
        
        fig.colorbar( mesh, ax= ax, label= "Correlation [-]" )
    
        # Labels
        ax.set_xlabel( "Estimated Parameter Index" )
        ax.set_ylabel( "Estimated Parameter Index" )

        # Aspect ratio and title
        ax.set_aspect( "equal" )
        ax.set_title( title )

        if save: fig.savefig( fname= self.runDir + fileName)
        if show: plt.show()