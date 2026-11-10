# Tudat imports. 
from tudatpy.estimation.observable_models_setup.model_settings import \
    two_way_doppler_averaged, n_way_averaged_doppler_type,\
    one_way_doppler_averaged, one_way_averaged_doppler_type

# Local imports
from observations.observation_class import observationsClass

# One way doppler. 
class oneWayDopplerObservationsClass ( observationsClass ):

    # Sets type as one-way doppler. 
    observationType = [one_way_averaged_doppler_type]

    def make_model_settings(self) -> None:

        # Observation model settings for each link definition.
        self.observationModelSettings = [
            one_way_doppler_averaged( linkDefinition ) for linkDefinition in self.linkDefinitions
        ]

# Two-way doppler. 
class twoWayDopplerObservationsClass ( observationsClass ):

    # Sets type as n-way doppler.
    observationType = [n_way_averaged_doppler_type]

    def make_model_settings(self) -> None:

        # Observation model settings for each link definition.
        self.observationModelSettings = [
            two_way_doppler_averaged( linkDefinition ) for linkDefinition in self.linkDefinitions
        ]
