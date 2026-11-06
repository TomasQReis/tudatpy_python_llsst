### OBSERVATION CLASS FILE ###
# This file defines the parent class for observations. 

### Library imports. 
from typing import Sequence, Mapping

### Self-made imports.
from bodies.bodies import spacecraft, groundStation, body

### Tudat imports. 
from tudatpy import estimation
from tudatpy.estimation.observations_setup import random_noise
from tudatpy.estimation.observations_setup.observations_simulation_settings import tabulated_simulation_settings

from tudatpy.estimation.observable_models_setup.model_settings import ObservableType
from tudatpy.estimation.observable_models_setup.links import LinkEndType, LinkDefinition
from tudatpy.estimation.observable_models_setup import links

from tudatpy.dynamics.environment import SystemOfBodies
from tudatpy.estimation.observable_models_setup import light_time_corrections

class observationsClass ():
    # Type of observation.
    observationType = None

    def __init__(
        self,
        transmitters: Sequence[body],
        receivers: Sequence[body]) -> None:

        if len( transmitters ) != len( receivers ):
            raise ValueError(
                f"Must have same amount of transmitters and receivers.\n"
                f"Num transmitters:{len( transmitters )} -- Num Receivers:{len( receivers )}"
            )

        self.transmitters = transmitters
        self.receivers = receivers 

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
