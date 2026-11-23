### Library imports
import numpy as np
import re
import time
from numpy.typing import NDArray
from itertools import product
from datetime import date
from pathlib import Path

### Tudat Imports
from tudatpy.interface import spice
from tudatpy.dynamics.propagation_setup import dependent_variable

### Local imports
from src.estimation.estimator_class import estimatorClass
from src.observations.observation_class import observationsClass
from src.environment.harmonics_class import shModelClass, shPyshClass
from src.estimation.analysis import analysisLibrary




### Constants
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

# Error paths 
ERRORSFILE      = "formal_errors.csv"
ERRORMAPFILE    = "error_map.png"

def get_last_run_number( runsDir: str, prefix: str= "run_" ) -> int:

    # Defines checking only for directories matching "run_int".
    pattern = re.compile( rf"{re.escape( prefix )}(\d+)" )

    # Obtains all the run number values from the directories. 
    runNumbers = [
        int( match.group( 1 ) )
        for path in Path( runsDir ).iterdir()
        if path.is_dir() and ( match := pattern.fullmatch( path.name ) )
    ]

    return max( runNumbers, default= 0 )


def estimate_with_observation_noise(
    estimator: estimatorClass, 
    observationsList: list[ observationsClass ], 
    estimationDegree: int= 5,
    estimationMaxIterations: int= 10,

    initialStateOffset: NDArray= np.array( [0,0,0,0,0,0] ),

    noiseDict: dict= {},
    intParamsDict: dict= {},

    resultsDir: str= "",
    ) -> None:
    """Performs a set of estimates that vary the observations noise. NOTE this
    does not apply noise on acceleration values, only DSN doppler and sst range
    observations. 

    Args:
        estimator (estimatorClass): Estimator with which the estimation will be \
    performed. 
        observationsList (list[observationsClass]): List with observationClasses 
    for this estimation.
        estimationDegree (int): Highest degree of estimated harmonics. 
        initialStateOffset (NDArray): Initial state offset for each arc. 
        noiseDict (dict): Dictionary of noise values. The keys indicating the name 
    of the observationClass they apply to and the value its standard deviation. 
        resultsDir (str): Results relative directory. 
    
    """

    # Load spice kernels. 
    spice.load_standard_kernels()

    # Creates directory for current day if not existing.
    dayDir = resultsDir + date.today().strftime( "%Y%m%d" ) + "/"
    Path( dayDir ).mkdir( parents= True, exist_ok= True ) 

    # Checks number of run sets within day. 
    setNum = get_last_run_number( 
        runsDir= dayDir,
        prefix= SETPREFIX
    ) 
    # Creates directory for set if not existing. 
    setPath = dayDir + SETPREFIX + f"{setNum + 1}/"
    Path( setPath ).mkdir( parents= True, exist_ok= True )
 
    # Checks value of last individual run. 
    highestRun = get_last_run_number (
        runsDir= SETPREFIX,
        prefix= RUNPREFIX
    )


    # Save propagation parameters. 
    with open( setPath + INTEGRATIONFILE, 'w' ) as file:
        for key, value in intParamsDict.items():
            file.write( f"{key}: {value}\n")
        file.write( f"spacecraft: { len( estimator.environmentReal.spacecrafts ) }")

    # Dependent variables list.
    dependentVariables = [
        dependent_variable.latitude(
            body= estimator.environmentReal.spacecrafts[0].name,
            central_body= estimator.environmentReal.frameOriginBody
        ),
        dependent_variable.longitude(
            body= estimator.environmentReal.spacecrafts[0].name,
            central_body= estimator.environmentReal.frameOriginBody
        )
    ]
    
    # Propagate reality once.
    estimator.propagate_reality(
        initialStateOffset= initialStateOffset,
        dependentVariables= dependentVariables
    )
    # Saves reality propagation to overall run directory. 
    estimator.save_real_propagation(
        fileDir= setPath,
        fileName= REALSTATESFILE
    )
    # Creates shModelClass from reference harmonics.
    harmonicsReal = shModelClass.make_from_environment(
        environment= estimator.environmentReal
    )
    # Convert to pysh harmonics and save. 
    pyshReal = shPyshClass.from_shModelClass( harmonicsReal )
    pyshReal.plot_gravity_anomaly( title= "Real Gravity Anomaly", show= False,
                                   save= True, fileDir= setPath, 
                                   fileName= REALMAPFILE )

    # Initializes observations objects 
    for observation in observationsList: observation.initial_setup()
    
    # Creates list of all possible combinations of given noise values. 
    combinations = list( product( *noiseDict.values() ) )
    # Create index array for tested noise sigmas. 
    testValues = np.empty( (len( combinations ), 2) )

    # NOTE: this is likely the part that would benefit from multithreading.
    # Iterates through all combinations of noise values.    
    i = 0
    for combination in combinations:
        # Startime for process.
        startTime = time.process_time()

        # Current combination linked to keys 
        currentCombination = dict( zip( noiseDict.keys(), combination ) )

        print(f"Combination {i+1} out of {len( combinations )}")
        print(f"Noise vals:{currentCombination}")

        # Individual run directory.
        runDir = setPath +  RUNPREFIX + f"{i+1+highestRun}/"
        # Creates directory if not existing. 
        Path( runDir ).mkdir( parents= True, exist_ok= True ) 

        # Save combination.
        testValues[i,:] = combination

        ### Estimation Process ###
        # Set new noise values. 
        for observation in observationsList: 
            if currentCombination[ observation.name ] > 0:
                observation.set_noise_sigma( noiseSigma= currentCombination[ 
                    observation.name ] 
                )

        # Create observations using noise values. 
        estimator.make_observations(
            observationsList= observationsList,

            weighObservations= True
        )

        # Save observation values. 
        estimator.save_observations(
            fileDir= runDir,
            fileName= OBSERVATIONSFILE
        )
        # Estimate
        estimator.make_estimation(
            maximumIterations= estimationMaxIterations,
            printEstimationOutput= False,
            estimationDegree= estimationDegree
        )
        harmonicsEstimated = shModelClass.make_from_estimate(
            estimator= estimator
        )
        # Save estimated harmonics. 
        harmonicsEstimated.save_coefficients(
            fileDir= runDir,
            fileName= ESTIMATEFILE
        )
        # Save combination to text file.
        noiseDictKeys = list( noiseDict.keys() )
        header = f"{noiseDictKeys[0]},{noiseDictKeys[1]}"
        combinationDir = runDir + NOISEVALSFILE
        np.savetxt( combinationDir, [ combination ], header= header, comments= "",
                   fmt= '%2.4e', delimiter= "," )
        estimator.save_formal_error(
            fileDir= runDir,
            fileName= ERRORSFILE
        )

        # Obtain difference between estimated and real harmonics.
        harmonicsDelta = harmonicsReal.make_from_difference(
            other= harmonicsEstimated
        )
        # Convert to pyshHarmonics
        pyshEstimated = shPyshClass.from_shModelClass( harmonicsEstimated )
        pyshDelta     = shPyshClass.from_shModelClass( harmonicsDelta )
        # Plot and save. 
        pyshEstimated.plot_gravity_anomaly( 
            title= "Estimated Gravity Anomaly", show= False,
            save= True, fileDir= runDir, fileName= ESTIMATEMAPFILE )
        pyshDelta.plot_gravity_anomaly(
            title= "Gravity Anomaly Error", show= False,
            save= True, fileDir= runDir, fileName= ERRORMAPFILE )

        endTime = time.process_time()

        

        # Save runtime and estimation details. 
        with open( runDir + "estimation.txt", 'w' ) as file:
            file.write( f"Estimation took {endTime - startTime} s to complete" )
            file.write( f" - Reality degree: {estimator.harmonicsDegreeReal}")
            file.write( f" - Estimated degree: {estimationDegree}")

        # Saves analysis plots. 
        analysis = analysisLibrary( setDir= runDir )
        analysis.load_propagation( realStatesFile= REALSTATESFILE )
        analysis.plot_observation_density( title= "Observation Density", 
                                           degreeSlice= estimationDegree + 20,
                                           save= True)
        i+=1

def read_observation_noise_estimates(
    runsDir: str,
    runNums: list[int]= [1],
    prefix: str= "run_",
) -> tuple[ list[ shModelClass ], NDArray ]: 
    '''Outputs a list of harmonics objects and structured array of noise values
    for the selected runs. 

    Args:
    - runsDir (str): Folder directory of runs. 
    - runNums (list[int]): List of run numbers you wish to load.
    - prefix (str): OPTIONAL. The prefix of individual run folders. 
    
    '''
    # Empty output lists. 
    harmonicsList = []
    noiseList= []

    for runNum in runNums:
        # Run directory
        runDir = runsDir + prefix + str( runNum ) + '/'

        # Extract harmonics model from each estimates file. 
        harmonicsEstimated = shModelClass.make_from_file(
            filePath= runDir + ESTIMATEFILE
        ) 
        harmonicsList.append( harmonicsEstimated )

        # Read noise file. 
        noiseList.append( np.genfromtxt( runDir + NOISEVALSFILE, delimiter= ',',
                                   names= True )
        )

    # Turn noise list into structured array. 
    noiseVals = np.array( noiseList )
        
    return harmonicsList, noiseVals
