### Local imports.
from observations.n_way_doppler import \
    two_way_doppler_averaged, one_way_doppler_averaged
from bodies.grail_spacecraft import \
    grailA, grailB


### Constant values from validation case. (Park et al., 2012, p. 396)
# Range-rate standard deviations. 
DSNSIGMA = 5e-5             # m/s
KBRRSIGMA = 1e-6            # m/s

# Count times. 
DSNCOUNT = 10               # s
KBRRCOUNT = 5               # s

# Links 
# X-band DSN links 
# GrailA - Goldstone
# GrailB - Canberra
# K-Band two-one-way KBRR links.
kBandLink1 = [ grailA, grailB ]
kBandLink2 = [ grailB, grailA ]

