### Functions relating to environments with the Moon as a central body. 

### Tudat imports.
from tudatpy.dynamics import environment_setup, propagation_setup, simulator
from tudatpy.dynamics.environment import SystemOfBodies 
from tudatpy.dynamics.propagation_setup.propagator import TranslationalStatePropagatorSettings
from tudatpy.astro import element_conversion, time_representation

### External imports.
import numpy as np

### Self-made imports.
from bodies.bodies import spacecraft, groundStation

class moonEnvironment ():
    def __init__(
            self, 
            simStartEpoch: time_representation.Time,
            simEndEpoch: time_representation.Time,
            timeStep: time_representation.Time,
            spacecrafts: list[spacecraft],
            level: int= 1,
            groundStations: list[groundStation]= [],
            customHarmonicsFile: str= "",
            ):

        self.level = level
        self.spacecrafts = spacecrafts
        self.groundStations = groundStations
        self.customHarmonicsFile = customHarmonicsFile
        self.simStartEpoch = simStartEpoch
        self.simEndEpoch = simEndEpoch
        self.timeStep = timeStep
        

    def make_environment_bodies( self, bodies: list[str] ):
        """
        Generates system of bodies for environment. 
        Args:
            bodies (list[str]): List of names of bodies for the environment.
        """

        # Global frame origin set to Moon. Orientation to J2000.
        frameOrigin       = "Moon"
        frameOrientation  = "J2000"

        # Body settings.
        bodySettings      = environment_setup.get_default_body_settings(
            bodies, frameOrigin, frameOrientation
        )
        # TODO: Custom spherical harmonics model. 
        if self.customHarmonicsFile:
            """bodySettings.get( "Moon" ).gravity_field_settings = \
                environment_setup.gravity_field.spherical_harmonic(
                    gravitational_parameter=
                )"""

        # Add spacecraft to body settings. 
        for spacecraft in self.spacecrafts:
            bodySettings.add_empty_settings( spacecraft.name )
            bodySettings.get( spacecraft.name ).constant_mass = spacecraft.mass
    
        # If ground stations list is not empty adds settings to environment. 
        if self.groundStations:
            # Empty stations settings list. 
            stationsSettingsList = []
            # Iterates throught ground stations. 
            for groundStation in self.groundStations:
                # Adds station settings to list. 
                stationsSettingsList.append(
                    groundStation.ground_station_settings()
                )
        
            # Adds ground station settings to respective body. 
            bodySettings.get( groundStation.parentBody ).ground_station_settings = \
                stationsSettingsList

        # Creates system of bodies. 
        self.systemOfBodies = environment_setup.create_system_of_bodies( bodySettings )

    def make_spacecraft_initial_states( self ):

        spacecraftInitialStates = []

        for spacecraft in self.spacecrafts:
            # Convert from keplerian initial state to cartesian coords. 
            spacecraftInitialStates.append ( element_conversion.keplerian_to_cartesian_elementwise(
                gravitational_parameter= self.systemOfBodies.get("Moon").gravitational_parameter,
                semi_major_axis= spacecraft.keplerianElems[0],
                eccentricity= spacecraft.keplerianElems[1],
                inclination= spacecraft.keplerianElems[2],
                argument_of_periapsis= spacecraft.keplerianElems[3],
                longitude_of_ascending_node= spacecraft.keplerianElems[4],
                true_anomaly= spacecraft.keplerianElems[5],
            ) )
        # Flatten out state vector.
        self.spacecraftInitialStates = np.concatenate( spacecraftInitialStates )

    def make_level_01_acceleration_settings ( self ):
        # Acceleration settings dict. 
        self.accelerationSettings = dict(
            Moon    = [propagation_setup.acceleration.spherical_harmonic_gravity(10,10)],
            Sun     = [propagation_setup.acceleration.point_mass_gravity()]
        )

    def make_level_02_acceleration_settings ( self ):
        # Acceleration settings dict. 
        self.accelerationSettings = dict(
            Moon    = [propagation_setup.acceleration.spherical_harmonic_gravity(10,10)],
            Sun     = [propagation_setup.acceleration.point_mass_gravity()],
            Jupiter = [propagation_setup.acceleration.point_mass_gravity()],
            Phobos  = [propagation_setup.acceleration.point_mass_gravity()],
            Deimos  = [propagation_setup.acceleration.point_mass_gravity()]
        )

    def make_propagation_settings( self, dependentVariables: list= [] ):
        # NOTE: This defines the cartesian state with default Moon mu if default
        # harmonics are used. 
        self.make_environment_bodies( bodies = ["Moon"] )
        self.make_spacecraft_initial_states( )
    
        match self.level:
            case 1: 
                self.make_environment_bodies( bodies = ["Moon", "Sun"] )
                self.make_level_01_acceleration_settings( )
            case 2: 
                self.make_environment_bodies( bodies = ["Moon", "Sun", "Jupiter",
                                                   "Phobos", "Deimos"] )
                self.make_level_02_acceleration_settings()

        # Bodies to propagate. 
        bodiesToPropagate = [spacecraft.name for spacecraft in self.spacecrafts]
    
        # Central bodies of propagation. 
        centralBodies = ["Moon" for _ in self.spacecrafts]

        # Spacecraft acceleration settings. 
        spacecraftAccelerationSettings = {
            spacecraft.name : self.accelerationSettings for spacecraft in self.spacecrafts }
    
        # Create acceleration models. 
        acccelerationModels = propagation_setup.create_acceleration_models(
            body_system=                    self.systemOfBodies,
            selected_acceleration_per_body= spacecraftAccelerationSettings,
            bodies_to_propagate=            bodiesToPropagate,
            central_bodies=                 centralBodies
        )

        # Create termination settings.
        terminationSettings = propagation_setup.propagator.time_termination(
            self.simEndEpoch
        )

        # Numerical integrator settings.
        integratorSettings = propagation_setup.integrator.runge_kutta_fixed_step(
            time_step= self.timeStep,
            coefficient_set= propagation_setup.integrator.CoefficientSets.rkf_78
        )

        # Create propagation settings. 
        self.propagatorSettings = propagation_setup.propagator.translational(
            central_bodies= centralBodies,
            acceleration_models= acccelerationModels,
            bodies_to_integrate= bodiesToPropagate,
            initial_states= self.spacecraftInitialStates,
            initial_time= self.simStartEpoch,
            termination_settings= terminationSettings,
            integrator_settings= integratorSettings,
            output_variables= dependentVariables,
        )

    def propagate( self ):

        # Create dynamics simulator.
        dynamicsSimulator = simulator.create_dynamics_simulator(
            bodies= self.systemOfBodies,
            propagator_settings= self.propagatorSettings
        )

        # Extract state history and dependent variables
        stateHistory = dynamicsSimulator.propagation_results.state_history
        dependentVarsHistory = dynamicsSimulator.propagation_results.dependent_variable_history

        return stateHistory, dependentVarsHistory