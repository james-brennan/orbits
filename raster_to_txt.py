"""
	Process a raster tif into a text file for input into overpasses
"""
import gdal
import numpy as np

f = gdal.Open("./data/land.tif")
geo = f.GetGeoTransform()

data = f.ReadAsArray()

long_min = geo[0]
lat_min = geo[3]
long_max = long_min + geo[1] * data.shape[1] 
lat_max  = lat_min + geo[5] * data.shape[0]

coords = []

for i,lon in enumerate(np.linspace( long_min, long_max, data.shape[1] )):
	for j,lat in enumerate(np.linspace( lat_min, lat_max, data.shape[0] )):
		coords.append([ lat, lon, data[j, i]])

# save coords to a file
coords = np.array(coords)

np.savetxt("coords.csv", coords, fmt='%5.2f', delimiter=',')
