# Contains functions pertaining to producing plots and maps for easier analysis 
# of results. 

### Library imports
import numpy as np

### Tudat imports.
from tudatpy.dynamics.propagation import \
    SimulationResults, MultiArcSimulationResults, SingleArcSimulationResults
from tudatpy.util import result2array

### Local imports. 
from src.estimation.estimator_class import estimatorClass


import numpy as np
from numpy.typing import NDArray

# NOTE: AI-made but verified. 
def cartesian_to_spherical(
    positions: NDArray[ np.float64 ],
    degrees: bool = True,
    lonRange360: bool = False,
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
        latitude, longitude =  latitude , longitude

    return np.column_stack( [ radius, latitude, longitude ] )

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
    

# Geometric observation density plotter
def plot_observation_density( 
    

    runDir: str,
    propagationFile: str,
    parametersFile: str,

    forceSlice: bool= True,
    longSlice: float= 0.0,
    latSlice: float= 0.0,
    degreeSlice: int= 0,

    multiArc: bool= True,
    multiSpacecraft: bool= False
    ):

    # Impose input slice sizes. 
    if forceSlice: 
        maxLongDegree = 360 // ( 2*longSlice)
        maxLatDegree = 180 // latSlice - 1
        
        # Convert to radians.
        longSlice   = np.deg2rad( longSlice )
        latSlice    = np.deg2rad( latSlice )

        if longSlice <= 0 or latSlice <= 0:
            raise ValueError(
                "Slice size cannot be equal or smaller than zero." \
                f"Long Slice: {longSlice} - Lat Slice: {latSlice}"
            )
        elif longSlice >= 2*np.pi or latSlice >= np.pi:
            raise ValueError(
                "Slice size cannot be equal to, or larger than entire sphere." \
                "Longitude slice < 360º - Latitude slice < 180º" \
                f"Long Slice: {longSlice} - Lat Slice: {latSlice}"
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

        #longSlice = 

    # Import propagation data. 
    propagationPath = runDir + propagationFile
    simulationResults = MultiArcSimulationResults.load_from_binary( path= propagationPath )   # type: ignore

    # Limit states that will be inspected depending on number of spacecraft. 
    if multiSpacecraft: 
        # Import integration parameters. 
        with open( runDir + parametersFile, "r" ) as file:
            for line in file:
                if line.startswith( "spacecraft: " ):
                    # Extract number of spacecraft. 
                    spacecraft = [ int( s ) for s in line.split() if s.isdigit() ][0]
        # Defines slice of each spacecraft's position. 
        stateSlice = slice( 1, 1 + spacecraft * 6, 3 )
    else: 
        # Limits slice to single spacecraft position. 
        stateSlice = slice( 1, 4 )

    
    # Extract states from propagation data. 
    assert isinstance( simulationResults, MultiArcSimulationResults )
    singleArcResults = simulationResults.single_arc_results

    # Extract each arc's position and merge to single array. 
    sphericalArr = np.empty( ( 0, 3 ) )      # TODO: Still needs to be generalized. 
    for singleArcResult in singleArcResults: # type: ignore
        stateArr = result2array( singleArcResult.state_history )[:, stateSlice]
        # Convert states to radius, latitude, longitude (Spherical).  
        stateSpherical = cartesian_to_spherical( stateArr )
        # Stack
        sphericalArr = np.vstack( ( sphericalArr, stateSpherical ) ) 

    # Create grid and bins. 

    # Sweep through states and check number of passes per grid. 

    # Plot map of density. 


