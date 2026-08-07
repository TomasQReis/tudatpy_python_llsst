# This file defines all code used for ll-sst observations. 
# This includes links setup, observation model setup and simulated observations
# code. 

### Self-made imports.
from vehicles.vehicles_common import spacecraft

### Tudat imports. 
from tudatpy import estimation
from tudatpy.estimation.observations_setup import random_noise
from tudatpy.estimation.observable_models_setup.links import LinkEndType
from tudatpy.dynamics.environment import SystemOfBodies

###---------------------------------------------
### One-way range observation model functions
###---------------------------------------------

# One-way range link creation. 
def link_creation_owr(
        transmitter: spacecraft, 
        receiver: spacecraft, 
        gSTransmitter: bool= False):
    """
    Creates link ends for one-way range observables. 
    Args:
        transmitter (spacecraft): Spacecraft object containing transmitter properties.
        receiver (spacecraft): Spacecraft containing receiver properties.
        gSTransmitter (bool): True when transmitter is a ground station. 
    Returns:
        owrLinkDefinition (LinkDefinition): Link definition for owr observational model. 
    """
    # Empty dictionary
    owrLinks = dict()

    # Checks if the transmitter is a ground station and defines link accordingly.
    # Otherwise, transmitter set to center of mass of transmitter dict object. 
    if gSTransmitter:
        # NOTE: Might have to change stuff so that this can be generalized to a ground station. 
        owrLinks[ LinkEndType.transmitter ] = estimation.observable_models_setup.links.body_reference_point_link_end_id( 
            "Earth", transmitter.name
            )
    else:
        owrLinks[ LinkEndType.transmitter ] = estimation.observable_models_setup.links.body_origin_link_end_id( 
            transmitter.name 
            )

    # Receiver link.
    owrLinks[ LinkEndType.receiver ] = estimation.observable_models_setup.links.body_origin_link_end_id( 
        receiver.name 
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

    # Empty light time corrections settings. 
    lightTimeCorrectionSettings = []

    # Observation settings list. 
    owrObservationSettings = []
    owrObservationSettings.append( estimation.observable_models_setup.model_settings.one_way_range( 
        owrLinkDefinition,
        ),
    )

    ### NOTE: Temporary
    # Creates new set of link definition for Graz station.
    dopplerLinks = dict()
    dopplerLinks[ LinkEndType.transmitter ] = estimation.observable_models_setup.links.body_reference_point_link_end_id( 
                "Earth", "Graz")
    dopplerLinks[ LinkEndType.receiver ] = estimation.observable_models_setup.links.body_origin_link_end_id( 
        "rociA" 
        )
    dopplerLinksDefinition = estimation.observable_models_setup.links.link_definition( dopplerLinks )

    # Adds one way range measurement. 
    owrObservationSettings.append( estimation.observable_models_setup.model_settings.one_way_range(
        link_ends= dopplerLinksDefinition
    ) )
    # Adds instantaneous way doppler measurement. 
    owrObservationSettings.append( estimation.observable_models_setup.model_settings.one_way_doppler_instantaneous(
        link_ends= dopplerLinksDefinition
    ))
    

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
        noiseAmplitude: float= 0.0
):
    """
    Performs the observations simulation.
    Args:
        observationTimes (list): List of floats with the observation times given in seconds since J2000.
        owrLinkDefintion (LinkDefinition): LinkEnds definition as given by the link_creation_owr function.
        owrObservationsSimulator: (list): List of ObservationSimulator as given by the estimator property observation_simulators or the create_observation_simulators function.
        bodies (SystemOfBodies): System of bodies for the observation model environment. 
        noiseAmplitude (float): Standard deviation defining the un-biased Gaussian distribution for the noise. 
    Returns:
        owrSimulatedObservations (ObservationCollection): Simulated observations object. 
        owrSimulatedObservationsDependentVars (NDArray): Dependent variables from the observations simulation. 
    """
    
    # Create simulated observations settings. 
    owrSimulatedObservationSettings = estimation.observations_setup.observations_simulation_settings.tabulated_simulation_settings(
        observable_type= estimation.observable_models_setup.model_settings.one_way_range_type,
        link_ends= owrLinkDefinition,
        simulation_times= observationTimes,
        reference_link_end_type= estimation.observable_models_setup.links.transmitter
    )

    ### -----------------------------------------------------------------------
    ### NOTE: Additional simulated observation settings should be added here
    ### after the nominal settings are created.

    if noiseAmplitude != 0.0:
        print("Adding noise to observations.")
        # Adds random noise to the observations simulator. 
        random_noise.add_gaussian_noise_to_all(
            observation_simulation_settings_list= [ owrSimulatedObservationSettings ],
            noise_amplitude= noiseAmplitude
        )
    
    ### -----------------------------------------------------------------------

    # Simulates observations. 
    owrSimulatedObservations = estimation.observations_setup.observations_wrapper.simulate_observations(
        simulation_settings= [ owrSimulatedObservationSettings ],
        observation_simulators= owrObservationSimulator,
        bodies= bodies
    )

    return owrSimulatedObservations


# Extract specific values from observation simulations.  
def extract_data_observations_owr(
        observationCollection: estimation.observations.ObservationCollection,
):
    """
    Extracts subset of data from simulated observations. 
    Args:
        observationCollection (ObservationCollection): Simulated observations object. 
    Returns:
        observationValues (NDArray): Values extracted from the simulated observations. 
        observationTimes (lst): Reference times for the observations. 
    """
    
    # List of observationCollection parsers.
    # Add other parsers in here if needed.
    rangeParser = estimation.observations.observations_processing.observation_parser(
        estimation.observable_models_setup.model_settings.one_way_range_type
    )

    observationValues, observationTimes = observationCollection.get_concatenated_observations_and_times(
        rangeParser
    )

    return observationValues, observationTimes








