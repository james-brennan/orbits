"""

  Idea
  ====

  Calculate minimum DOB accurary per sensor and then per algorithm


  1. for sensor
  -------------


  1. Need to derive satellite tracks for a year (pyephm?)
  2. Convert to a ground track with swath width calculations

  2. Generate a global cloudiness index per day of year / per hour too
  --------------------------------------------------------------------

    This is more tricky!
    Preferably as a pdf so can do clever bayes shit



  STEP 1.

  Deriving for iss
  from https://programmingforresearch.wordpress.com/
        2012/10/30/using-pyephem-to-get-the-ground-coordinates-of-a-satellite/

  import ephem
  import datetime
  ## [...]
  name = "ISS (ZARYA)";
  line1 = "1 25544U 98067A   12304.22916904  .00016548  00000-0  28330-3 0  5509";
  line2 = "2 25544  51.6482 170.5822 0016684 224.8813 236.0409 15.51231918798998";




"""

# try TERRA
name = "TERRA"
line1 = "1 25994U 99068A   16048.43680378  .00000258  00000-0  67198-4 0  9999"
line2 = "2 25994  98.1982 124.4247 0001352 105.3907 254.7441 14.57126067859938"
tle_rec = ephem.readtle(name, line1, line2)
tle_rec.compute()


# choose a datetime
date = datetime.datetime(2016,1,1,12,0,0)
tle_rec.compute(date) # works


# now lets try a range? and plot?
# for january 1st

dates =


# from http://stackoverflow.com/questions/10688006/generate-a-list-of-datetimes-between-an-interval-in-python
def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta

times = []

for result in perdelta(datetime.datetime(2016, 1, 1, 0,0,0,0), datetime.datetime(2016, 2, 1), datetime.timedelta(minutes=1)):
    times.append(result)

times = np.array(times)

lons = []
lats = []

for ts in times:
    # compute location of orbit
    tle_rec.compute(ts) # works
    # save lat and lon
    lons.append(tle_rec.sublong)
    lats.append(tle_rec.sublat)




# test it...
locs = []
for time in perdelta(datetime.datetime(2016, 1, 1, 0,0,0,0), datetime.datetime(2016, 1, 1, 1,0,0,0),
                        datetime.timedelta(minutes=1)):
    locs.append(get_location(tle_rec, time))

locs = np.array(locs)
plt.plot(locs.T[0], locs.T[1], 'ro-'); plt.show()



# sun stuff

sun.compute(date)


"""
    Check daytime algorithm?
    =========================

    1. Calculate satellite overpasses
    2. make an observer where satellite overpasses [lat, lon]
    3. Calculate sun elevation
    4. throw away overpass points where sun zenith above an angle

"""


TERRA = ephem.readtle(name, line1, line2)
date = datetime.datetime(2016,1,1,12,0,0)
terra_loc = get_location(TERRA, date)

# what is the elevation of the sun at this time?
# 1. make observer
observer_on_the_ground = ephem.Observer()
observer_on_the_ground.lat = terra_loc[0]
observer_on_the_ground.long = terra_loc[1]
observer_on_the_ground.date = date

# 1. set up sun
sun = ephem.Sun()
# compute sun elevation stuff
sun.compute(observer_on_the_ground)
sun_alt = np.degrees(sun.alt)
# if sun_alt < 0 it's below the horizon of this location




class overpass(object):
    """
    Class to store overpass for a location
    """
    def __init__(self, lat, long, datetime):
        self.lat = lat
        self.long = long
        self.datetime = datetime
        self.daytime = None
        self.solarZenith = None

from ephem import degree

def get_overpass(orbital, time):
    """
    Function which returns a lat and lon for a time
    for the given pyephem orbital
    """
    orbital.compute(time)
    the_overpass = overpass( orbital.sublat / ephem.degree,
                             orbital.sublong / ephem.degree,
                             time)
    return the_overpass

TERRA = ephem.readtle(name, line1, line2)
date = datetime.datetime(2016,1,1,12,0,0)
terra_gtg = get_overpass(TERRA, date)



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
    elif next_sunset < next_sunrise:
        sensor_overpass.daytime = False
    else:
        sensor_overpass.daytime = -1 #error
    sun.compute(observer_on_the_ground)
    # can check with solarzenith angle
    solZenith = np.degrees(sun.alt)
    sensor_overpass.solarZenith = solZenith
    return None

"""
Check it works?
"""
TERRA = ephem.readtle(name, line1, line2)
date = datetime.datetime(2016,1,1,12,0,0)
terra_gtg = get_overpass(TERRA, date)
only_daytime_overpasses(terra_gtg, sun)

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

"""
Generate a day's worth
"""
overpasses = []
for time in perdelta(datetime.datetime(2016, 1, 1, 0,0,0,0), datetime.datetime(2016, 2, 1, 0,0,0,0),
                        datetime.timedelta(minutes=5)):
    overpasses.append(get_overpass(TERRA, time))
"""
plot it..
"""
plot_daytime_overpasses(overpasses)
plt.show()


TERRA = ephem.readtle(name, line1, line2)
date = datetime.datetime(2016,1,1,12,0,0)
terra_gtg = get_overpass(TERRA, date)
# re-checking
# what is the elevation of the sun at this time?
# 1. make observer
observer_on_the_ground = ephem.Observer()
observer_on_the_ground.lat = terra_gtg.lat
observer_on_the_ground.long = terra_gtg.long
observer_on_the_ground.date = terra_gtg.datetime

# 1. set up sun
sun = ephem.Sun()
# compute sun elevation stuff
sun.compute(observer_on_the_ground)
sun_alt = np.degrees(sun.alt)
# if sun_alt < 0 it's below the horizon of this location

# sanity make location london...
terra_gtg.long = np.radians(0)
terra_gtg.lat = np.radians(52) #still midday NYD
observer_on_the_ground.lat = terra_gtg.lat
observer_on_the_ground.long = terra_gtg.long
observer_on_the_ground.date = terra_gtg.datetime
observer_on_the_ground.previous_rising(sun)



"""
    CURRENT ISSUES TIMEs need to be in utc...
"""


def generate_timestamps(delta_mins=30):
    """
    Think this is right...
    Generate datetimes for 2016,1,1 to 2017,1,1
    Then convert to utc times

    These can then be used for the ephem dates
    """
    # from http://stackoverflow.com/questions/10688006/generate-a-list-of-datetimes-between-an-interval-in-python
    def perdelta(start, end, delta):
        curr = start
        while curr < end:
            yield curr
            curr += delta

    times = []

    for result in perdelta(datetime.datetime(2016, 1, 1, 0,0,0,0), datetime.datetime(2017, 1, 1),
                            datetime.timedelta(minutes=delta_mins)):
        times.append(result)
    # now for each time comvert to utc timestamp
    # from here:
    #  http://stackoverflow.com/questions/5067218/get-utc-timestamp-in-python-with-datetime
    utcs = []
    for dt in times:
        timestamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
        utcs.append(timestamp)
    return np.array(utcs)



get_overpass(TERRA, utcs[0])
