### External library imports.
from matplotlib import pyplot as plt
from numpy import ndarray

### Tudat imports
from tudatpy.util import result2array

lineStyles = ["-", "--", "-.", ":"]

def trajectory_plot_3d( 
        spacecrafts: list,
        stateHistory: dict,
        title: str
 ):
    """
    Plots a set of positions for the given spacecraft dictionary list. Assumes
    that propagation has been performed and stateHistory is formatted correctly
    along with the spacecraft list. 
    Args:
        spacecrafts (list): list of spacecraft dictionaries. 
        stateHistory (dict): Dictionary whose keys are the timestamps of the propagation. Each key contains a flattenned numpy array of the states of each spacecraft at the given epoch, organized such that each set of 6 values corresponds to one spacecraft.
        title (str): Title of plot. 
    """
    # Convert state history into a numpy array. 
    stateHistoryArray = result2array(stateHistory)

    # Define a 3D figure using pyplot
    fig = plt.figure(figsize=(6,6), dpi=125)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title(title)

    for index, spacecraft in enumerate(spacecrafts):

        # Plot the positional state history
        ax.plot(stateHistoryArray[:, index*6+1], 
                stateHistoryArray[:, index*6+2], 
                stateHistoryArray[:, index*6+3], 
                label=spacecraft["name"], 
                linestyle=lineStyles[index % len(lineStyles)])
        ax.scatter(0.0, 0.0, 0.0, label="Moon", marker='o', color='blue')

    # Add the legend and labels, then show the plot
    ax.legend()
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.set_zlabel('z [m]')
    ax.set_aspect('equal')
    plt.show()

def generalized_plot_2d(
        yVariables: dict,
        xVariables: dict,
        title: str,
        # TODO: Add a better method for generalized x-y axes. 
        xAxisLabel: str,
        yAxisLabel: str
):
    
    # Figure and axes initialization.
    # TODO: Implement different y-axes for same x-axis. 
    fig = plt.figure(figsize=(6,6), dpi=125)
    ax = fig.add_subplot()
    ax.set_title(title)

    # Iterate through dictionary of data. 
    i = 0
    for key, data in yVariables.items():
        ax.plot(
            xVariables[key],
            data,
            label= key,
            linestyle=lineStyles[i % len(lineStyles)]
        )
        i += 1

    # Add legend and axes. 
    ax.legend()
    ax.set_xlabel(xAxisLabel)
    ax.set_ylabel(yAxisLabel)
    
    ax.grid()
    
    fig.tight_layout()

    plt.show()

    