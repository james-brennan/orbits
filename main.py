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

def main(name, line1, line2, orbital_filename):
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
    satellite = ephem.readtle(name, line1, line2)
    

    # Landsat 8
    #name = "Landsat8"
    #line1="1 39084U 13008A   16051.82349873  .00000188  00000-0  51829-4 0  9999"
    #line2="2 39084  98.1988 123.2603 0001265  89.4360 270.6984 14.57110027160810"
    #LD8 = ephem.readtle(name, line1, line2)
    

    sun = ephem.Sun()
    fov = np.radians(68.6)

    """
    Make pandas dataframe to store swath information
    """
    import pandas as pd
    data = {"DateTime": [],"DOY":[],"Month": [],
            "orbit_id":[], "ground_lat": [], 
            "ground_lon": [], "swath_width": []}
    swaths = pd.DataFrame(data)
    swaths.set_index(keys="DateTime")
    # generate shapefile

    orbit_id = 0
    # need to do splitted by hemisphere unfortunately..
    for orbit in make_an_orbit(satellite):
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
            """
            Create a tempoary dataframe for this orbit
            """
            epoch = datetime.datetime(1970, 1, 1)
            #import pdb; pdb.set_trace()
            tmp_d = {"DateTime": [(o.datetime - epoch).total_seconds() for o in orbit],
                     "DOY":[int(o.datetime.strftime('%j')) for o in orbit],
                     "Month": [o.datetime.month for o in orbit],
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
    swaths.to_csv(orbital_filename, header=True)


if __name__ == "__main__":

    name = "TERRA"
    line1 = "1 25994U 99068A   16048.43680378  .00000258  00000-0  67198-4 0  9999"
    line2 = "2 25994  98.1982 124.4247 0001352 105.3907 254.7441 14.57126067859938"
    filename = "TERRA_orbits.csv"
    main(name, line1, line2, filename)
