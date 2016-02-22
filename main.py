#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""

  Main routine

"""
from orbit_calculation import *
from swath_geom import *

import ephem
import datetime
import numpy as np
#import matplotlib.pyplot as plt

def main():
    """
    Steps
    1. generate shapefile to save orbits
    2. Run generator which returns per orbital swath
        1. Create polygon per orbital swath
        2. Append to shapefile
    3. Save shapefile
    """
    #name = "TERRA"
    #line1 = "1 25994U 99068A   16048.43680378  .00000258  00000-0  67198-4 0  9999"
    #line2 = "2 25994  98.1982 124.4247 0001352 105.3907 254.7441 14.57126067859938"
    #TERRA = ephem.readtle(name, line1, line2)
    

    # Landsat 8
    name = "Landsat8"
    line1="1 39084U 13008A   16051.82349873  .00000188  00000-0  51829-4 0  9999"
    line2="2 39084  98.1988 123.2603 0001265  89.4360 270.6984 14.57110027160810"
    LD8 = ephem.readtle(name, line1, line2)
    

    sun = ephem.Sun()
    fov = np.radians(68.6)

    """
    Make pandas dataframe to store swath information
    """
    import pandas as pd
    data = {"DateTime": [],"orbit_id":[], "ground_lat": [], "ground_lon": [], "swath_width": []}
    swaths = pd.DataFrame(data)
    swaths.set_index(keys="DateTime")
    # generate shapefile

    orbit_id = 0
    # need to do splitted by hemisphere unfortunately..
    for orbit in make_an_orbit(LD8):
        #import pdb; pdb.set_trace()
        if len(orbit) > 1:
            """
            So worth doing processing on orbit...

            """
            sun = ephem.Sun()

            print(orbit[0].datetime)

            for overpass in orbit:
                overpass.only_daytime_overpasses(sun)
                overpass.derive_swath_width(fov)

            # calculate heading is trickier...
            for ov in xrange(len(orbit[:-1])):
                # need to calculate difference in location between current and next
                orbit[ov].calculate_heading(orbit[ov+1])
                orbit[ov].calculate_swath_edges()
            # throw away last overpass as no heading info possible
            orbit.pop()
            #import pylab as plt
            #plt.plot([o.heading for o in orbit])
            #import pdb; pdb.set_trace()
            """
            Now do geom stuff:
            1. make polygon for this swath
            """
            #import pdb; pdb.set_trace()

            """
            Pickle to figure this out
            """
            # from shapely.geometry import MultiLineString
            # import pickle
            # with open("orbit%i.pik" %id_poly , "wb") as f:
            #     pickle.dump(orbit, f)
            # print "picked"
            # print orbit[0].true_heading
            #continue
            """
            Create a tempoary dataframe for this orbit
            """
            epoch = datetime.datetime(1970, 1, 1)
            tmp_d = {"DateTime": [(o.datetime - epoch).total_seconds() for o in orbit],
                     "orbit_id": orbit_id * np.ones(len(orbit)),
                     "ground_lat": [o.lat for o in orbit],
                     "ground_lon": [o.long for o in orbit],
                     "swath_width": [o.swath_width for o in orbit]}
            tmp = pd.DataFrame(tmp_d)
            tmp.set_index(keys="DateTime")
            #import pdb; pdb.set_trace()
            orbit_id +=1 
            """
            Append to main dataframe
            """
            swaths = swaths.append(tmp)
            #swaths.set_index(keys="DateTime")

    """
    Save the DataFrame to a file
    """
    swaths = swaths.set_index(keys="DateTime")
    #swaths.set_index(keys="DateTime")
    #import pdb; pdb.set_trace()
    swaths.to_csv("orbits.csv")


if __name__ == "__main__":
    main()
