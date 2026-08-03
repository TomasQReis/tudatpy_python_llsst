# This file defines all code used for ll-sst observations. 
# This includes links setup, observation model setup and simulated observations
# code. 

# Tudat imports. 
from tudatpy import estimation
from tudatpy.estimation.observable_models_setup import links
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
            transmitterDict[ "name" ] 
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
    """
    Creates an observation simulator for later use in either estimating 
    parameters or simulating observations. 
    Args:
        owrLinkDefinition (LinkDefinition): LinkDefinition object created with the correspoding link creation function.
        bodies (SystemOfBodies): SystemOfBodies object used in the observations model.
    Returns:
        owrObservationSimulator (list[ObservationSimulator]): List of ObservationSimulators to be used in estimation or simulating observations. 
    """

    """ # First order Sun-dependent relativistic light-time correction settings. 
    lightTimeCorrectionSettings = [ 
        estimation.observable_models_setup.light_time_corrections.light_time_convergence_settings( 
            maximum_number_of_iterations= 100
         ) 
    ] """
    # Empty light time corrections settings. 
    lightTimeCorrectionSettings = []

    # Observation settings list. 
    owrObservationSettings = []
    owrObservationSettings.append( estimation.observable_models_setup.model_settings.one_way_range( 
        owrLinkDefinition,
        light_time_correction_settings= lightTimeCorrectionSettings,
        ),
    )

    # Create observational simulator. 
    owrObservationSimulator = estimation.observations_setup.observations_simulation_settings.create_observation_simulators(
        observation_settings= owrObservationSettings,
        bodies= bodies
    )

    return owrObservationSimulator, owrObservationSettings

# Create parameters for the simulated observations. 
def simulate_observations_owr(
        observationTimes: list,
        owrLinkDefinition: estimation.observable_models_setup.links.LinkDefinition,
        owrObservationSimulator: list[estimation.observable_models.observables_simulation.ObservationSimulator],
        bodies: SystemOfBodies,
):
    """
    Performs the observations simulation.
    Args:
        observationTimes (list): List of floats with the observation times given in seconds since J2000.
        owrLinkDefintion (LinkDefinition): LinkEnds definition as given by the link_creation_owr function.
        owrObservationsSimulator: (list): List of ObservationSimulator as given by the estimator property observation_simulators or the create_observation_simulators function.
        bodies (SystemOfBodies): System of bodies for the observation model environment. 
    Returns:
        owrSimulatedObservations (ObservationCollection): Simulated observations object. 
        owrSimulatedObservationsDependentVars (NDArray): Dependent variables from the observations simulation. 
    """
    
    # Create simulated observations settings. 
    owrSimulatedObservationSettings = estimation.observations_setup.observations_simulation_settings.tabulated_simulation_settings(
        observable_type= estimation.observable_models_setup.model_settings.one_way_range_type,
        link_ends= owrLinkDefinition,
        simulation_times= observationTimes,
    )

    # NOTE: Additional simulated observation settings should be added here
    # after the nominal settings are created.
    # Adds range between links dependent variable. 
    dependentVariableRangeSettings = estimation.observations_setup.observations_dependent_variables.target_range_between_link_ends_dependent_variable()
    dependentVariableCoGRangeSettings = estimation.observations_setup.observations_dependent_variables.body_center_distance_dependent_variable(
        body_name= "rociA",
        start_link_end_id= owrLinkDefinition.link_end_id( LinkEndType.transmitter ),
        end_link_end_id= owrLinkDefinition.link_end_id( LinkEndType.receiver )
    )
    estimation.observations_setup.observations_dependent_variables.add_dependent_variables_to_all(
        dependent_variable_settings= [ dependentVariableRangeSettings ],
        observation_simulation_settings= [ owrSimulatedObservationSettings ],
        bodies= bodies
    )


    # Simulates observations. 
    owrSimulatedObservations = estimation.observations_setup.observations_wrapper.simulate_observations(
        simulation_settings= [ owrSimulatedObservationSettings ],
        observation_simulators= owrObservationSimulator,
        bodies= bodies
    )

    # Retrieves dependent variables. 
    owrSimulatedObservationsDependentVars = owrSimulatedObservations.dependent_variable(
        dependent_variable_settings= dependentVariableRangeSettings
    )

    return owrSimulatedObservations, owrSimulatedObservationsDependentVars