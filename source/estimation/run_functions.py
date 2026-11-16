### Library imports
import numpy as np
from numpy.typing import NDArray
from itertools import product

### Local imports
from source.estimation.estimator_class import estimatorClass
from source.observations.observation_class import observationsClass
from source.environment.harmonics_class import shModelClass


def estimate_with_observation_noise(
    estimator: estimatorClass, 
    observationsList: list[ observationsClass ], 

    initialStateOffset: NDArray= np.array( [0,0,0,0,0,0] ),

    noiseDict: dict= {},

    resultsDir: str= "",
    runsDir: str= "",
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

    # Creates directory for current day if not existing.
    # TODO 

    # Saves reality propagation to overall run directory. 
    estimator.save_real_propagation(
        fileDir= resultsDir + runsDir,
        fileName= "reality_states"
    )

    ### Nested for loops
    # NOTE: this is likely the part that would benefit from multithreading. 
    # Iterates through all combinations of noise values. 
    i = 0
    for combination in product( *noiseDict.values() ):
        # Individual run directory.
        runDir = f"run_noise_{i+1}/"

        # Save combination.
        testValues[i,:] = combination
        i+=1

        currentCombination = dict( zip( noiseDict.keys(), combination ) )

        print( currentCombination )

        # Set new noise values. 
        for observation in observationsList: 
            observation.set_noise_sigma( noiseSigma= currentCombination[ observation.name ] )

        # Create observations using noise values. 
        estimator.make_observations(
            observationsList= observationsList
        )

        # Save observation values. 
        estimator.save_observations(
            fileDir= resultsDir + runsDir + runDir,
            fileName= f"observations"
        )
            
        # Estimate
        estimator.make_estimation(
            maximumIterations= 10,
            printEstimationOutput= False
        )

        # Save to array
        estimatedHarmonics = shModelClass.make_from_estimate(
            estimator= estimator
        )
        estimatedHarmonics.save_coefficients(
            fileDir= resultsDir + runsDir + runDir,
            fileName= f"estimated_harmonics"
        )

# Output array

