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

# Geometric observation density plotter
def plot_observation_density( 
    longSlice: float,
    latSlice: float,

    runDir: str,
    propagationFile: str,
    parametersFile: str,

    multiArc: bool= True,
    multiSpacecraft: bool= False
    ):
    # Warn of degree limitation with given slices. 
    maxLongDegree = 360 // ( 2*longSlice)
    maxLatDegree = 180 // latSlice 

    print(f"WARNING: observation density valid up to degree: {min(
        maxLatDegree, maxLongDegree
        ) }")

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


