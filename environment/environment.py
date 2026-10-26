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

### Directories for models 
gravityModelsDir    = "data/models/gravity/"
atmoModelsDir       = "data/models/atmosphere/"

### Variables for models. 
# Gravity 
GGRX1200A           = gravityModelsDir + "gggrx_1200a_formatted.csv"
GGRX1200L           = gravityModelsDir + "gggrx_1200l_formatted.csv"
LP150Q              = gravityModelsDir + "lp150q_formatted.csv"

### Overall limits for arc and simulation timespans. 
# Uses seconds between 1st Jan 2000 and 1st Jan 2005 as approximation for 5 year limit.
MAXSPAN             = 157766400.0
# 1 day as minimum timespan.
MINSPAN             = 24*60**2      

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
        timeSpan = simEndEpoch - simStartEpoch
         
        if timeSpan > MAXSPAN:
            raise RuntimeError(
                f"Timespan larger than maximum:\n"
                f"User: {timeSpan} -- Max: {MAXSPAN}"
            )
        elif timeSpan < MINSPAN:
            raise RuntimeError(
                f"Timespan smaller than minimum:\n"
                f"User: {timeSpan} -- Min: {MINSPAN}"
            )
        else:
            return True


def check_arc_timespan_limit( arcLength: float, timeSpan: float ):
    """
    Checks whether arc length is within R3-1 limits (1 day to 5 years) and if 
    it is smaller than the entire simulation timespan. Returns true if so. 
    Args:
        arcLength (float): seconds since J2000 for arc length.
        timeSpan (float): seconds since J2000 for simulation timespan. 
    """

    if arcLength < MINSPAN or arcLength > MAXSPAN:
        raise RuntimeError(
            f"Arclength out of bounds:\n"
            f"Arc: {arcLength} -- Min/Max: {MINSPAN}/{MAXSPAN}"
        )
    elif arcLength > timeSpan:
        raise RuntimeError(
            f"Arc longer than simulation timespan:\n"
            f"Arc: {arcLength} -- Sim: {timeSpan}"
        )
    else:
        return True


# Load spice kernels and convert time epochs to seconds since J2000. 
def load_spice(simStartDate: list, 
               simEndDate: list, 
               skipTimespanCheck: bool= False):
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

    if skipTimespanCheck or check_timespan_limit(
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

        # Custom spherical harmonics model. 
        if self.customHarmonicsBool:
            bodySettings.get( self.frameOriginBody ).gravity_field_settings = \
                environment_setup.gravity_field.from_file_spherical_harmonic(
                    file= self.customHarmonicsFile,
                    maximum_degree  = 420,
                    maximum_order   = 420
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
    def select_propagation_level( self, harmonicsDegree: int= 10 ): return None

    # Propagation settings creator. 
    def make_propagation_settings( 
            self, 
            dependentVariables: list= [],
            harmonicsDegree: int= 10,
            arcTimeLength: float= 0.0,
            skipArcCheck: bool= False,
            keepEnvironment: bool= False 
        ):

        # Checks multi-arc propagation.
        if arcTimeLength != 0.0:
            if not skipArcCheck:
                # Checks arc length limits. 
                check_arc_timespan_limit(
                    arcLength= arcTimeLength,
                    timeSpan= float(self.simEndEpoch)
                )
            # Number of arcs.
            arcNumber = int( float(self.simEndEpoch - self.simStartEpoch) // arcTimeLength ) 
        else: 
            arcNumber = 1

        # Selects propagation level. 
        self.select_propagation_level( harmonicsDegree= harmonicsDegree )
    
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

        # Numerical integrator settings.
        integratorSettings = propagation_setup.integrator.runge_kutta_fixed_step(
            time_step= self.timeStep,
            coefficient_set= propagation_setup.integrator.CoefficientSets.rkf_78
        )

        # Empty list for individual arc settings. 
        self.propagatorSettings = [] 
        
        # Initial states. 
        
        self.make_spacecraft_initial_states( )

        ### NOTE: These all change per arc of integration. For loop. 
        for arc in range(arcNumber):
            # Arc termination time. 
            if arc < arcNumber-1: 
                arcFinalTime = self.simStartEpoch + arcTimeLength * (arc+1) 
            else: 
                # Avoids propagating beyond final epoch. 
                arcFinalTime = self.simEndEpoch

            # Create termination settings.
            terminationSettings = propagation_setup.propagator.time_termination(
                arcFinalTime  # sim end epoch or start epoch plus n * arclength. 
            )

            # Create propagation settings. 
            # NOTE: Multi-arc is set up to use integration results to find initial
            # State of each subsequent arc. TODO: Needs verification. 
            self.propagatorSettings.append( propagation_setup.propagator.translational(
                central_bodies= centralBodies,
                acceleration_models= acccelerationModels,
                bodies_to_integrate= bodiesToPropagate,
                initial_states= self.spacecraftInitialStates,
                initial_time= self.simStartEpoch + arc * arcTimeLength,
                termination_settings= terminationSettings,
                integrator_settings= integratorSettings,
                output_variables= dependentVariables,
                ) 
            )

        self.arcSettings = propagation_setup.propagator.multi_arc(
            single_arc_settings= self.propagatorSettings,
            transfer_state_to_next_arc= True
        )

        if keepEnvironment: 
            self.arcSettings.processing_settings.set_integrated_result = True

    # Dynamics propagator. 
    def propagate( self ):
    
        # Create dynamics simulator.
        dynamicsSimulator = simulator.create_dynamics_simulator(
            bodies= self.systemOfBodies,
            propagator_settings= self.arcSettings
        )

        # Extract state history and dependent variables
        arcResults = dynamicsSimulator.propagation_results.single_arc_results # type: ignore

        return arcResults