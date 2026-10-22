### Tudat imports.
from tudatpy.dynamics import propagation_setup
from tudatpy.astro import time_representation

### External imports.
import numpy as np

### Self-made imports.
from bodies.bodies import spacecraft, groundStation
from environment.environment import environmentClass

class marsEnvironment ( environmentClass ):
    def __init__ ( 
            self,
            simStartEpoch: time_representation.Time,
            simEndEpoch: time_representation.Time,
            timeStep: time_representation.Time,
            spacecrafts: list[spacecraft],
            level: int= 1,
            groundStations: list[groundStation]= [],
            customHarmonicsFile: str= "", ):
        
        # Calls inherited initalization. 
        environmentClass.__init__(
            self, 
            simStartEpoch= simStartEpoch, 
            simEndEpoch= simEndEpoch, 
            timeStep= timeStep,
            spacecrafts= spacecrafts,
            level= level,
            groundStations= groundStations,
            customHarmonicsFile= customHarmonicsFile
            )
        # Sets frame origin body as moon.
        self.frameOriginBody = "Mars"

    def make_level_01_acceleration_settings ( self ):
        # Acceleration settings dict. 
        self.accelerationSettings = dict(
            Mars    = [propagation_setup.acceleration.spherical_harmonic_gravity(10,10)],
            Sun     = [propagation_setup.acceleration.point_mass_gravity()]
        )

    def make_level_02_acceleration_settings ( self ):
        # Acceleration settings dict. 
        self.accelerationSettings = dict(
            Mars    = [propagation_setup.acceleration.spherical_harmonic_gravity(10,10)],
            Sun     = [propagation_setup.acceleration.point_mass_gravity()],
            Jupiter = [propagation_setup.acceleration.point_mass_gravity()],
            Phobos  = [propagation_setup.acceleration.point_mass_gravity()],
            Deimos  = [propagation_setup.acceleration.point_mass_gravity()]
        )

    def select_propagation_level( self ):
        # NOTE: This defines the cartesian state with default Moon mu if default
        # harmonics are used. 
        self.make_environment_bodies( bodies = ["Mars"] )
        self.make_spacecraft_initial_states( )
    
        match self.level:
            case 1: 
                self.make_environment_bodies( bodies = ["Mars", "Sun"] )
                self.make_level_01_acceleration_settings( )
            case 2: 
                self.make_environment_bodies( bodies = ["Mars", "Sun", "Jupiter",
                                                        "Phobos", "Deimos"] )
                self.make_level_02_acceleration_settings()

    