### VERIFICATION ESTIMATION SET ###
# Zero noise and position offset. 
# Varies total time of simulation and maximum degree estimated. 


### Local imports. 
from src.environment.environment import convert_to_j2000, GGRX420L
from src.environment.moon_environment import moonEnvironment

from src.observations.observation_class import observationsClass
from src.observations.n_way_doppler import \
    oneWayDopplerObservationsClass

from src.bodies.grail_spacecraft import grailList
from src.bodies.ground_stations import grazStation

from src.estimation.estimator_class import estimatorClass

from src.observations.validation_models import \
    sstLinks, dsnXBandLinks, DSNSIGMA, DSNCOUNT, KBRRSIGMA, KBRRCOUNT

### External library imports.
import numpy as np

### ESTIMATION SET VALUES ###
# Parameters, simulation length.

sim1 = {'sim_duration':6 * 24*60**2}
sim2 = {'sim_duration':12 * 24*60**2}
sim3 = {'sim_duration':24 * 24*60**2}
sim4 = {'sim_duration':48 * 24*60**2}

simDurationList = [sim1, sim2]

# Max degrees.
environmentDegree   = 40
estimatedDegree     = 40

stateOffset = np.zeros(6) 

### Environment and estimation parameters.
# Initial epoch. 
simStartDate    = [2001, 1, 1, 0, 0, 0]
simStartEpoch= convert_to_j2000(simStartDate)

# Placeholder final epoch 
simEndEpoch= simStartEpoch + 1 * (24*60**2)

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

# Environment definition.
environmentReality = moonEnvironment(
    level= 3,
    simStartEpoch= intParamsDict["startEpoch"],   # type: ignore
    simEndEpoch= intParamsDict["endEpoch"],       # type: ignore
    timeStep= intParamsDict['timeStep'],         # type: ignore

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

    spacecrafts= grailList,
    groundStations= [ grazStation ],

    customHarmonicsBool= True,
    customHarmonicsFile= GGRX420L,
    harmonicsMaxDegree= environmentDegree,
)

### Observations objects. 
grailSSTObservations = oneWayDopplerObservationsClass(
    environmentReal= environmentReality,
    linkGroups= sstLinks,

    noiseSigma= 0.0,
    countTime= KBRRCOUNT,
    epochMargin= 1*60**2,

    name= 'sst_range'
)
grailDSNObservations = oneWayDopplerObservationsClass(
    environmentReal= environmentReality,
    linkGroups= dsnXBandLinks,

    noiseSigma= 0.0,
    countTime= DSNCOUNT,
    epochMargin= 1*60**2,

    name= 'dsn_doppler'
)
observationsList: list[ observationsClass ]
observationsList = [grailSSTObservations, grailDSNObservations]

# Noise dictionary
observationsDict = {
    'sst_range': 0.0,
    'dsn_doppler': 0.0
}


### Estimator object.
estimator = estimatorClass(
    environmentReal= environmentReality,
    environmentReference= environmentReference,

    arcLengthReal= intParamsDict["arcLength"],
    arcLengthReference= intParamsDict["arcLength"],

    harmonicsDegreeReal= environmentDegree,
    harmonicsDegreeReference= environmentDegree
)