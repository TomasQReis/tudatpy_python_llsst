### Local imports. 
from src.environment.environment import *
from src.environment.moon_environment import moonEnvironment

from src.observations.n_way_doppler import \
    oneWayDopplerObservationsClass

from src.bodies.bodies import *
from src.bodies.roci_ab import *
from src.bodies.grail_spacecraft import grailList
from src.bodies.ground_stations import grazStation

from src.estimation.estimator_class import estimatorClass
from src.estimation.run_functions import *
from src.estimation.run_setups.zero_noise import \
    estimator, simDurationList, observationsList, observationsDict, stateOffset, \
    environmentReality

from src.estimation.analysis import *

from src.observations.validation_models import \
    sstLinks, dsnXBandLinks, DSNSIGMA, DSNCOUNT, KBRRSIGMA, KBRRCOUNT

### External library imports.
import numpy as np

### Tudat imports


### Directories 
# Data directory. 
resultsDir = "results/"

if __name__ == "__main__":

    if externalSimArgs := False:

        thisSet = simTimeSet(
        resultsPath= 'results/',
        setParamsList= simDurationList
        )
        thisSet.set_estimator( estimator= estimator,
            observationsList= observationsList )
        thisSet.set_dependent_variables(
            mainSpacecraftName= grailList[0].name,
            centralBodyName= 'Moon'
        ) 
        thisSet.run_set( initialStateOffset= stateOffset, maxIterations= 15,
                         estimatedDegree= 10, observationsDict= observationsDict )


    ### TEST WITH A LIST OF SIMULATION TOTAL TIMES ###
    if iterateSimulationTime:= True:

        simLength = 14      # Days

        # Max degrees.
        environmentDegree   = 10
        estimatedDegree     = 10


        baselineOffset = np.array( [ 10, 10, 10, 0.001, 0.001, 0.001 ] )
        
        ### Environment and estimation parameters.
        # Initial epoch. 
        simStartDate    = [2001, 1, 1, 0, 0, 0]
        simStartEpoch= convert_to_j2000(simStartDate)

        # Final Epoch 
        simEndEpoch= simStartEpoch + simLength * (24*60**2)

        # Simulation arcLengths
        arcLength = 24 * (60**2) 

        # Propagation time step
        propTimeStep = 60*6     # s 

        intParamsDict = {
            'startEpoch': simStartEpoch,
            'endEpoch': simEndEpoch,
            'arcLength': arcLength,
            'timeStep': propTimeStep
        }
        
        # Dictionary of noise values. 

        noise1 = { 'sst_range_noise': 0.0, 'doppler_noise': 0.0 }
        noise2 = { 'sst_range_noise': KBRRSIGMA, 'doppler_noise': DSNSIGMA }
        noise3 = { 'sst_range_noise': KBRRSIGMA*2, 'doppler_noise': DSNSIGMA*2 }
        noise4 = { 'sst_range_noise': KBRRSIGMA*4, 'doppler_noise': DSNSIGMA*4 }

        noiseList = [ noise1 ]

        noiseDict  = {
            'sst_range_noise' : [KBRRSIGMA],
            'doppler_noise' : [DSNSIGMA]
        }
        # Initial state offset for each arc. 
        initialStateOffset = np.array( [1, 1, 1, 1e-3, 1e-3, 1e-3] ) # [m,m,m,m/s,m/s,m/s]

        # Environment definition.
        environmentReality = moonEnvironment(
            level= 3,
            simStartEpoch= intParamsDict["startEpoch"],   # type: ignore
            simEndEpoch= intParamsDict["endEpoch"],       # type: ignore
            timeStep= 60*3,         # type: ignore

            arcTimeLength= 0.0,
            skipArcCheck= True,

            spacecrafts= grailList,
            groundStations= [ grazStation ],

            customHarmonicsBool= True,
            customHarmonicsFile= GGRX420L,
            harmonicsMaxDegree= environmentDegree,
        )
        environmentReference = moonEnvironment(
            level= 3,
            simStartEpoch= intParamsDict["startEpoch"],   # type: ignore
            simEndEpoch= intParamsDict["endEpoch"],       # type: ignore
            timeStep= intParamsDict['timeStep'],         # type: ignore

            arcTimeLength= intParamsDict["arcLength"],
            skipArcCheck= True,

            spacecrafts= grailList,
            groundStations= [ grazStation ],

            customHarmonicsBool= True,
            customHarmonicsFile= GGRX420L,
            harmonicsMaxDegree= environmentDegree,
        )


        # Observations 
        ### Observations objects. 
        grailSSTObservations = oneWayDopplerObservationsClass(
            environmentReal= environmentReality,
            linkGroups= sstLinks,

            noiseSigma= 0.0,
            countTime= KBRRCOUNT,
            epochMargin= 1*60**2,

            name= 'sst_range_noise'
        )
        grailDSNObservations = oneWayDopplerObservationsClass(
            environmentReal= environmentReality,
            linkGroups= dsnXBandLinks,

            noiseSigma= 0.0,
            countTime= DSNCOUNT,
            epochMargin= 1*60**2,

            name= 'doppler_noise'
        )

        ### Estimator object.
        estimator = estimatorClass(
            environmentReal= environmentReality,
            environmentReference= environmentReference,

            arcLengthReal= 0.0,
            arcLengthReference= intParamsDict["arcLength"],

            harmonicsDegreeReal= environmentDegree,
            harmonicsDegreeReference= environmentDegree
        )

        thisSet = noiseSet(
            resultsPath= 'results/',
            setParamsList= noiseList
        )
        thisSet.set_estimator( estimator= estimator,
            observationsList= [grailSSTObservations, grailDSNObservations] )
        thisSet.set_dependent_variables(
            mainSpacecraftName= grailList[0].name,
            centralBodyName= 'Moon'
        ) 
        thisSet.run_set( initialStateOffset= np.zeros(6), 
                         maxIterations= 10,
                         estimatedDegree= 10 )
