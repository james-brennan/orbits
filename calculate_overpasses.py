"""
	
	Calculate overpasses

"""
import pandas as pd



def closest_node(node, nodes):
    dist_2 = (nodes - node)**2
    return np.argmin(dist_2), dist_2[np.argmin(dist_2)]


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    from http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6378137.0 # earth radius [m]
    return c * r


def load_orbits(file):
	"""

	"""
	df = pd.DataFrame.from_csv(file)
	return df

def calculate(location, orbits_df):
	"""
	Take lat long locations and compare with
	the orbits to calculate number of overpasses
	in a year

	"""
	lat, lon = location
	counts = 0
	d = []
	swath_distances = []
	for orbit in np.unique(orbits_df["orbit_id"]).astype(int):
		"""
		Find point at the same latitude which
		"""
		the_swath = df.loc[df['orbit_id'] == orbit]
		swath_lats = the_swath.ground_lat.values
		nearest_loc, distance = closest_node(lat, swath_lats)
		"""
		Needs to be less than a certain distance...
		"""
		#assert distance < 0.1**2 # assert less than 0.05 of a degree away
		swath_distances.append([orbit, nearest_loc, distance])
		"""
		We now need to check whether the location and swath are 
		within the swath_width distance

		"""
		swlat, swlon = the_swath.iloc[nearest_loc].ground_lat, the_swath.iloc[nearest_loc].ground_lon
		distance = haversine(lon, lat, swlon, swlat)
		"""
		distance should be less than swath_width/2
		"""
		if distance < 0.5 * the_swath.iloc[nearest_loc].swath_width:
			counts += 1
			d.append(distance)
	return counts, swath_distances


location = 20, 0

df = load_orbits("orbits.csv")
test = calculate(location, df)
print test[0]

np.savetxt("test.csv", np.array(test[1]), fmt="%5.4g")


# make lats file...

coords = []
for lat in np.linspace(-90,90,360):
	for lon in np.linspace(-180,180,720):
		coords.append([lat, lon])

coords = np.array(coords)
np.savetxt("coords.csv", coords, fmt='%5.2f', delimiter=',')



s = []
for i in xrange(-90,90,1):
	location = 52, i
	s.append(calculate(location, df))



df = load_orbits("orbits.csv")



counts = np.genfromtxt("counts")
