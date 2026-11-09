
# Tudat imports. 
from tudatpy.estimation.observable_models_setup.model_settings import \
    one_way_range, one_way_range_type

# Local imports
from observations.observation_class import observationsClass

class oneWayObservationsClass ( observationsClass ):

    # Sets observation type as one-way range. 
    observationType = [one_way_range_type]

    def make_observation_model_settings(self) -> None:

        # Observation settings list. 
        observationModelSettings = []

        # Loops through exisitng
        for linkDefinition in self.linkDefinitions:
            observationModelSettings.append( one_way_range( linkDefinition ) )

        self.observationModelSettings = observationModelSettings