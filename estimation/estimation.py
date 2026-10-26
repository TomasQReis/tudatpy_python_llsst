### Tudat imports. 

### Self-made imports. 
from environment.environment import environmentClass 
# TODO: Would be nice to have these in the estimator class or part of their own class. 
# Just make them modular and easy to access...
from obs_models.ll_sst import link_creation_one_way, observation_model_simulator_owr,\
    simulate_observations_owr, extract_data_observations_owr

### External imports.
import numpy as np


class estimator ():
    def __init__(
        self,
        referenceEnvironment: environmentClass,
        estimationEnvironment: environmentClass,

        referenceHarmonicsDegree: int= 10,
        estimationHarmonicsDegree: int= 10
    ) -> None:

        self.referenceEnvironment   = referenceEnvironment
        self.estimationEnvironment  = estimationEnvironment

        self.referenceHarmonicsDegree = referenceHarmonicsDegree
        self.estimationHarmonicsDegree = estimationHarmonicsDegree
    def make_estimator_observations (
            self,
    ):
        ### Propagate reality 
        self.referenceEnvironment.make_propagation_settings(
            harmonicsDegree= self.referenceHarmonicsDegree,
            arcTimeLength= 0.0,
            keepEnvironment= True, 
            skipArcCheck= True      # TODO: Remove after testing. 
        )

        # Save propagation results. 
        self.referenceResults = self.referenceEnvironment.propagate()

        ### Simulate observations. 
        # Observation epoch. 
        # TODO: Generalize epoch margin for light-time. 
        observationEpochMargin = self.referenceEnvironment.timeStep * 10
        observationEpochStart = self.referenceEnvironment.simStartEpoch + observationEpochMargin
        observationEpochEnd = self.referenceEnvironment.simEndEpoch - observationEpochMargin

        observationEpochs = np.arange( float(observationEpochStart), 
                                      step= float(self.estimationEnvironment.timeStep) , 
                                      stop= float(observationEpochEnd) ) 

        # Link definition. One way range. 
        # TODO: Make a modular way for selecting observation pairs. 
        receivers = self.referenceEnvironment.spacecrafts
        transmitters = [self.referenceEnvironment.groundStations[0], 
                        self.referenceEnvironment.groundStations[0]]

        # Create observation links.
        observationType, observationLinkDefintions = link_creation_one_way(
            transmitters= transmitters,
            receivers= receivers
        )

        # Create observation model simulator.
        observationSimulator, observationSettings = observation_model_simulator_owr(
            owrLinkDefinitions= observationLinkDefintions,
            bodies= self.referenceEnvironment.systemOfBodies
        )

        # Dictionary of observation types and their respective link definitions. 
        linkEndsPerObservable = {
            observationType: observationLinkDefintions
        }

        # TODO: Generalize noise input for observations. 
        noiseAmplitude = 0.0

        # Simulate observations.
        simulatedObservationsNoisy = simulate_observations_owr(
            observationTimes= observationEpochs.tolist(),
            linkEndsPerObservatble= linkEndsPerObservable,
            owrObservationSimulator= observationSimulator,
            bodies= self.referenceEnvironment.systemOfBodies,
            noiseAmplitude= noiseAmplitude
        )

        ### Save observations. 
        # TODO: Generalize for all transmitters. 
        self.observations, self.observationTimes = extract_data_observations_owr(
            observationCollection= simulatedObservationsNoisy,
            transmitter= self.referenceEnvironment.spacecrafts[0]
        )




