
# Tudat imports. 
from tudatpy.estimation.observable_models_setup.model_settings import one_way_range_type

# Local imports
from observations.observation_class import observationsClass

class oneWayObservationsClass ( observationsClass ):

    # Sets observation type as one-way range. 
    observationType = one_way_range_type


