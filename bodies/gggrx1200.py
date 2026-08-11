import numpy as np


modelsDir = "data/models/"


def gggrx_coefficients(
        maxDegree: int,
):
    """
    Reads a GRAIL-style spherical harmonics .tab file and returns
    zero-padded cosine and sine coefficient arrays indexed by [degree, order].

    Args:
        maxDegree (int): if provided, arrays are sized to this degree. If None, sized to the maximum degree found in the file.

    Returns:
        cosineCoefficients (NDArray): shape (maxDegree+1, maxDegree+1)
        sineCoefficients (NDArray): shape (maxDegree+1, maxDegree+1)
    """
    # Load first 4 columns, skipping the header row.
    data = np.loadtxt(modelsDir + "gggrx_1200a_sha.tab", 
                      skiprows=1, usecols=(0, 1, 2, 3),
                      delimiter=",")

    degrees = data[:, 0].astype(int)
    orders = data[:, 1].astype(int)
    cosineVals = data[:, 2]
    sineVals = data[:, 3]

    if maxDegree is None:
        maxDegree = degrees.max()

    # Filter to only rows within the requested maxDegree (and valid order <= degree).
    mask = (degrees <= maxDegree) & (orders <= maxDegree)
    degrees = degrees[mask]
    orders = orders[mask]
    cosineVals = cosineVals[mask]
    sineVals = sineVals[mask]

    # Initialize zero-filled square arrays.
    cosineCoefficients = np.zeros((maxDegree + 1, maxDegree + 1))
    sineCoefficients = np.zeros((maxDegree + 1, maxDegree + 1))


    # Populate using (degree, order) as index pairs.
    cosineCoefficients[degrees, orders] = cosineVals
    sineCoefficients[degrees, orders] = sineVals

    return cosineCoefficients, sineCoefficients


