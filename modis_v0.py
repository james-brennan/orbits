"""

Minimal working example...

"""
import ephem
import datetime
import numpy as np
import matplotlib.pyplot as plt


class overpass(object):
    """
    Class to store overpass for a location
    """
    def __init__(self, lat, long, datetime, elevation, eclipsed):
        self.lat = lat
        self.long = long
        self.datetime = datetime
        self.daytime = None
        self.solarZenith = None
        self.sat_elevation = elevation # elevation of satellite
        self.eclipsed = eclipsed # if eclisped by the earth --> same as night?
        self.swath = None
    def derive_swath_width(self, fov):
        """

        """
        R_e = 6378137.0 # earth radius [m]
        s = 0.5 * fov # half of field of view
        h = self.sat_elevation
        sin_alpha = np.arcsin( ( np.sin(s) * (R_e + h) ) / ( R_e )   ) - s
        alpha = np.sin(sin_alpha)
        swath = 2*((alpha/2*np.pi) * R_e) # in metres
        self.swath =  swath



def get_overpass(orbital, time):
    """
    Function which returns a lat and lon for a time
    for the given pyephem orbital
    """
    orbital.compute(time)
    the_overpass = overpass( orbital.sublat / ephem.degree,
                             orbital.sublong / ephem.degree,
                             time, orbital.elevation, orbital.eclipsed)
    return the_overpass



"""

    Potential method for only daytime overpasses

"""
def only_daytime_overpasses(sensor_overpass, sun):
    """
    Return only those which are visible -- this will take awhile i imagine
    """
    observer_on_the_ground = ephem.Observer()
    observer_on_the_ground.lat = np.radians(sensor_overpass.lat)
    observer_on_the_ground.long = np.radians(sensor_overpass.long)
    observer_on_the_ground.date = sensor_overpass.datetime

    """
    Improvment from
    http://stackoverflow.com/questions/15044521/
            javascript-or-python-how-do-i-figure-out-if-its-night-or-day

    think should work without timezones
    -- essentially next sunset should be before the next sunset

    For it to be the day time the sunset must be nearer than
    the next sunrise


    NOTE: towards the poles the sun never rises or sets
          depending on time of year. When this happens
          pyephem raises an error...
          These are some annoying edge cases to deal
          with

    """

    #import pdb; pdb.set_trace()
    try:
        next_sunrise= observer_on_the_ground.next_rising(sun).datetime()
        next_sunset = observer_on_the_ground.next_setting(sun).datetime()
    except (ephem.AlwaysUpError):
        # polar summer and sun never sets
        # so it must be daytime...
        sensor_overpass.daytime = True
        sun.compute(observer_on_the_ground)
        # can check with solarzenith angle
        solZenith = np.degrees(sun.alt)
        return None
    except (ephem.NeverUpError):
        # polar winter and sun never sets
        # so it must be nighttime
        sensor_overpass.daytime = False
        sun.compute(observer_on_the_ground)
        # can check with solarzenith angle
        solZenith = np.degrees(sun.alt)
        return None
    # if no exceptions it's not polar and sun does rise and set...
    if next_sunset < next_sunrise:
        sensor_overpass.daytime = True
    elif next_sunset > next_sunrise:
        sensor_overpass.daytime = False
    else:
        import pdb; pdb.set_trace() # something wrong
        sensor_overpass.daytime = -1 #error
    sun.compute(observer_on_the_ground)
    # can check with solarzenith angle
    solZenith = np.degrees(sun.alt)
    sensor_overpass.solarZenith = solZenith
    return None


"""
Sanity check? plot only daytime overpasses
"""

def plot_daytime_overpasses(overpasses_list):
    sun = ephem.Sun()
    # check all overpasse
    tmp = []
    for over in overpasses_list:
        only_daytime_overpasses(over, sun)
        if over.daytime:
            tmp.append(over)
    # only plot day time
    lon, lat = [], []
    for ov in tmp:
        lon.append(ov.long)
        lat.append(ov.lat)
    plt.plot(lon, lat, 'ro')
    # and also plot all?
    lon, lat = [], []
    for ov in overpasses_list:
        lon.append(ov.long)
        lat.append(ov.lat)
    plt.plot(lon, lat, 'k+')
    #


# from http://stackoverflow.com/questions/10688006/generate-a-list-of-datetimes-between-an-interval-in-python
def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta


"""

    MAIN

"""
name = "TERRA"
line1 = "1 25994U 99068A   16048.43680378  .00000258  00000-0  67198-4 0  9999"
line2 = "2 25994  98.1982 124.4247 0001352 105.3907 254.7441 14.57126067859938"
TERRA = ephem.readtle(name, line1, line2)

overpasses = []
for time in perdelta(datetime.datetime(2016, 1, 1, 0,0,0,0), datetime.datetime(2016, 2, 1, 0,0,0,0),
                        datetime.timedelta(minutes=5)):
    overpasses.append(get_overpass(TERRA, time))




"""
plot it.. seems to work...
"""
plot_daytime_overpasses(overpasses)
plt.show()

plt.plot([o.solarZenith for o in overpasses], [o.sat_elevation for o in overpasses], 'ro')
plt.show()

"""
 next steps... Calculate ground coverage for the day passes...
 fov stuff etc...
    1. assume spherical earth

    2.


    Explanation of oblique triangle method from swath_width.pdf



"""
def derive_swath_width(fov, sensor_altitude):
    """

    """
    R_e = 6378137.0 # earth radius [m]
    s = 0.5 * fov # half of field of view
    h = sensor_altitude
    sin_alpha = np.arcsin( ( np.sin(s) * (R_e + h) ) / ( R_e )   ) - s
    alpha = np.sin(sin_alpha)
    swath = 2*((alpha/2*np.pi) * R_e) # in metres
    return swath

def calculate_swath_edges(overpass):
    """
    returns min_lat, min_lon and max_lat,_max edges of swath

    equations from
    http://stackoverflow.com/questions/4102520/how-to-transform-a-distance-from-degrees-to-metres


    remeber that this is the arc_distance [m]
    """
    R_e = 6378137.0 # earth radius [m]
    dlatitude = overpass.swath_width * 360 / (2*np.pi * R_e)
    dlongitude =  overpass.swath_width *360 * / (2*np.pi* np.cos(latitude) )

    # now calculate +/- from the actual lat/long
    lats = [overpass.lat - dlatitude, overpass.lat + dlatitude]
    lons = [overpass.long - dlongitude, overpass.long + dlongitude]

    # need to wrap to -90..90 and -180..180 probably!
    returns lat, lons
