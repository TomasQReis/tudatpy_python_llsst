import unittest

import numpy as np

### Tudat Imports 
from tudatpy.interface import spice
from tudatpy.util import result2array

### Custom Imports
from bodies.roci_ab import rociA, rociB
from bodies.ground_stations import grazStation

from environment.environment import GGRX1200L, MAXSPAN, MINSPAN, LP150Q, GGRX1200A\
    ,convert_to_j2000, check_timespan_limit, check_arc_timespan_limit, load_spice
from environment.moon_environment import moonEnvironment

from estimation.estimation import estimator

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
            customHarmonicsFile= GGRX1200L,
            harmonicsMaxDegree= 40
        )
    
        environmentDefaultHarmonics = moonEnvironment(
            level= 3,
            simStartEpoch= simStartEpoch,   # type: ignore
            simEndEpoch= simEndEpoch,       # type: ignore
            timeStep= 10.0,                 # type: ignore
            spacecrafts= spacecrafts,
            customHarmonicsBool= False,
            harmonicsMaxDegree= 40
        )

        environmentLoadedHarmonics.make_propagation_settings( )
        environmentDefaultHarmonics.make_propagation_settings( )

        stateHistoryLoaded = environmentLoadedHarmonics.propagate()
        stateHistoryDefault = environmentDefaultHarmonics.propagate()
    
        stateArrayLoaded = result2array(stateHistoryLoaded.state_history)
        stateArrayDefault = result2array(stateHistoryDefault.state_history)
    
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


class propagationTests ( unittest.TestCase ):
    # Load kernels
    spice.load_standard_kernels()

    def test_multi_vs_single_arc_propagation ( self ):
        # Given as [Year, Month, Day]
        simStartDate    = [2001, 1, 1, 0, 0, 0]
        simEndDate      = [2001, 1, 3, 0, 0, 0]
    
        # Propagation time step size. 
        propTimeStep = 120.0     # [s]
    
        # Arc Length. 
        arcLength = 12 * 60**2 # 24hrs
        # Single Arc. 
        arcLength0 = 0.0
    
        # Load SPICE kernels and return J2000 formatted epochs. 
        simStartEpoch, simEndEpoch = load_spice( 
            simStartDate= simStartDate, simEndDate= simEndDate,
            skipTimespanCheck= True
            )
    
        # Choose list of spacecraft for simulation. 
        spacecrafts = [ rociA, rociB ]
    
        # Choose list of ground stations for simulation.
        groundStations = [ grazStation ]
    
    
        # Reference degree. 
        referenceDegree = 5
    
        environmentSingleArc = moonEnvironment(
            level= 3,
            simStartEpoch= simStartEpoch,   # type: ignore
            simEndEpoch= simEndEpoch,       # type: ignore
            timeStep= propTimeStep,         # type: ignore
            spacecrafts= spacecrafts,
            groundStations= groundStations,
            customHarmonicsBool= False,
            harmonicsMaxDegree= referenceDegree,
        )
        environmentMultiArc = moonEnvironment(
            level= 3,
            simStartEpoch= simStartEpoch,   # type: ignore
            simEndEpoch= simEndEpoch,       # type: ignore
            timeStep= propTimeStep,         # type: ignore
            spacecrafts= spacecrafts,
            groundStations= groundStations,
            customHarmonicsBool= False,
            customHarmonicsFile= LP150Q,
            harmonicsMaxDegree= referenceDegree
        )
    
        environmentSingleArc.make_propagation_settings()
        environmentMultiArc.make_propagation_settings()

    
        environmentSingleArc.make_propagation_settings( 
            arcTimeLength= arcLength0,
            skipArcCheck= True )
        environmentMultiArc.make_propagation_settings(
            arcTimeLength= arcLength,
            skipArcCheck= True
        )
        # Propagates single and multi-arc environments. 
        singleArcResults = environmentSingleArc.propagate()
        multiArcResults = environmentMultiArc.propagate()
    
        # Extracts reference propagation results. 
        multiArcResults = multiArcResults.single_arc_results

        multiArcXCoordinates = np.array( [] )

        lastArc = len(multiArcResults) - 1
        for i in range( len( multiArcResults ) ):
            arcStateArray = result2array( multiArcResults[i].state_history )
            # Extracts X-coordinates from single arc. 
            xCoordinates = arcStateArray[:,1]
            # Concatenates individual arc results.
            if i == lastArc:
                multiArcXCoordinates = np.concat( (multiArcXCoordinates, xCoordinates) )
            else: 
                multiArcXCoordinates = np.concat( (multiArcXCoordinates, xCoordinates[:-1]) )
    
        # Single arc results should match. 
        singleArcResultsArray = result2array( singleArcResults.state_history )
        # Extracts X-coordinates. 
        singleArcXCoordinates = singleArcResultsArray[:,1]

        # Should be equal. 
        self.assertEqual ( singleArcXCoordinates.all(), multiArcXCoordinates.all() )