"""

  Modis v1

"""
#from orbit_calculation import *
import ephem
import datetime
import numpy as np
import matplotlib.pyplot as plt



name = "TERRA"
line1 = "1 25994U 99068A   16048.43680378  .00000258  00000-0  67198-4 0  9999"
line2 = "2 25994  98.1982 124.4247 0001352 105.3907 254.7441 14.57126067859938"
TERRA = ephem.readtle(name, line1, line2)

overpasses = []
for time in perdelta(datetime.datetime(2016, 1, 1, 0,0,0,0), datetime.datetime(2016, 1, 1, 1,0,0,0),
                        datetime.timedelta(minutes=0.6)):
    overpasses.append(get_overpass(TERRA, time))

# for each overpasses do necessary calculations
# 1. is day?
sun = ephem.Sun()
fov = np.radians(55)

for ov in overpasses:
    ov.only_daytime_overpasses(sun)
    ov.derive_swath_width(fov)

# calculate heading is trickier...
for ov in xrange(len(overpasses[:-1])):
    # need to calculate difference in location between current and next
    overpasses[ov].calculate_heading(overpasses[ov+1])
    overpasses[ov].calculate_swath_edges()


plt.scatter([o.long for o in overpasses], [o.lat for o in overpasses],
            c = [o.heading for o in overpasses])

plt.plot([o.lons[0] for o in overpasses[:-1]], [o.lats[0] for o in overpasses[:-1]], 'r-*')
plt.plot([o.lons[1] for o in overpasses[:-1]], [o.lats[1] for o in overpasses[:-1]], 'k-*')


plt.plot([o.long for o in overpasses],  [o.heading for o in overpasses])
