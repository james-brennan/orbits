#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
  Locating IDL crossings

  from answer to 
  http://gis.stackexchange.com/questions/18562/how-can-i-make-a-polyline-wrap-around-the-world

"""

from osgeo import ogr
from osgeo import osr
import numpy as np
from shapely.geometry.polygon import LinearRing
from osgeo import ogr
from shapely.geometry import Polygon, MultiPolygon






def plot_polys(multi):
    for pl in multi:
        plt.plot(pl.exterior.xy[0], pl.exterior.xy[1])


def plot_orbit(orbit):
    lat1 = [o.lats[1] for o in orbit]
    lat0 =  [o.lats[0] for o in orbit]
    lon0 =  [o.lons[0] for o in orbit]
    lon1 =  [o.lons[1] for o in orbit]
    plt.plot(lon1, lat1)
    plt.plot(lon0, lat0)



def solve_great_circle(lat0, lon0, lat1, lon1):
    """
    http://gis.stackexchange.com/questions/18562/how-can-i-make-a-polyline-wrap-around-the-world
    """
    lat0 = np.radians(lat0)
    lon0 = np.radians(lon0)
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    (x0, y0, z0) = (np.cos(lon0)*np.sin(lat0), np.sin(lon0)*np.sin(lat0), np.cos(lat0))
    (x1, y1, z1) = (np.cos(lon1)*np.sin(lat1), np.sin(lon1)*np.sin(lat1), np.cos(lat1))

    """
    To get intersection distance solve:

    t * y0 + (1-t) * y1 = 0
    """
    t = y1 / (y1 - y0)
    # intersection coords are
    (x, y, z) = (t * x0 + (1-t) * x1, 0, t * z0 + (1-t) * z1)
    lat2 = np.arctan(z/x)
    return np.degrees(lat2)


"""

    Breakpoint needs to be represented a certain way:
    after lat0 aattach another point with lat2,-180 if lon0 is negative or
    lat2, 180 if lon0 is positive 

    Then attach before lat1,lon1 a similar rule...

"""


def make_swath2(orbit):
    """
    Steps do splitting
    """
    limited_pass = [o for o in orbit if ((o.lat > -70) & (o.lat < 70) )]
    """
    Split coords into leftmost and rightmost

    think this needs to be cleverer...
        eg this will change if satelitte is ascending or descending

    idea 1: check bottom and top for both boundary longs
        the left one should be less for both

    """
    ##import pdb; pdb.set_trace()
    Acoords = np.array([[o.lats[0], o.lons[0]] for o in limited_pass])
    Bcoords = np.array([[o.lats[1], o.lons[1]] for o in limited_pass])
    all_coords = np.concatenate((Acoords, Bcoords[::-1]))
    x = all_coords[:,1]
    y = all_coords[:,0]
    xy = np.dstack((x,y))
    poly = Polygon(xy[0])
    return poly



def make_swath(orbit):
    limited_pass = [o for o in orbit if ((o.lat > -70) & (o.lat < 70) )]
    """
    Split coords into leftmost and rightmost

    think this needs to be cleverer...
        eg this will change if satelitte is ascending or descending

    idea 1: check bottom and top for both boundary longs
        the left one should be less for both

    """
    ##import pdb; pdb.set_trace()
    Acoords = np.array([[o.lats[0], o.lons[0]] for o in limited_pass])
    Bcoords = np.array([[o.lats[1], o.lons[1]] for o in limited_pass])
    """
    For each set see if we need to split

    There are a few cases:

    1. Only one swath edge crosses IDL 
    2. Both cross

    -- either way end up with two polygons
        but they're construction is different...

    Need to see which case we get...

    """
    
    d = {"ACoords": None, "BCoords": None }


    for i,c in zip(["ACoords", "BCoords"],[Acoords, Bcoords]) :
        split_coords = split_coords_around_IDL(c)
        if split_coords[0] == True:
            # coords split by crossing IDL
            # save to dictionary d
            d[i]  = split_coords
        elif split_coords[0] == False:
            d[i] = split_coords
    ##import pdb; pdb.set_trace()
    """
    Figure out which case we have of 1 or 2
    """
    ##import pdb; pdb.set_trace()
    if (d["ACoords"][0] == True) & (d["BCoords"][0] == True):
        """
        Both cross IDL
        So process each set into two polygons
        
        """
        polys = []
        for i in xrange(2):
            set_of_coords = np.concatenate((d["ACoords"][1+i], d["BCoords"][1+i][::-1]))
            poly = Polygon(set_of_coords)
            polys.append(poly)
        mpoly = MultiPolygon(polys)
    elif (d["ACoords"][0] == True) & (d["BCoords"][0] == False):
        """
        Only Acoords cross IDL
        So process each set into two polygons

        Need to make two polygons by creating two coords along idl at correct latitude
        of each crossing

        Step
        1. Figure out which hemisphere ACoords 
        """
        #import pdb; pdb.set_trace()
        set1= d["ACoords"][1]
        set2 = d["ACoords"][2]

        # for both we need to append a point with longitude at IDL 
        # and the right latitude

        tmp_sort = set1[set1[:,1].argsort()][::-1]
        if tmp_sort[-1][1] < 0:
            # in west
            lat = tmp_sort[0][0]
            lon = -179.9999
            set1_corner = (lat, lon)
        if tmp_sort[-1][1] > 0:
            # in west
            lat = tmp_sort[0][0]
            lon = +179.9999
            set1_corner = (lat, lon)
        set1 = np.vstack((set1, set1_corner))

        """
        This one is more difficult:
            corner needs to be higher up...
            needs to be at maximum/minimum latitude found in set1...
        """

        tmp_sort = set2[set2[:,1].argsort()][::-1]
        if tmp_sort[-1][1] < 0:
            # in west
            lat = set1_corner[0]
            lon = -179.9999
            set2_corner = (lat, lon)
        if tmp_sort[-1][1] > 0:
            # in west
            lat = set1_corner[0]
            lon = +179.9999
            set2_corner = (lat, lon)

        set2 = np.vstack((set2_corner, set2))

        """
        Now need to figure out which set is polygons
        """
        # need to swap axes too...
        x = set1[:,1]
        y = set1[:,0]
        xy = np.dstack((x,y))
        west_ply = Polygon(xy[0])
        set2_with_bcoords = np.concatenate((d["BCoords"][1], set2[::-1]))
        x = set2_with_bcoords[:,1]
        y = set2_with_bcoords[:,0]
        xy = np.dstack((x,y))
        east_ply = Polygon(xy[0])
        mpoly = MultiPolygon((west_ply,east_ply))

    elif (d["ACoords"][0] == False) & (d["BCoords"][0] == True):
        """
        Only Bcoords cross IDL
        So process each set into two polygons
        Reverse situation from above:
            switch?
        """
        #import pdb; pdb.set_trace()
        set1= d["BCoords"][1]
        set2 = d["BCoords"][2]

        # for both we need to append a point with longitude at IDL 
        # and the right latitude

        tmp_sort = set1[set1[:,1].argsort()][::-1]
        if tmp_sort[-1][1] < 0:
            # in west
            lat = set1[:,0].max()
            lon = -179.9999
            set1_corner = (lat, lon)
        if tmp_sort[-1][1] > 0:
            # in west
            lat = set1[:,0].max()
            lon = +179.9999
            set1_corner = (lat, lon)
        set1 = np.vstack((set1, set1_corner))

        """
        This one is more difficult:
            corner needs to be higher up...
            needs to be at maximum/minimum latitude found in set1...
        """

        tmp_sort = set2[set2[:,1].argsort()][::-1]
        if tmp_sort[-1][1] < 0:
            # in west
            lat = set1_corner[0]
            lon = -179.9999
            set2_corner = (lat, lon)
        if tmp_sort[-1][1] > 0:
            # in west
            lat = set1_corner[0]
            lon = +179.9999
            set2_corner = (lat, lon)

        set2 = np.vstack((set2_corner, set2))

        """
        Now need to figure out which set is polygons
        """
        #import pdb; pdb.set_trace()
        # need to swap axes too...
        x = set1[:,1]
        y = set1[:,0]
        xy = np.dstack((x,y))
        west_ply = Polygon(xy[0])
        set2_with_acoords = np.concatenate((d["ACoords"][1], set2[::-1]))
        x = set2_with_acoords[:,1]
        y = set2_with_acoords[:,0]
        xy = np.dstack((x,y))
        east_ply = Polygon(xy[0])
        mpoly = MultiPolygon((west_ply,east_ply))

    elif (d["ACoords"][0] == False) & (d["BCoords"][0] == False):
        """
        Neither cross IDL:

        This one is tricky too because sometimes one swath edge
        is in one hemisphere and the other in the other...

        """
       
        """
        Check whether this case is a swath:
            1. Crossing the prime merdian
            2. Crossing the dateline

        The case can be determined by if all or only some of the coords
        are across hemispheres
        """
        a_any_in_east = np.any(d["ACoords"][1][:,1] >0) # any a coords in east
        b_any_in_east = np.any(d["BCoords"][1][:,1] >0) # any b coords in east
        a_all_in_east = np.all(d["ACoords"][1][:,1] >0) # any a coords in east
        b_all_in_east = np.all(d["BCoords"][1][:,1] >0) # any b coords in east

        """
        If both are true or both false is easy...
        """
        """
        First check if all are in one hemisphere for both
        think right---
        """
        if a_all_in_east == b_all_in_east:
            # all in the same hemisphere -- easiest case
            #import pdb; pdb.set_trace()
            all_coords = np.concatenate((d["ACoords"][1], d["BCoords"][1][::-1]))
            x = all_coords[:,1]
            y = all_coords[:,0]
            xy = np.dstack((x,y))
            poly = Polygon(xy[0])
            mpoly = MultiPolygon([poly])
            return mpoly
        elif (a_any_in_east == True) & (b_any_in_east == False):
            """
            Now: tricky...

            Case where both cross prime meridian
            case where only one crosses prime meridian

            """
            #import pdb; pdb.set_trace()
            """
            A crosses prime meridian but b doesn't
            """
            # should be same as above...
            all_coords = np.concatenate((d["ACoords"][1], d["BCoords"][1][::-1]))
            x = all_coords[:,1]
            y = all_coords[:,0]
            xy = np.dstack((x,y))
            poly = Polygon(xy[0])
            mpoly = MultiPolygon([poly])
            return mpoly
        elif (a_any_in_east == False) & (b_any_in_east == True):
            """
            B crosses prime meridian but A doesn't
            """
            #import pdb; pdb.set_trace()
            all_coords = np.concatenate((d["ACoords"][1], d["BCoords"][1][::-1]))
            x = all_coords[:,1]
            y = all_coords[:,0]
            xy = np.dstack((x,y))
            poly = Polygon(xy[0])
            mpoly = MultiPolygon([poly])
            return mpoly
        elif (a_any_in_east == True) & (b_any_in_east == True):
            """
            B crosses prime meridian AS DOES A 
            """
            #import pdb; pdb.set_trace()
            all_coords = np.concatenate((d["ACoords"][1], d["BCoords"][1][::-1]))
            x = all_coords[:,1]
            y = all_coords[:,0]
            xy = np.dstack((x,y))
            poly = Polygon(xy[0])
            mpoly = MultiPolygon([poly])
            return mpoly
        elif a_all_in_east != b_all_in_east:
            """
            Now trickier cases still
            if all of either is in east and the other all in west
            """

            """
            not in the same hemisphere
            Need to make two polygons 
            """
            #import pdb; pdb.set_trace()
            polys = []
            for hemi, coords in zip([a_all_in_east, b_all_in_east], [d["ACoords"][1], d["BCoords"][1]]):
                if hemi: # is this line in the east or west?
                    """ 
                    in east
                    Need to add some corners at 179.99 at min lat and max lat...
                    """
                    # 1. sort the coords
                    ##import pdb; pdb.set_trace()
                    top_corner = [coords[:,0].max(), 179.999]
                    bottom_corner = [coords[:,0].min(), 179.999]
                    # append these 
                    d2 = np.vstack(( coords, bottom_corner, top_corner))
                    # make poly...
                    x = d2[:,1]
                    y = d2[:,0]
                    xy = np.dstack((x,y))
                    ply = Polygon(xy[0])
                    polys.append(ply)
                else:
                    # in west
                    top_corner = [coords[:,0].max(), -179.999]
                    bottom_corner = [coords[:,0].min(), -179.999]
                    # append these 
                    d2 = np.vstack(( coords, bottom_corner, top_corner))
                    x = d2[:,1]
                    y = d2[:,0]
                    xy = np.dstack((x,y))
                    ply = Polygon(xy[0])
                    polys.append(ply)
            # make multipolygon
            mpoly = MultiPolygon(polys)
            return mpoly
    pass
    return mpoly






def split_coords_around_IDL(coords):

    """
    Do firsts
    """
    fc = coords
    diff = abs(np.diff(fc[:,1]))

    # index where it crosses the dateline
    # before 
    idl = diff >= 180

    # where is this
    where_idl = np.where(idl==True)
    # split at these locations -- maybe more than 1 but assume 1 for now
    if where_idl[0].shape[0] > 0:
        fc_1 = fc[1:where_idl[0]]
        fc_2 = fc[where_idl[0]+1:]


        # the last of fc_1 and first of fc_2 are now either side of IDL
        #need to calculate intermediate points 
        lat0, lon0 = fc_1[-1]
        lat1, lon1 = fc_2[0]
        intersection_lattiude = solve_great_circle(lat0, lon0, lat1, lon1)

        """
        Attach this point to ends of the split coords
        Turned off for now
        """
        #if lon0 < 0:
        #   loc = (intersection_lattiude, -179.9999)
        #   fc_1 = np.vstack((fc_1, loc))
        #else:
        #   loc = (intersection_lattiude, 179.9999)
        #   fc_1 = np.vstack((fc_1, loc))
        #if lon1 < 0:
        #   loc = (intersection_lattiude, -179.9999)
        #   fc_2 = np.vstack((loc, fc_2))
        #else:
        #   loc = (intersection_lattiude, 179.9999)
        #   fc_2 = np.vstack((loc, fc_2))
        return True, fc_1, fc_2
    else:
        return False, fc

"""

    might not need to do the interpolate stuff 
    just splitting might be okay as doing at high frequency...
"""
