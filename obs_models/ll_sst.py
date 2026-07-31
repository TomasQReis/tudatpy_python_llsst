# This file defines all code used for ll-sst observations. 
# This includes links setup, observation model setup and simulated observations
# code. 

# Tudat imports. 
from tudatpy import estimation
from tudatpy.estimation.observable_models_setup.links import LinkEndType
from tudatpy.dynamics.environment import SystemOfBodies

###---------------------------------------------
### One-way range observation model functions
###---------------------------------------------

# One-way range link creation. 
def link_creation_owr(
        transmitterDict: dict, 
        receiverDict: dict, 
        gSTransmitter: bool= False):
    """
    Creates link ends for one-way range observables. 
    Args:
        transmitter (dict): Dictionary containing transmitter properties. Accepts ground station and spacecraft dictionaries as formatted in the vehicles file.
        receiver (dict): Dictionary containing receiver properties. Accepts ground station and spacecraft dictionaries as formatted in the vehicles file.
        gSTransmitter (bool): True when transmitter is a ground station. 
    Returns:
        owrLinkDefinition (LinkDefinition): Link definition for owr observational model. 
    """
    # Empty dictionary
    owrLinks = dict()

    # Checks if the transmitter is a ground station and defines link accordingly.
    # Otherwise, transmitter set to center of mass of transmitter dict object. 
    if gSTransmitter:
        owrLinks[ LinkEndType.transmitter ] = estimation.observable_models_setup.links.body_reference_point_link_end_id( 
            "Earth", transmitterDict[ "name" ] 
            )
    else:
        owrLinks[ LinkEndType.transmitter ] = estimation.observable_models_setup.links.body_origin_link_end_id( 
            receiverDict[ "name" ] 
            )

    # Receiver link.
    owrLinks[ LinkEndType.receiver ] = estimation.observable_models_setup.links.body_origin_link_end_id( 
        receiverDict[ "name" ] 
        )

    # Link definition 
    owrLinkDefinition = estimation.observable_models_setup.links.link_definition( owrLinks )

    return owrLinkDefinition

# One-way range observation model simulator.
# TODO: Implement light-time corrections, noise and bias (Later version)
def observation_model_simulator_owr(
        owrLinkDefinition: estimation.observable_models_setup.links.LinkDefinition,
        bodies: SystemOfBodies):

    # Observation settings list. 
    owrObservationSettings = []
    owrObservationSettings.append( estimation.observable_models_setup.model_settings.one_way_range( 
        owrLinkDefinition,
        light_time_correction_settings= [],
    ))

    # Create observational simulator. 
    owrObservationSimulator = estimation.observations_setup.observations_simulation_settings.create_observation_simulators(
        observation_settings= owrObservationSettings,
        bodies= bodies
    )

    return owrObservationSimulator
