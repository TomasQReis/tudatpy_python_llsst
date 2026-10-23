import unittest

### Tudat Imports 
from tudatpy.interface import spice
from tudatpy.util import result2array

### Custom Imports
from bodies.roci_ab import rociA
from environment.environment import GGRX1200L
from environment.moon_environment import moonEnvironment




class stateDifferenceTestCase ( unittest.TestCase ):
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