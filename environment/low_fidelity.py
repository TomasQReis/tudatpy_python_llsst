###
# This file contains all code pertaining to defining the low fidelity 
# bodies and dynamics used for simulated observations and parameter estimation. 
# This environment consists of an Sun-Earth-Moon system with low-degree (10)
# spherical harmonic gravity field for the Moon and point mass for the Earth.
# Basically just for me to get to know the program bit by bit and play around.
### 

### External library imports.
import numpy as np

### Tudat imports.
from tudatpy.dynamics import environment_setup, propagation_setup, simulator
from tudatpy.dynamics.environment import SystemOfBodies
from tudatpy.dynamics.propagation_setup.propagator import TranslationalStatePropagatorSettings
from tudatpy.astro import element_conversion


def environment_bodies_low_fidelity( spacecrafts: list ):
    """
    Sets up low-fidelity simulation environment bodies.

    Args:
        spacecraft (list): List of strings of spacecraft included in simulation.

    Returns:
        bodies ( SystemOfBodies ): Object containing the objects for bodies and environment models constituting the physical environment.   
    """
    # Default body settings for Sun, Earth and Moon.
    bodiesToCreate              = ["Earth", "Moon", "Sun"]

    # Global frame origin set to Moon. Orientation to J2000.
    globalFrameOrigin           = "Moon"
    globalFrameOrientation      = "J2000"

    # Body settings.
    bodySettings              = environment_setup.get_default_body_settings(
        bodiesToCreate, globalFrameOrigin, globalFrameOrientation
    )

    # Add spacecraft to body settings. 
    for spacecraft in spacecrafts:
        bodySettings.add_empty_settings( spacecraft["name"] )

    # Create system of bodies. 
    bodies = environment_setup.create_system_of_bodies( bodySettings )

    return bodies

def environment_prop_settings_low_fidelity( 
        spacecrafts: list, 
        bodies: SystemOfBodies,
        simStartEpoch: float,
        simEndEpoch: float,
        timeStep: float= 10.0,
        sHMoon: bool= False,
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
        sHMoon (bool): True when choosing to include a Spherical Harmonics degree/order 10 acceleration. 
    Returns:
        propagatorSettings (TranslationalStatePropagatorSettings): Translational state propagator settings object.
    """

    # Bodies to propagate. 
    bodiesToPropagate = [spacecraft["name"] for spacecraft in spacecrafts]

    # Central bodies of propagation. 
    centralBodies = ["Moon" for _ in spacecrafts]

    # Environment acceleration settings. 
    environmentAccelerationSettings = dict(
        Sun     = [propagation_setup.acceleration.point_mass_gravity()],

        Earth   = [propagation_setup.acceleration.point_mass_gravity()],

    )
    if sHMoon:
        environmentAccelerationSettings["Moon"] = [propagation_setup.acceleration.spherical_harmonic_gravity(10,10)]
    else:
        environmentAccelerationSettings["Moon"] = [propagation_setup.acceleration.point_mass_gravity()]
    
    # Spacecraft acceleration settings. 
    spacecraftAccelerationSettings = {
        spacecraft["name"] : environmentAccelerationSettings for spacecraft in spacecrafts}

    # Create acceleration models. 
    acccelerationModels = propagation_setup.create_acceleration_models(
        body_system=                    bodies,
        selected_acceleration_per_body= spacecraftAccelerationSettings,
        bodies_to_propagate=            bodiesToPropagate,
        central_bodies=                 centralBodies
    )
    
    # Empty initial cartesian state and dependent variables list. 
    initialCartesianStatesList = []
    for spacecraft in spacecrafts:
        # Define initial cartesian states.
        # Convert from keplerian initial state to cartesian coords. 
        cartesianState = element_conversion.keplerian_to_cartesian_elementwise(
            gravitational_parameter= bodies.get("Moon").gravitational_parameter,
            semi_major_axis= spacecraft["keplerianElems"][0],
            eccentricity= spacecraft["keplerianElems"][1],
            inclination= spacecraft["keplerianElems"][2],
            argument_of_periapsis= spacecraft["keplerianElems"][3],
            longitude_of_ascending_node= spacecraft["keplerianElems"][4],
            true_anomaly= spacecraft["keplerianElems"][5],
        )
        # Save initial state to spacecraft.
        spacecraft["cartesianInitial"] = cartesianState
        # Append to initial states. 
        initialCartesianStatesList.append( cartesianState )

    # TODO: Implement a method for ensuring correct relative distance measure
    # for more than two satellites in constellation. 
    # Something with an array with the pairs we want to have as links?
    # NOTE: TEMPORARY!
    dependentVariablesList = [
        propagation_setup.dependent_variable.relative_distance(
            body= spacecrafts[0]["name"],
            relative_body= spacecrafts[1]["name"]
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
        output_variables= dependentVariablesList
    )

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
    
