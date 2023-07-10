import fiona
import os
import matplotlib
import shapely.geometry as geometry
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

## quickly get the location of the hard disk
import psutil
partitions = psutil.disk_partitions()
for p in partitions:
    if p.fstype == "exFAT": # Windows
        external_drive = p.mountpoint
        logging.info('disk located at : ' + external_drive)
    elif p.fstype == "exfat": # Osx
        external_drive = p.mountpoint + "/"
        logging.info('disk located at : ' + external_drive)

######## FUNCTIONS REQUIRED ##########################

from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import split

def splitPolygon(polygon, nx, ny):
    minx, miny, maxx, maxy = polygon.bounds
    dx = (maxx - minx) / nx
    dy = (maxy - miny) / ny

    minx, miny, maxx, maxy = polygon.bounds
    dx = (maxx - minx) / nx  # width of a small part
    dy = (maxy - miny) / ny  # height of a small part
    horizontal_splitters = [LineString([(minx, miny + i*dy), (maxx, miny + i*dy)]) for i in range(ny)]
    vertical_splitters = [LineString([(minx + i*dx, miny), (minx + i*dx, maxy)]) for i in range(nx)]
    splitters = horizontal_splitters + vertical_splitters
    result = polygon
    
    for splitter in splitters:
        result = MultiPolygon(split(result, splitter))
    
    return result

######## REAL CODE STARTS HERE #######################


directory = external_drive + "UAV_Steglitz_2019/00__Code/qgis/study_site"
string = "areas_EPSG_3045_new_new" #"areas"

for filename in os.listdir(directory):
    if filename.endswith(".shp") and string in filename:
        file_path = os.path.join(directory, filename)
        with fiona.open(file_path) as src:
            for feature in src:
                # Get the polygon geometry from the feature
                polygon = geometry.Polygon(feature["geometry"]["coordinates"][0])
                
                # Divide the polygon into four equal parts using the splitPolygon() function
                divided_polygons = splitPolygon(polygon, 2, 2)
                
                # Plot each divided polygon
                for divided_polygon in divided_polygons:
                    x, y = zip(*divided_polygon.exterior.coords)
                    plt.plot(x, y)
                

print("end of file")
