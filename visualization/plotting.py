### External library imports.
from matplotlib import pyplot as plt
from numpy.typing import NDArray

### Internal library imports. 
from bodies.common import spacecraft

### Tudat imports
from tudatpy.util import result2array

lineStyles = ["-", "--", "-.", ":"]
lineColors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']

def trajectory_plot_3d( 
        spacecrafts: list[spacecraft],
        stateHistoryArray: NDArray,
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

    # Define a 3D figure using pyplot
    fig = plt.figure(figsize=(6,6), dpi=125)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title(title)

    for index, spacecraft in enumerate(spacecrafts):

        # Plot the positional state history
        ax.plot(stateHistoryArray[:, index*6+1], 
                stateHistoryArray[:, index*6+2], 
                stateHistoryArray[:, index*6+3], 
                label=spacecraft.name, 
                linestyle=lineStyles[index % len(lineStyles)])
        ax.scatter(0, 0, 0, label="Moon", marker='o', color='blue')

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
        xAxisLabel: str,
        yAxisLabel: str,
        secondaryAxisKeys: list = None, # type: ignore
        secondaryAxisLabel: str = None, # type: ignore
):

    if secondaryAxisKeys is None:
        secondaryAxisKeys = []
    
    # Figure and axes initialization.
    fig = plt.figure(figsize=(6,6), dpi=125)
    ax = fig.add_subplot()
    ax.set_title(title)

    # Create secondary axis only if needed.
    ax2 = ax.twinx() if secondaryAxisKeys else None

    # Iterate through dictionary of data. 
    i = 0

    # Iterates through data dictionaries and plots.  
    for key, data in yVariables.items():
        targetAx = ax2 if key in secondaryAxisKeys else ax
        targetAx.plot(
            xVariables[key],
            data,
            label=key,
            linestyle=lineStyles[i % len(lineStyles)],
            color=lineColors[i % len(lineColors)]
        )
        i += 1

    # Add legend and axes. 
    ax.legend()
    ax.set_xlabel(xAxisLabel)
    ax.set_ylabel(yAxisLabel)
    if ax2 is not None:
        ax2.set_ylabel(secondaryAxisLabel)

    # Combine legends from both axes into one.
    lines, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines += lines2
        labels += labels2
    ax.legend(lines, labels)
    
    ax.grid()
    
    fig.tight_layout()

    plt.show()

    