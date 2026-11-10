
# Tudat imports. 
from tudatpy.estimation.observable_models_setup.model_settings import \
    one_way_range, one_way_range_type

# Local imports
from observations.observation_class import observationsClass

class oneWayRangeObservationsClass ( observationsClass ):

    # Sets observation type as one-way range. 
    observationType = [one_way_range_type]

    def make_model_settings(self) -> None:

        # Observation model settings for each link definition.
        self.observationModelSettings = [
            one_way_range( linkDefinition ) for linkDefinition in self.linkDefinitions
        ]
