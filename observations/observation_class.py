### OBSERVATION CLASS FILE ###
# This file defines the parent class for observations. 

### Library imports. 
from typing import Sequence, Mapping
from numpy.typing import NDArray

### Local imports.
from bodies.bodies import spacecraft, groundStation, body

### Tudat imports. 
from tudatpy import estimation
from tudatpy.estimation.observations_setup import random_noise
from tudatpy.estimation.observations_setup.observations_simulation_settings import \
    tabulated_simulation_settings, create_observation_simulators
from tudatpy.estimation.observable_models_setup.model_settings import ObservableType, ObservationModelSettings
from tudatpy.estimation.observable_models_setup.links import LinkEndType, LinkDefinition
from tudatpy.estimation.observable_models_setup import links

from tudatpy.dynamics.environment import SystemOfBodies
from tudatpy.estimation.observable_models_setup import light_time_corrections

class observationsClass ():
    # Type of observation.
    observationType: ObservableType

    # Empty list of simulator settings. 
    observationSimulatorSettings = []

    def __init__(
        self,
        transmitters: Sequence[body],
        receivers: Sequence[body],
        times: Sequence[float]) -> None:

        if len( transmitters ) != len( receivers ):
            raise ValueError(
                f"Must have same amount of transmitters and receivers.\n"
                f"Num transmitters:{len( transmitters )} -- Num Receivers:{len( receivers )}"
            )

        self.transmitters = transmitters
        self.receivers = receivers 
        self.times = times

    def make_link_definitions( self ) -> None:

        # Empty link definition list. 
        linkDefinitions = []
        # Emtpy link end IDs dictionary. 
        linkEndIds = dict()

        # Cycles through transmitters. 
        for index, transmitter in enumerate(self.transmitters):
    
            # Checks if the transmitter is a ground station and defines link accordingly.
            # Otherwise, transmitter set to center of mass of transmitter dict object. 
            if isinstance(transmitter, groundStation): 
                linkEndIds[ LinkEndType.transmitter ] = estimation.observable_models_setup.links.body_reference_point_link_end_id( 
                    transmitter.parentBody, transmitter.name
                    )
            else:
                linkEndIds[ LinkEndType.transmitter ] = estimation.observable_models_setup.links.body_origin_link_end_id( 
                    transmitter.name 
                    )
    
            receiver = self.receivers[index]
            # Receiver links. NOTE: Should not be ground station. 
            if not (receiver, spacecraft): 
                raise TypeError(
                    f"Ground stations must be set as transmitters.\n"
                    f"{receiver.name} set as receiver.\n"
                )
            else:
                linkEndIds[ LinkEndType.receiver ] = estimation.observable_models_setup.links.body_origin_link_end_id( 
                    receiver.name 
                    )
    
            # Appends to link definition list
            linkDefinitions.append(
                estimation.observable_models_setup.links.link_definition( linkEndIds ))

        self.linkDefinitions = linkDefinitions

        # Dictionary of observation types and respective link definitions. 
        self.linkEndsPerObservableType = {
            self.observationType: self.linkDefinitions
        }

    # Defined for each different observation model. 
    def make_observation_model_settings( self ) -> None: 

        # Generalized observation model settings. 
        self.observationModelSettings : Sequence[ObservationModelSettings]

        
    # Makes observation simulation settings. Needs observation model settings. 
    def make_observation_simulation_settings(
        self,
        systemOfBodiesReal: SystemOfBodies
    ):

        # Empty light time corrections settings. 
        # NOTE: As of now unused. 
        lightTimeCorrectionSettings = []
    
        # Create observational simulator. 
        self.observationSimulator = create_observation_simulators(
            observation_settings= self.observationModelSettings,
            bodies= systemOfBodiesReal
        )

        # Adds tabulated observation simulator settings for each link.
        for linkDefinition in self.linkDefinitions:
            self.observationSimulatorSettings.append( tabulated_simulation_settings(
                observable_type= self.observationType,
                link_ends= linkDefinition,
                simulation_times= self.times, # type: ignore (Float == time)
                )
            )

        # NOTE: This snippet is commented out as it may not be needed.
        # Previously it solved an issue with the ground-stations causing
        # light-time correction errors that crashed the estimation. 
        # Left here "just in case". 
        """ for observationType in self.linkEndsPerObservableType:
            for linkEndIndex in range( len( self.linkEndsPerObservableType[observationType] ) ):
                # Extracts transmitter name.
                transmitterBody = self.linkEndsPerObservableType[observationType][linkEndIndex].link_end_id(
                    link_end_type= links.LinkEndType.transmitter ).body_name
                
                # If transmitter is Earth, sets reference link to receiver. 
                if transmitterBody == "Earth": referenceLink = LinkEndType.receiver
                else: referenceLink = LinkEndType.transmitter
    
                self.observationSimulatorSettings.append( tabulated_simulation_settings(
                    observable_type= self.observationType,
                    link_ends= self.linkEndsPerObservableType[observationType][linkEndIndex],
                    simulation_times= self.times, # type: ignore (Float == time)
                    # Depending on ground station link end chooses receiver or transmitter. 
                    reference_link_end_type= referenceLink
        ) ) """

    # Adds observation noise to existing simulator settings. 
    def set_observation_simulator_settings_noise(
        self,
        observableTypes: Sequence[ ObservableType ],
        noiseAmplitudes: Sequence[ float ],

    ): pass

    