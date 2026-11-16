### Library imports
import numpy as np
import re
from numpy.typing import NDArray
from itertools import product
from datetime import date
from pathlib import Path

### Local imports
from source.estimation.estimator_class import estimatorClass
from source.observations.observation_class import observationsClass
from source.environment.harmonics_class import shModelClass


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

    initialStateOffset: NDArray= np.array( [0,0,0,0,0,0] ),

    noiseDict: dict= {},

    resultsDir: str= "",
    ) -> None:
    """Performs a set of estimates that vary the observations noise. NOTE this
    does not apply noise on acceleration values, only DSN doppler and sst range
    observations. Returns two arrays with the stored noise combinations and 

    Args:
    - estimator (estimatorClass): Estimator with which the estimation will be \
    performed. 
    - observationsList (list[observationsClass]): List with observationClasses 
    for this estimation.
    - estimationDegree (int): Highest degree of estimated harmonics. 
    - initialStateOffset (NDArray): Initial state offset for each arc. 
    - noiseDict (dict): Dictionary of noise values. The keys indicating the name 
    of the observationClass they apply to and the value its standard deviation. 
    - resultsDir (str): Results relative directory. 
    
    """

    # Creates directory for current set of runs if not existing.
    dayDir = resultsDir + date.today().strftime( "%Y%m%d" ) + "/"
    Path( dayDir ).mkdir( parents= True, exist_ok= True ) 
    # Checks for previous noise runs. 
    noiseRunsDirPrefix = "noise_runs_"
    noiseRunsNum = get_last_run_number( 
        runsDir= dayDir,
        prefix= noiseRunsDirPrefix
    ) 
    # Creates directory for noise runs if not existing. 
    runsDir = dayDir + noiseRunsDirPrefix + f"{noiseRunsNum + 1}/"
    Path( runsDir ).mkdir( parents= True, exist_ok= True ) 
    # Checks value of last individual run. 
    runDirPrefix = "run_"
    highestRun = get_last_run_number (
        runsDir= runsDir,
        prefix= runDirPrefix
    )

    # Create index array for tested noise sigmas. 
    testValues = np.empty( (len( noiseDict.values() ), 2) )
    
    # Propagate reality once.
    estimator.propagate_reality(
        initialStateOffset= initialStateOffset
    )
    # Saves reality propagation to overall run directory. 
    estimator.save_real_propagation(
        fileDir= runsDir,
        fileName= "reality_states"
    )

    # Initializes observations objects 
    for observation in observationsList: observation.initial_setup()

    # NOTE: this is likely the part that would benefit from multithreading. 
    # Iterates through all combinations of noise values. 
    i = 0
    combinations = list( product( *noiseDict.values() ) )
    for combination in combinations:
        # Current combination linked to keys 
        currentCombination = dict( zip( noiseDict.keys(), combination ) )

        print(f"Combination {i+1} out of {len( combinations )}")
        print(f"Noise vals:{currentCombination}")

        # Individual run directory.
        runDir = runsDir +  runDirPrefix + f"{i+1+highestRun}/"
        # Creates directory if not existing. 
        Path( runDir ).mkdir( parents= True, exist_ok= True ) 

        # Save combination.
        testValues[i,:] = combination

        ### Estimation Process ###
        # Set new noise values. 
        for observation in observationsList: 
            observation.set_noise_sigma( noiseSigma= currentCombination[ observation.name ] )

        # Create observations using noise values. 
        estimator.make_observations(
            observationsList= observationsList
        )

        # Save observation values. 
        estimator.save_observations(
            fileDir= runDir,
            fileName= f"observations"
        )
        # Estimate
        estimator.make_estimation(
            maximumIterations= 10,
            printEstimationOutput= False,
            estimationDegree= estimationDegree
        )
        estimatedHarmonics = shModelClass.make_from_estimate(
            estimator= estimator
        )
        # Save estimated harmonics. 
        estimatedHarmonics.save_coefficients(
            fileDir= runDir,
            fileName= f"estimated_harmonics"
        )
        # Save combination to text file.
        noiseDictKeys = list( noiseDict.values() )
        header = f"{noiseDictKeys[0]},{noiseDictKeys[1]}"
        combinationDir = runDir + "noise_values.csv"
        np.savetxt( combinationDir, combination, header= header, comments= "",
                   delimiter= ",")

        i+=1
