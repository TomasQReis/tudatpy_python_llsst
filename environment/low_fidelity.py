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
from tudatpy.interface import spice
from tudatpy import dynamics
from tudatpy.dynamics import environment_setup, propagation_setup, simulator
from tudatpy.dynamics.environment import SystemOfBodies
from tudatpy.astro import element_conversion
from tudatpy import constants
from tudatpy.util import result2array
from tudatpy.astro.time_representation import DateTime

# TODO: Put this in a common functions file. 
def load_spice(startEpoch: list, endEpoch: list, longEpoch: bool= False):
    """
    Loads NAIF SPICE kernels with the given start and end epochs, returns 
    given epochs in seconds since J2000.
    Args:
        startEpoch (list): List of int. Represents a date written as [year, month, 
        day, hour, minute, seconds]. 
        endEpoch (list): list of int. Same representation as start epoch. 
        longEpoch (bool): 
    Returns:
        simStartEpoch (float): Time in seconds since J2000.
        simEndEpoch (float): Time in seconds since J2000.
    """
    # Load kernels
    spice.load_standard_kernels()

    # Convert given epochs to seconds since J2000.
    if longEpoch:
        simStartEpoch = DateTime(
            startEpoch[0], startEpoch[1], startEpoch[2],
            startEpoch[3], startEpoch[4], startEpoch[5]
        ).to_epoch()
        simEndEpoch = DateTime(
            endEpoch[0], endEpoch[1], endEpoch[2],
            endEpoch[3], endEpoch[4], endEpoch[5]
        ).to_epoch()
    else:
        simStartEpoch = DateTime(
            startEpoch[0], startEpoch[1], startEpoch[2]
        ).to_epoch()
        simEndEpoch = DateTime(
            endEpoch[0], endEpoch[1], endEpoch[2],
        ).to_epoch()

    return simStartEpoch, simEndEpoch

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
        timeStep: float= 10.0
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

        Moon    = [propagation_setup.acceleration.point_mass_gravity()]
        # TODO: Uncomment when point_mass simulation works. 
        #Moon    = [propagation_setup.acceleration.spherical_harmonic_gravity(10,10)]
    )

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
    
    # Define initial cartesian states.
    initialCartesianStatesList = []
    for spacecraft in spacecrafts:
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
        integrator_settings= integratorSettings
    )

    return propagatorSettings
    


