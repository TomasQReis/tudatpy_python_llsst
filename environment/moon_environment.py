### Functions relating to environments with the Moon as a central body. ###

### Tudat imports.
from tudatpy.dynamics import propagation_setup
from tudatpy.astro import time_representation

### External imports.
import numpy as np

### Self-made imports.
from bodies.bodies import spacecraft, groundStation
from environment.environment import environmentClass

class moonEnvironment ( environmentClass ):

    # Sets frame origin body as moon.
    frameOriginBody = "Moon"

    def select_propagation_level( self ):
        # NOTE: This defines the cartesian state with default Moon mu if default
        # harmonics are used. 
        self.make_environment_bodies( bodies = ["Moon", "Earth"] )
        self.make_spacecraft_initial_states( )
    
        match self.level:
            case 1: 
                self.make_environment_bodies( bodies = ["Moon", "Earth", "Sun"] )
                self.make_level_01_acceleration_settings( )
            case 2: 
                self.make_environment_bodies( bodies = ["Moon", "Earth", "Sun", 
                                                        "Jupiter"] )
                self.make_level_02_acceleration_settings()
            case 3:
                self.make_environment_bodies(
                    bodies= ["Moon", "Earth", "Sun", "Jupiter"]
                )
                self.make_level_03_acceleration_settings( 
                    harmonicsDegree= self.harmonicsMaxDegree
                )

    def make_level_01_acceleration_settings ( self ):
        # Acceleration settings dict. 
        self.accelerationSettings = dict(
            Moon    = [propagation_setup.acceleration.spherical_harmonic_gravity(10,10)],
            Earth   = [propagation_setup.acceleration.point_mass_gravity()],
            Sun     = [propagation_setup.acceleration.point_mass_gravity()]
        )

    def make_level_02_acceleration_settings ( self ):
        # Acceleration settings dict. 
        self.accelerationSettings = dict(
            Moon    = [propagation_setup.acceleration.spherical_harmonic_gravity(10,10)],
            Earth   = [propagation_setup.acceleration.point_mass_gravity()],
            Sun     = [propagation_setup.acceleration.point_mass_gravity()],
            Jupiter = [propagation_setup.acceleration.point_mass_gravity()]
        )

    def make_level_03_acceleration_settings ( self, harmonicsDegree: int= 10 ):
        # Acceleration settings dict. 
            self.accelerationSettings = dict(
                Moon    = [propagation_setup.acceleration.spherical_harmonic_gravity(
                    harmonicsDegree, harmonicsDegree)],
                Earth   = [propagation_setup.acceleration.point_mass_gravity()],
                Sun     = [propagation_setup.acceleration.point_mass_gravity()],
                Jupiter = [propagation_setup.acceleration.point_mass_gravity()]
            )



    