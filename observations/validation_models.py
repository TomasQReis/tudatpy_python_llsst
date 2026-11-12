### Local imports.
from observations.n_way_doppler import \
    oneWayDopplerObservationsClass

from bodies.grail_spacecraft import \
    grailA, grailB
from bodies.ground_stations import \
    grazStation

from environment.moon_environment import \
    moonEnvironment

### Tudat imports.
from tudatpy.estimation.observations_setup.ancillary_settings import \
    FrequencyBands


### Constant values from validation case. (Park et al., 2012, p. 396)
# Range-rate standard deviations. 
DSNSIGMA = 5e-5             # m/s
KBRRSIGMA = 1e-6            # m/s

# Count times. 
DSNCOUNT = 10               # s
KBRRCOUNT = 5               # s

### Link Ends
## X-band DSN links 
# GrailA - Goldstone
# GrailB - Canberra
# NOTE: Temporary DSN links.
xBandLink1 = [ grazStation, grailA ]
xBandLink2 = [ grazStation, grailB ]
dsnXBandLinks = [ xBandLink1, xBandLink2 ]
xBand = FrequencyBands.x_band

## Ka-Band two-one-way KBRR links.
kABandLink1 = [ grailA, grailB ]
kABandLink2 = [ grailB, grailA ]
sstLinks = [ kABandLink1, kABandLink2 ]
kABand = FrequencyBands.ka_band

