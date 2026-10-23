import unittest

### Tudat Imports 
from tudatpy.interface import spice
from tudatpy.util import result2array

### Custom Imports
from bodies.roci_ab import rociA
from environment.environment import GGRX1200L, MAXSPAN, MINSPAN, convert_to_j2000, \
    check_timespan_limit, check_arc_timespan_limit
from environment.moon_environment import moonEnvironment

class environmentTests ( unittest.TestCase ):
    # Load kernels
    spice.load_standard_kernels()

    def test_spherical_harmonics_import( self ):
        
        simStartEpoch   = 0.0
        simEndEpoch     = 1000.0 

        # Choose list of spacecraft for simulation. 
        spacecrafts = [ rociA ]

        environmentLoadedHarmonics = moonEnvironment(
            level= 3,
            simStartEpoch= simStartEpoch,   # type: ignore
            simEndEpoch= simEndEpoch,       # type: ignore
            timeStep= 10.0,                 # type: ignore
            spacecrafts= spacecrafts,
            customHarmonicsBool= True,
            customHarmonicsFile= GGRX1200L
        )
    
        environmentDefaultHarmonics = moonEnvironment(
            level= 3,
            simStartEpoch= simStartEpoch,   # type: ignore
            simEndEpoch= simEndEpoch,       # type: ignore
            timeStep= 10.0,                 # type: ignore
            spacecrafts= spacecrafts,
            customHarmonicsBool= False
        )

        environmentLoadedHarmonics.make_propagation_settings( harmonicsDegree= 40 )
        environmentDefaultHarmonics.make_propagation_settings( harmonicsDegree= 40 )

        stateHistoryLoaded, _ = environmentLoadedHarmonics.propagate()
        stateHistoryDefault, _ = environmentDefaultHarmonics.propagate()
    
        stateArrayLoaded = result2array(stateHistoryLoaded)
        stateArrayDefault = result2array(stateHistoryDefault)
    
        self.assertEqual( stateArrayLoaded.all(), stateArrayDefault.all() )

    def test_timespan_check ( self ):
        # Given as [Year, Month, Day, Hour, Minutes, Seconds]
        startDate       = [2000, 1, 1, 0, 0, 0]
        # First date, below limit. 
        endDate1        = [2000, 1, 1, 12, 0, 0]
        # Second date, above limit. 
        endDate2        = [2006, 1, 1, 0, 0, 0]
        # Third date, within limts. 
        endDate3        = [2003, 1, 1, 0, 0, 0]

        # Convert to seconds since J2000.
        startEpoch      = convert_to_j2000( startDate )
        endEpoch1       = convert_to_j2000( endDate1 )
        endEpoch2       = convert_to_j2000( endDate2 )
        endEpoch3       = convert_to_j2000( endDate3 )

        # Checks for expected behaviors.
        with self.assertRaises( RuntimeError ):
            check_timespan_limit( startEpoch, endEpoch1 )
            check_timespan_limit( startEpoch, endEpoch2 )
        self.assertTrue( check_timespan_limit( startEpoch, endEpoch3 ) ) 

    def test_arc_length_check ( self ):
        with self.assertRaises( RuntimeError ):
            # Longer arc than simulation timespan.
            check_arc_timespan_limit( MINSPAN + 100.0 , MINSPAN + 10.0 )
            # Shorter arc than minimum and maximums. 
            check_arc_timespan_limit( MAXSPAN + 1.0, MAXSPAN + 100.0 )
            check_arc_timespan_limit( MINSPAN - 1.0, MAXSPAN )
        # Checks if acceptable condition passes. 
        self.assertTrue( check_arc_timespan_limit ( MINSPAN + 1.0, MAXSPAN ) )