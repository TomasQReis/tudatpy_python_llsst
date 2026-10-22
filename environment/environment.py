# Functions shared by all environment files. 

### Tudat imports.
from tudatpy.interface import spice
from tudatpy.astro.time_representation import DateTime
from tudatpy.dynamics import environment
from tudatpy.dynamics import environment_setup, propagation_setup, simulator
from tudatpy.astro import time_representation, element_conversion
from tudatpy.dynamics.environment import SystemOfBodies 

### External imports.
import numpy as np

### Self-made imports.
from bodies.bodies import spacecraft, groundStation

def convert_to_j2000(date: list):
    """
    Converts given date to seconds since J2000. 
    Args: 
        date (list): Formatted as [year, month, day] or [year, month, day, hour
        minute, seconds].
        longEpoch (bool): True if long date list. 
    Returns:
        dateJ2000 (Time): Seconds since J2000. 
    """

    if len(date) == 6:
        dateJ2000 = DateTime(
            date[0], date[1], date[2],
            date[3], date[4], date[5]
        ).to_epoch()
    elif len(date) == 3:
        dateJ2000 = DateTime(
            date[0], date[1], date[2]
        ).to_epoch()
    else: 
        raise ValueError(
            f"Date is given outside of required format."
        )

    return dateJ2000


def check_timespan_limit(simStartEpoch: float, simEndEpoch: float):
        """
        Checks whether timespan is within R3-1 limits (1 day to 5 years). 
        Returns True if timespan is within limits. 
        Args:
            simStartEpoch (float): seconds since J2000 for start of simulation timespan.
            simEndEpoch (float): seconds since J2000 for end of simulation timespan. 
        """
        # Uses seconds between 1st Jan 2000 and 1st Jan 2005 as approximation for 5 year limit.
        maxSpan = 157766400.0
        # 1/2 day as minimum timespan.
        # TODO: Correct back to 1 day. 
        minSpan = 12*60**2

        timeSpan = simEndEpoch - simStartEpoch
         
        if timeSpan > maxSpan:
            raise RuntimeError(
                f"Timespan larger than maximum:\n"
                f"User: {timeSpan} -- Max: {maxSpan}"
            )
        elif timeSpan < minSpan:
            raise RuntimeError(
                f"Timespan smaller than minimum:\n"
                f"User: {timeSpan} -- Min: {minSpan}"
            )
        else:
            return True

# Load spice kernels and convert time epochs to seconds since J2000. 
def load_spice(simStartDate: list, simEndDate: list):
    """
    Loads NAIF SPICE kernels with the given start and end epochs, returns 
    given epochs in seconds since J2000.
    Args:
        startEpoch (list): List of int. Represents a date written as [year, month, 
        day, hour, minute, seconds]. 
        endEpoch (list): list of int. Same representation as start epoch. 
    Returns:
        simStartEpoch (float): Time in seconds since J2000.
        simEndEpoch (float): Time in seconds since J2000.
    """
    # Load kernels
    spice.load_standard_kernels()

    # Convert given epochs to seconds since J2000.
    simStartEpoch = convert_to_j2000(
        date= simStartDate
    )
    simEndEpoch = convert_to_j2000(
        date= simEndDate
    )

    if check_timespan_limit(
            simStartEpoch= simStartEpoch,
            simEndEpoch= simEndEpoch
        ):  print("Timespan Within Limits")


    return simStartEpoch, simEndEpoch

# Extract spherical harmonic coefficients from a desired body. 
def return_sh_coefficients(
    bodyName: str,
    systemOfBodies: environment.SystemOfBodies,
    maxDegree: int,
    maxOrder: int,
):
    """
    Returns the spherical harmonics coefficients for a body. 
    Args:
        bodyName (str): Name of body.
        systemOfBodies (SystemOfBodies): System of bodies used. 
        maxDegree (int): maximum desired degree for returned coefficients. 
        maxOrder (int): maximum desired order for returned coefficients.
    Returns:
        cosineCoefficients (NDArray): Array of cosine coefficients following the (i,j)=(degree,order) indexing format.
        sineCoefficients (NDArray): Array of sine coefficients following the (i,j)=(degree,order) indexing format.
    """

    # Extract singular body from system of bodies.  
    body = systemOfBodies.get(
        body_name= bodyName
    )

    # Extract gravity field model. 
    gravityFieldModel =  body.gravity_field_model

    # Check whether extracted model is not a spherical harmonics model. 
    if type(gravityFieldModel) is not environment.SphericalHarmonicsGravityField:
        raise TypeError(
            f"ERROR: Body:{bodyName} does not have a spherical harmonics model associated with it."
        )
    
    # Extracts coefficients, keeping the (i,j) = (degree,order) entry order. 
    cosineCoefficients = gravityFieldModel.cosine_coefficients[:maxDegree+1, :maxOrder+1]
    sineCoefficients = gravityFieldModel.sine_coefficients[:maxDegree+1, :maxOrder+1]

    # Extract gravitational parameter.
    gravitationalParameter = body.gravitational_parameter 

    # Extract reference radius. 
    referenceRadius = gravityFieldModel.reference_radius
    
    return cosineCoefficients, sineCoefficients, referenceRadius, gravitationalParameter


class environmentClass ():
    def __init__(
        self, 
        simStartEpoch: time_representation.Time,
        simEndEpoch: time_representation.Time,
        timeStep: time_representation.Time,
        spacecrafts: list[spacecraft],
        level: int= 1,
        groundStations: list[groundStation]= [],
        customHarmonicsBool: bool= False,
        customHarmonicsFile: str= "",
        ):

        self.level = level
        self.spacecrafts = spacecrafts
        self.groundStations = groundStations
        self.customHarmonicsBool = customHarmonicsBool
        self.customHarmonicsFile = customHarmonicsFile
        self.simStartEpoch = simStartEpoch
        self.simEndEpoch = simEndEpoch
        self.timeStep = timeStep
        self.frameOriginBody = ""
        self.systemOfBodies: SystemOfBodies
        self.accelerationSettings: dict

    # SystemOfBodies creator. 
    def make_environment_bodies( self, bodies: list[str] ):
    
        # Global frame origin set to Moon. Orientation to J2000.
        frameOrigin       = self.frameOriginBody
        frameOrientation  = "J2000"

        # Body settings.
        bodySettings      = environment_setup.get_default_body_settings(
            bodies, frameOrigin, frameOrientation
        )
        # TODO: Custom spherical harmonics model. 
        if self.customHarmonicsBool:
            bodySettings.get( self.frameOriginBody ).gravity_field_settings = \
                environment_setup.gravity_field.spherical_harmonic(
                    gravitational_parameter= None, #FromFile
                    reference_radius= None, #From File
                    normalized_cosine_coefficients= None, #From File
                    normalized_sine_coefficients= None, #From File
                    associated_reference_frame= "IAU_" + self.frameOriginBody
                )

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

    # Spacecraft Initial states creator. 
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

    # Empty propagation level selector. 
    def select_propagation_level( self ): return None

    # Propagation settings creator. 
    def make_propagation_settings( self, dependentVariables: list= [] ):

        # Selects propagation level. 
        self.select_propagation_level( )
    
        # Bodies to propagate. 
        bodiesToPropagate = [spacecraft.name for spacecraft in self.spacecrafts]
    
        # Central bodies of propagation. 
        centralBodies = [self.frameOriginBody for _ in self.spacecrafts]

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

    # Dynamics propagator. 
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