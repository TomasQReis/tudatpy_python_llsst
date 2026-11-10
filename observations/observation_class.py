### OBSERVATION CLASS FILE ###
# This file defines the parent class for observations. 

### Library imports. 
from typing import Sequence, MutableSequence
from numpy.typing import NDArray

### Local imports.
from bodies.bodies import spacecraft, groundStation, body
from environment.environment import environmentClass

### Tudat imports. 
from tudatpy import estimation
from tudatpy.estimation.observations_setup import \
    random_noise, observations_wrapper
from tudatpy.estimation.observations_setup.observations_simulation_settings import \
    tabulated_simulation_settings, create_observation_simulators

from tudatpy.estimation.observable_models_setup.model_settings import ObservableType, ObservationModelSettings
from tudatpy.estimation.observable_models_setup.links import LinkEndType, LinkDefinition
from tudatpy.estimation.observable_models_setup import links

from tudatpy.dynamics.environment import SystemOfBodies
from tudatpy.estimation.observable_models_setup import light_time_corrections



# Merges a list of observation classes.  
def merge_observations(
        observationList: list[ observationsClass ],
        observationTimes: list[ float ]
    ):
    """Merges separate observation classes into a single one."""

    # Empty lists of class inputs. 
    mergedTransmitters  = []
    mergedReceivers     = []

    # Empty list of observation types. 
    mergedObservationTypes = []

    # Empty list of link definitions.
    mergedLinkDefinitions = []

    # Empty lists of model and simulator settings and simulators. 
    mergedModelSettings     = []
    mergedSimulatorSettings = []

    for observation in observationList:

        # Merges input arguments of class.
        mergedTransmitters.extend( observation.transmitters )
        mergedReceivers.extend( observation.receivers )

        # Creates a list of observation types to match number of links.
        mergedObservationTypes.extend( 
            [ observation.observationType[0] ] * len( observation.linkDefinitions ) )

        # Merges link definitions.
        mergedLinkDefinitions.extend( observation.linkDefinitions )

        # Merges model and simulator settings and simulators. 
        mergedModelSettings.extend( observation.observationModelSettings )
        mergedSimulatorSettings.extend( observation.observationSimulatorSettings )

    # Initializes merged observations class. 
    mergedObservations = observationsClass(
        transmitters= mergedTransmitters,
        receivers= mergedReceivers,
        times= observationTimes,
        environmentReal= observationList[0].environmentReal,
        uniqueObservationType= False
    )

    # Overwrites observation type. 
    mergedObservations.observationType = mergedObservationTypes

    # Overwrites link definitions.
    mergedObservations.linkDefinitions = mergedLinkDefinitions

    # Overwrites simulator and model settings. 
    mergedObservations.observationModelSettings     = mergedModelSettings
    mergedObservations.observationSimulatorSettings = mergedSimulatorSettings

    # Outputs merged observations class. 
    return mergedObservations 

# Checks for ground station link ends. 
def check_ground_station ( linkEnd: body, linkEndType:LinkEndType, linkEndIds: dict ) -> dict:
    """Checks whether the link end is a ground station."""
    if isinstance( linkEnd, groundStation ):
        linkEndIds[ linkEndType ] = estimation.observable_models_setup.links.body_reference_point_link_end_id( 
            linkEnd.parentBody, linkEnd.name
        )
    else:
        linkEndIds[ linkEndType ] = estimation.observable_models_setup.links.body_origin_link_end_id( 
            linkEnd.name
        )
    return linkEndIds


class observationsClass ():
    # Type of observation.
    observationType: list[ ObservableType ]

    # Empty list of simulator settings. 
    observationSimulatorSettings = []

    def __init__(
        self,
        
        
        times: Sequence[float],

        environmentReal: environmentClass,

        transmitters: Sequence[body] = [],
        receivers: Sequence[body] = [],
        linkGroups: Sequence[Sequence[body]] = [[]],

        uniqueObservationType: bool= True) -> None:

        if len( transmitters ) != len( receivers ):
            raise ValueError(
                f"Must have same amount of transmitters and receivers.\n"
                f"Num transmitters:{len( transmitters )} -- Num Receivers:{len( receivers )}"
            )

        self.transmitters = transmitters
        self.receivers = receivers  
        self.linkGroups = linkGroups

        self.times = times

        self.environmentReal = environmentReal

        # If unique type, makes link definitions and model settings immediately. 
        if uniqueObservationType:
            self.make_link_definitions()
            self.make_model_settings()

    def make_link_definitions( self ) -> None:

        
        # Emtpy link end IDs dictionary. 
        linkEndIds = dict()
        # Empty link definition list.
        linkDefinitions = []

        # Iterates through lists of link Ends (groups). 
        for groupIndex in range( len( self.linkGroups ) ):
            
            # Checks number of link ends.
            if len( self.linkGroups[groupIndex] ) > 2:
                # Sets transmitter.
                linkEndIds = check_ground_station(
                    linkEnd= self.linkGroups[groupIndex][0],
                    linkEndType= LinkEndType.transmitter,
                    linkEndIds= linkEndIds
                ) 
                # Sets intermediate ends as retransmitters. 
                for retransmitterLinks in self.linkGroups[groupIndex][1:-1]:
                    linkEndIds = check_ground_station(
                        linkEnd= retransmitterLinks,
                        linkEndType= LinkEndType.retransmitter,
                        linkEndIds= linkEndIds
                    )
                # Sets receiver. 
                linkEndIds = check_ground_station(
                    linkEnd= self.linkGroups[groupIndex][-1],
                    linkEndType= LinkEndType.receiver,
                    linkEndIds= linkEndIds
                )
            else: # Sets link end Ids for a one-way link.
                # Sets transmitter.
                linkEndIds = check_ground_station(
                    linkEnd= self.linkGroups[groupIndex][0],
                    linkEndType= LinkEndType.transmitter,
                    linkEndIds= linkEndIds
                )
                # Sets receiver. 
                linkEndIds = check_ground_station(
                    linkEnd= self.linkGroups[groupIndex][-1],
                    linkEndType= LinkEndType.receiver,
                    linkEndIds= linkEndIds
                )
                
            # Link definition list. 
            linkDefinitions.append( estimation.observable_models_setup.links.link_definition( linkEndIds ) )

        self.linkDefinitions = linkDefinitions

    # Defined for each different observation model. 
    def make_model_settings( self ) -> None: 

        # Generalized observation model settings. 
        self.observationModelSettings : Sequence[ObservationModelSettings]

    # Makes observation simulation settings. Needs observation model settings. 
    def make_simulation_settings(
        self,
    ):

        # Empty light time corrections settings. 
        # NOTE: As of now unused. 
        lightTimeCorrectionSettings = []
    
        # Create observational simulator. 
        self.observationSimulator = create_observation_simulators(
            observation_settings= self.observationModelSettings,
            bodies= self.environmentReal.systemOfBodies
        )

        # Adds tabulated observation simulator settings for each link.
        if len( self.observationType ) > 1:
            for typeIndex, linkDefinition in enumerate( self.linkDefinitions ):
                self.observationSimulatorSettings.append( tabulated_simulation_settings(
                    observable_type= self.observationType[typeIndex],
                    link_ends= linkDefinition,
                    simulation_times= self.times, # type: ignore (Float == time)
                    )
                )
        else:
            for linkDefinition in self.linkDefinitions:
                self.observationSimulatorSettings.append( tabulated_simulation_settings(
                    observable_type= self.observationType[0],
                    link_ends= linkDefinition,
                    simulation_times= self.times, # type: ignore (Float == time)
                    )
                )

        # NOTE: The following snippet is commented out as it may not be needed.
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

    def simulate_observation( self ):
        """Simulates observations provided simulator and its settings have been
        previously created."""

        self.simulatedObservations = observations_wrapper.simulate_observations(
            simulation_settings= self.observationSimulatorSettings,
            observation_simulators= self.observationSimulator,
            bodies= self.environmentReal.systemOfBodies
        )

        return self.simulatedObservations
        

    # Adds observation noise to existing simulator settings. 
    def set_simulator_settings_noise(
        self,
        observationType: ObservableType,
        noiseSigma: float,
    ):
        # Stores types of each simulator settings object.
        types = ( self.observationType * len( self.observationSimulatorSettings )
            if len( self.observationType ) == 1 else self.observationType )

        # Iterates through simulator settings and adds noise to matching observation types.
        for currentType, currentLinkDefinition in zip( 
            types, self.linkDefinitions, strict= True ):
            if currentType == observationType:
                random_noise.add_gaussian_noise_to_observable_for_link_ends(
                    observation_simulation_settings_list= self.observationSimulatorSettings,
                    noise_amplitude= noiseSigma,
                    observable_type= observationType,
                    link_definition= currentLinkDefinition
                )

    def set_simulator_settings_ancillary(
        self,
        ancillaryObsType: ObservableType,
        ancillarySettings
    ) -> None: 

        # Stores types of each simulator settings object.
        types = ( self.observationType * len( self.observationSimulatorSettings )
            if len( self.observationType ) == 1 else self.observationType )

        # Sweeps through types and adds ancillary to matching settings. 
        for observationType, settings in zip( types, self.observationSimulatorSettings, strict= True ):
            if observationType == ancillaryObsType:
                settings.ancillary_settings = ancillarySettings



        

        

        

