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
    name = "TERRA"
    line1 = "1 25994U 99068A   16048.43680378  .00000258  00000-0  67198-4 0  9999"
    line2 = "2 25994  98.1982 124.4247 0001352 105.3907 254.7441 14.57126067859938"
    TERRA = ephem.readtle(name, line1, line2)
    sun = ephem.Sun()
    fov = np.radians(110)

    # generate shapefile
    spatialReference = osr.SpatialReference()
    # WGS84
    spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

    # Now convert it to a shapefile with OGR
    driver = ogr.GetDriverByName('Esri Shapefile')
    ds = driver.CreateDataSource('orbits.shp')
    layer = ds.CreateLayer('testing',  spatialReference, ogr.wkbMultiLineString)
    # Add one attribute
    layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn('swidth', ogr.OFTReal))
    defn = layer.GetLayerDefn()

    id_poly = 0

    # need to do splitted by hemisphere unfortunately..
    for orbit in make_an_orbit(TERRA):
        #import pdb; pdb.set_trace()
        if len(orbit) > 1:
            """
            So worth doing processing on orbit...

            """
            sun = ephem.Sun()
            fov = np.radians(110)

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
            from shapely.geometry import MultiLineString
            import pickle
            with open("orbit%i.pik" %id_poly , "wb") as f:
                pickle.dump(orbit, f)
            print "picked"
            print orbit[0].true_heading
            #continue
            """
            annyoing dateline wrap around means we need to check
            whether an orbit crosses it
            if it does we need to make two polygons

            """
            import splitting_geoms
            try:
                swath_polygon = make_two_swath_linestrings(orbit)
            except ValueError: # not enough points for orbit...
                continue

            line = MultiLineString([[[o.long, o.lat] for o in orbit]])


            # add to the output shapefile
            ## If there are multiple geometries, put the "for" loop here

            # Create a new feature (attribute and geometry)
            feat = ogr.Feature(defn)
            feat.SetField('id', id_poly)
            feat.SetField('swidth', 1.00)
            id_poly +=1
            # Make a geometry, from Shapely object
            geom = ogr.CreateGeometryFromWkb(swath_polygon.wkb)
            feat.SetGeometry(geom)

            layer.CreateFeature(feat)
            feat = geom = None  # destroy these

    # Save shapefile
    ds = layer = feat = geom = None


if __name__ == "__main__":
    main()
