import matplotlib.pyplot as plt
import numpy as np

from src.estimation.analysis import *

def plot_density_observation_verification():

    # File directory and name.
    fileDir = "src/tests/files/"
    fileNameTraj = "test_trajectory.png"
    fileNameDens = "test_density.png"

    # Verification Inputs
    lonSlice = 60
    latSlice = 30

    lats   = np.array( [ -75, -60, -52, -37, -27, -10,  0,  -9, -22, -30, -42, -50, -58, -56 ] )
    lons   = np.array( [  30,  32,  29,  28,  30,  47, 60,  72,  73,  68,  60,  36,  22,   0 ] )
    
    # Expected values. 
    #latIdx = np.array( [   5,   5,   4,   4,   3,   3,  3,   3,   3,   3,   4,   4,   4,   4 ] )
    #lonIdx = np.array( [   0,   0,   0,   0,   0,   0,  0,   1,   1,   1,   1,   0,   0,   0 ] )

    # Create plot showing trajectory.
    fig, ax = plt.subplots( figsize= ( 9, 4.5 ) )
    ax.plot( lons, lats, linestyle= "--", marker= "X", label= "Trajectory" )

    ax.set_ylim( bottom= -90, top= 90 )
    ax.set_yticks( np.arange( -90, 91, latSlice ) )
    ax.set_ylabel( "Latitude [deg]" )

    ax.set_xlim( left= 0, right= 360 )
    ax.set_xticks( np.arange( 0, 361, lonSlice ) )
    ax.set_xlabel( "Longitude [deg]" )

    ax.set_aspect( "equal" )
    ax.set_title( "Ground track" )

    ax.grid()

    fig.savefig( fname= fileDir + fileNameTraj )

    # Run observation density function.  
    testAnalysis = analysisLibrary( runDir="src/tests/files/", loadOnCreation= False )
    testAnalysis.lats = lats
    testAnalysis.lons = lons

    testAnalysis.plot_observation_density( 
        title= "Test Density", forceSlice= True, latSlice= latSlice, 
        lonSlice= lonSlice, show= False, save= True
        )
