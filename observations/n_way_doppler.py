# Tudat imports. 
from typing import Sequence

from tudatpy.estimation.observable_models_setup.model_settings import \
    two_way_doppler_averaged, n_way_averaged_doppler_type,\
    one_way_doppler_averaged, one_way_averaged_doppler_type
from tudatpy.estimation.observations_setup.ancillary_settings import \
    n_way_doppler_ancillary_settings, doppler_ancillary_settings, FrequencyBands

# Local imports
from bodies.bodies import body
from environment.environment import environmentClass
from observations.observation_class import observationsClass

# One way doppler. 
class oneWayDopplerObservationsClass ( observationsClass ):

    # Sets type as one-way doppler. 
    observationType = [one_way_averaged_doppler_type]

    def __init__(
        self, 
        environmentReal: environmentClass, 
        linkGroups: Sequence[Sequence[body]], 

        epochMargin: float = 1 * 60 ** 2, 
        noiseSigma: float = 0, 
        uniqueObservationType: bool = True,
        
        countTime: float= 10,
        frequencyBand: FrequencyBands= FrequencyBands.s_band
        ) -> None:
        
        super().__init__(environmentReal, linkGroups, epochMargin,
                         noiseSigma, uniqueObservationType)

        # Attributes. 
        self.countTime = countTime
        self.frequencyBand = [frequencyBand]        # Saved as sequence-like

        # Make doppler-specific ancillary settings. 
        self.make_doppler_ancillary_settings()

    def make_model_settings(self) -> None:

        # Observation model settings for each link definition.
        self.observationModelSettings = [
            one_way_doppler_averaged( linkDefinition ) for linkDefinition in self.linkDefinitions
        ]

    def make_doppler_ancillary_settings(self) -> None:

        # Initializes count time and frequency bands. 
        self.make_simulator_settings_ancillary(
            ancillarySettings= n_way_doppler_ancillary_settings(
                integration_time= self.countTime,  
            )
        )
        self.make_simulator_settings_ancillary(
            ancillarySettings= n_way_doppler_ancillary_settings(
                frequency_bands= self.frequencyBand,  
            )
        )

    def set_count_time( self, countTime: float ): 
        # Sets new value.
        self.countTime = countTime

        # Re-sets simulation settings. 
        self.make_simulator_settings_ancillary(
            ancillarySettings= n_way_doppler_ancillary_settings(
                integration_time= self.countTime,  
            )
        )

    def set_frequency_band( self, frequencyBand ): 
        # Sets new value.
        self.frequencyBand = [frequencyBand]        # Saved as sequence-like

        # Re-sets simulation settings. 
        self.make_simulator_settings_ancillary(
            ancillarySettings= n_way_doppler_ancillary_settings(
                frequency_bands= self.frequencyBand,  
            )
        )

# Two-way doppler. 
class twoWayDopplerObservationsClass ( oneWayDopplerObservationsClass ):

    # Sets type as n-way doppler.
    observationType = [n_way_averaged_doppler_type]

    def __init__(
        self, 
        environmentReal: environmentClass, 
        epochMargin: float = 1 * 60 ** 2, 
        linkGroups: Sequence[Sequence[body]] = [[]], 
        noiseSigma: float = 0, 
        uniqueObservationType: bool = True,
        
        countTime: float= 10,
        frequencyBand: FrequencyBands= FrequencyBands.s_band
            ) -> None:
        
        super().__init__(environmentReal, linkGroups, epochMargin,
                         noiseSigma, uniqueObservationType)

        self.countTime = countTime
        self.frequencyBand = frequencyBand

    def make_model_settings(self) -> None:

        # Observation model settings for each link definition.
        self.observationModelSettings = [
            two_way_doppler_averaged( linkDefinition ) for linkDefinition in self.linkDefinitions
        ]
