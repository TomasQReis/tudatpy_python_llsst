###
# This file contains all code pertaining to defining the low fidelity 
# bodies and dynamics used for simulated observations and parameter estimation. 
# This environment consists of an Sun-Earth-Moon system with low-degree (10)
# spherical harmonic gravity field for the Moon and point mass for the Earth.
# Basically just for me to get to know the program bit by bit and play around.
### 

### Self-made imports.
from vehicles.vehicles_common import spacecraft

### External library imports.
import numpy as np

### Tudat imports.
from tudatpy.dynamics import environment_setup, propagation_setup, simulator
from tudatpy.dynamics.environment import SystemOfBodies
from tudatpy.dynamics.propagation_setup.propagator import TranslationalStatePropagatorSettings
from tudatpy.astro import element_conversion
from tudatpy.astro import gravitation

# Low fidelity truth model. 
def environment_bodies_low_fidelity_true_model( spacecrafts: list[spacecraft] ):
    """
    Sets up low-fidelity "true" environment bodies. These are used in the low fidelity simulated observations. 

    Args:
        spacecraft (list): List of strings of spacecraft included in simulation.

    Returns:
        bodies ( SystemOfBodies ): Object containing the objects for bodies and environment models constituting the physical environment.   
    """
    # Default body settings for Sun, Earth and Moon.
    bodiesToCreate              = ["Earth", "Moon", "Sun", "Jupiter", "Saturn", "Mars", "Venus"]

    # Global frame origin set to SSB. Orientation to J2000.
    globalFrameOrigin           = "Moon"
    globalFrameOrientation      = "J2000"

    # Body settings.
    bodySettings              = environment_setup.get_default_body_settings(
        bodiesToCreate, globalFrameOrigin, globalFrameOrientation
    )

    # Add spacecraft to body settings. 
    for spacecraft in spacecrafts:
        bodySettings.add_empty_settings( spacecraft.name )
        bodySettings.get( spacecraft.name ).constant_mass = spacecraft.mass

    ### NOTE: Temporary
    # Adds example graz station. 
    grazPosition = [ 4194426.1, 1162694.5, 4647246.9 ]
    grazStationSettings = environment_setup.ground_station.basic_station( "Graz", grazPosition )

    earthStationsSettingsList = list()
    earthStationsSettingsList.append( grazStationSettings )

    bodySettings.get("Earth").ground_station_settings = earthStationsSettingsList

    # Create system of bodies. 
    bodies = environment_setup.create_system_of_bodies( bodySettings )

    return bodies

# TODO: Refactor using spacecraft class. 
# Low fidelity estimation model. 
def environment_bodies_low_fidelity_estimation_model( 
        spacecrafts: list[spacecraft],
        harmonicCoeffOrder: int= 0 ):
    """
    Sets up low-fidelity estimation model environment bodies. These are used in the low fidelity estimation. 

    Args:
        spacecraft (list): List of strings of spacecraft included in simulation.
        harmonicCoeffOrder (int): Maximum order/degree of SH created for target body. 

    Returns:
        bodies ( SystemOfBodies ): Object containing the objects for bodies and environment models constituting the physical environment.   
    """
    # Default body settings for Sun, Earth.
    bodiesToCreate              = ["Earth", "Sun"]

    # Global frame origin set to Moon. Orientation to J2000.
    globalFrameOrigin           = "SSB"
    globalFrameOrientation      = "J2000"

    # Body settings.
    bodySettings              = environment_setup.get_default_body_settings(
        bodiesToCreate, globalFrameOrigin, globalFrameOrientation
    )

    # Add specific settings for the Moon.
    bodySettings.add_empty_settings( "Moon" )
    # Add default spice ephemeris. 
    bodySettings.get( "Moon" ).ephemeris_settings = environment_setup.ephemeris.direct_spice(
        frame_origin= "SSB",
        frame_orientation= "J2000"
    )
    # Add default rotation model.
    bodySettings.get( "Moon" ).rotation_model_settings = environment_setup.rotation_model.spice(
        base_frame= "J2000",
        target_frame= "IAU_Moon"
    )

    # Create empty sets of un-normalized cosine coefficients. 
    unnormalizedCosineCoeffs = np.zeros( [harmonicCoeffOrder +1, harmonicCoeffOrder +1] ) 
    unnormalizedSineCoeffs = np.zeros( [harmonicCoeffOrder +1, harmonicCoeffOrder +1] ) 
    

    # Normalize initialized guesses. 
    normalizedCosineCoeffs, normalizedSineCoeffs = gravitation.normalize_spherical_harmonic_coefficients(
        unnormalized_cosine_coefficients= unnormalizedCosineCoeffs,
        unnormalized_sine_coefficients= unnormalizedSineCoeffs
    )

    # Set initial guess for SH gravity field. 
    bodySettings.get( "Moon" ).gravity_field_settings = environment_setup.gravity_field.spherical_harmonic(
        gravitational_parameter= 4.9028001224453001E+12,    # Value for gggrx1200 [m^3/s^2]
        reference_radius= 1738000.0,                        # Value for gggrx1200 [m]
        normalized_cosine_coefficients= normalizedCosineCoeffs,
        normalized_sine_coefficients=   normalizedSineCoeffs,
        associated_reference_frame= "IAU_Moon"
    )
    

    # Add spacecraft to body settings. 
    for spacecraft in spacecrafts:
        bodySettings.add_empty_settings( spacecraft["name"] )
        bodySettings.get( spacecraft["name"] ).constant_mass = spacecraft["mass"]

    # Create system of bodies. 
    bodies = environment_setup.create_system_of_bodies( bodySettings )

    return bodies


def environment_prop_settings_low_fidelity( 
        spacecrafts: list[spacecraft], 
        bodies: SystemOfBodies,
        simStartEpoch: float,
        simEndEpoch: float,
        timeStep: float= 10.0,
        harmonicCoeffOrder: int= 0,
        trueModel: bool= False,
        keepEnvironment: bool= False,
        stateOffset= np.zeros(6),
    ):
    """
    Creates the propagator settings for the low fidelity Sun-Earth-Moon 
    environment.
    
    Args:
        spacecrafts (list): List of spacecraft dictionaries involved in the propagation. 
        bodies (SystemOfBodies): Object containing the objects for bodies and environment models constituting the physical environment.
        simStartEpoch (float): Time since J2000 in seconds for the start of the propagation.
        simEndEpoch (float): Time since J2000 in seconds for the end of the propagation.
        timeStep (float): Fixed time-step for the rk4 integration. Defaults to 10.0s. 
        harmonicCoeffOrder (int): Defines SH coefficient maximum order/degree to use in propagation.
        trueModel (bool): True when propagator settings are intended for use in "real" propagation (simulated observations). 
    Returns:
        propagatorSettings (TranslationalStatePropagatorSettings): Translational state propagator settings object.
    """

    # Bodies to propagate. 
    bodiesToPropagate = [spacecraft.name for spacecraft in spacecrafts]

    # Central bodies of propagation. 
    centralBodies = ["Moon" for _ in spacecrafts]

    # Environment acceleration settings. 
    environmentAccelerationSettings = dict(
        Sun     = [propagation_setup.acceleration.point_mass_gravity()],

        Earth   = [propagation_setup.acceleration.point_mass_gravity()],

    )
    # Check whether these are the propagation settings for "reality".
    """ if trueModel:
        environmentAccelerationSettings["Jupiter"] = [propagation_setup.acceleration.point_mass_gravity()]
        environmentAccelerationSettings["Saturn"] = [propagation_setup.acceleration.point_mass_gravity()]
        environmentAccelerationSettings["Mars"] = [propagation_setup.acceleration.point_mass_gravity()]
        environmentAccelerationSettings["Venus"] = [propagation_setup.acceleration.point_mass_gravity()] """

    # Check if spherical harmonics should be included for the moon. 
    if harmonicCoeffOrder != 0:
        environmentAccelerationSettings["Moon"] = [propagation_setup.acceleration.spherical_harmonic_gravity(
            harmonicCoeffOrder,harmonicCoeffOrder)]
    else:
        environmentAccelerationSettings["Moon"] = [propagation_setup.acceleration.point_mass_gravity()]


    
    # Spacecraft acceleration settings. 
    spacecraftAccelerationSettings = {
        spacecraft.name : environmentAccelerationSettings for spacecraft in spacecrafts}

    # Create acceleration models. 
    acccelerationModels = propagation_setup.create_acceleration_models(
        body_system=                    bodies,
        selected_acceleration_per_body= spacecraftAccelerationSettings,
        bodies_to_propagate=            bodiesToPropagate,
        central_bodies=                 centralBodies
    )
    
    # Empty initial cartesian state list. 
    initialCartesianStatesList = []

    #print(f"Top of for loop:{simStartEpoch}")

    for spacecraft in spacecrafts:
        # Define initial cartesian states.
        # When true assumes taking initial state from stored keplerian elements. 
        if trueModel:
            # Convert from keplerian initial state to cartesian coords. 
            cartesianState = element_conversion.keplerian_to_cartesian_elementwise(
                gravitational_parameter= bodies.get("Moon").gravitational_parameter,
                semi_major_axis= spacecraft.keplerianElems[0],
                eccentricity= spacecraft.keplerianElems[1],
                inclination= spacecraft.keplerianElems[2],
                argument_of_periapsis= spacecraft.keplerianElems[3],
                longitude_of_ascending_node= spacecraft.keplerianElems[4],
                true_anomaly= spacecraft.keplerianElems[5],
            ) 

        else: 
            # If not the truth simulation, uses offset true state at given sim
            # start epoch as the initial state. 
            cartesianState = spacecraft.find_cartesian_state( 
                stateEpoch= simStartEpoch
            ) + stateOffset

        # Append to initial states. 
        initialCartesianStatesList.append( cartesianState )

    # TODO: Implement a method for ensuring correct relative distance measure
    # for more than two satellites in constellation. 
    # Something with an array with the pairs we want to have as links?
    # NOTE: TEMPORARY!
    dependentVariablesList = [
        propagation_setup.dependent_variable.relative_distance(
            body= spacecrafts[0].name,
            relative_body= spacecrafts[1].name
        )
    ]


    # Flatten out state vector.
    initialCartesianStates = np.concatenate( initialCartesianStatesList )

    # Create termination settings.
    terminationSettings = propagation_setup.propagator.time_termination(
        simEndEpoch
    )

    # Numerical integrator settings.
    integratorSettings = propagation_setup.integrator.runge_kutta_fixed_step(
        time_step= timeStep,
        coefficient_set= propagation_setup.integrator.CoefficientSets.rk_4
    )

    # Create propagation settings. 
    propagatorSettings = propagation_setup.propagator.translational(
        central_bodies= centralBodies,
        acceleration_models= acccelerationModels,
        bodies_to_integrate= bodiesToPropagate,
        initial_states= initialCartesianStates,
        initial_time= simStartEpoch,
        termination_settings= terminationSettings,
        integrator_settings= integratorSettings,
        output_variables= dependentVariablesList,
    )

    # Keep propagation results as ehemeris at the end of propagation. 
    if keepEnvironment:
        propagatorSettings.processing_settings.set_integrated_result = True

    return propagatorSettings

    
def environment_propagate_low_fidelity(
        bodies: SystemOfBodies,
        propagationSettings: TranslationalStatePropagatorSettings,
):
    """
    Propagates the provided bodies with the given propagation settings.
    Args:
        bodies (SystemOfBodies): Object containing the objects for bodies and environment models constituting the physical environment.   
        propagationSettings (TranslationalStatePropagatorSettings) : SingleArcPropagatorSettings-derived class to define settings for single-arc translational dynamics. 
    Returns:
        stateHistory (dict): Dictionary whose keys are the timestamps of the propagation. Each key contains a flattenned numpy array of the states of each spacecraft at the given epoch, organized such that each set of 6 values corresponds to one spacecraft.
    """
    
    # Create dynamics simulator.
    dynamicsSimulator = simulator.create_dynamics_simulator(
        bodies= bodies,
        propagator_settings= propagationSettings
    )

    # Extract state history. 
    stateHistory = dynamicsSimulator.propagation_results.state_history
    # Extract dependent variables history. 
    dependentVarsHistory = dynamicsSimulator.propagation_results.dependent_variable_history

    return stateHistory, dependentVarsHistory
    
