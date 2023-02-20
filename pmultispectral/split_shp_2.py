import fiona
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from shapely.geometry import LineString, MultiPolygon, Polygon, shape, mapping
from shapely.ops import split

tolerance = 1

def save_to_disk(divided_polygons, filename):
    schema = {
        'geometry': 'Polygon',
        'properties': {},
    }
    crs = {'init': 'epsg:4326'}
    
    with fiona.open(filename, 'w', 'ESRI Shapefile', schema, crs) as dst:
        for polygon in divided_polygons:
            dst.write({
                'geometry': mapping(polygon),
                'properties': {}
            })

def split_polygon(polygon, split_percentage):
    centroid = polygon.centroid
    minx, miny, maxx, maxy = polygon.bounds
    mid = (minx + maxx) / 2
    cut_line = LineString([(centroid.x, miny), (centroid.x, maxy)])
    #cut_line = LineString([(minx, centroid.y), (maxx, centroid.y)])
    #minx, miny, maxx, maxy = polygon.bounds
    #mid = (minx + maxx) / 2
    #cut_line = LineString([(mid, miny), (mid, maxy)])
    divided_polygons = split(polygon, cut_line)
    divided_polygons = sorted(divided_polygons, key=lambda p: p.centroid.x)
    left_polygon_area = divided_polygons[0].area
    right_polygon_area = divided_polygons[1].area
    # for p in divided_polygons:
    #         x, y = p.exterior.xy
    #         plt.plot(x, y)
    while abs(left_polygon_area - split_percentage * polygon.area) > tolerance:
        if left_polygon_area < split_percentage * polygon.area:
            minx = mid
        else:
            maxx = mid
        mid = (minx + maxx) / 2
        cut_line = LineString([(mid, miny), (mid, maxy)])
        divided_polygons = split(polygon, cut_line)
        divided_polygons = sorted(divided_polygons, key=lambda p: p.centroid.x)
        left_polygon_area = divided_polygons[0].area
        right_polygon_area = divided_polygons[1].area
        # for p in divided_polygons:
        #     x, y = p.exterior.xy
        #     plt.plot(x, y)
    return divided_polygons

def split_polygon_orthogonally(polygon, split_percentage):
    minx, miny, maxx, maxy = polygon.bounds
    mid = (miny + maxy) / 2
    cut_line = LineString([(minx, mid), (maxx, mid)])
    divided_polygons = split(polygon, cut_line)
    divided_polygons = sorted(divided_polygons, key=lambda p: p.centroid.y)
    bottom_polygon_area = divided_polygons[0].area
    top_polygon_area = divided_polygons[1].area
    # for p in divided_polygons:
    #             x, y = p.exterior.xy
    #             plt.plot(x, y)
    while abs(bottom_polygon_area - split_percentage * polygon.area) > tolerance:
        if bottom_polygon_area < split_percentage * polygon.area:
            miny = mid
        else:
            maxy = mid
        mid = (miny + maxy) / 2
        cut_line = LineString([(minx, mid), (maxx, mid)])
        divided_polygons = split(polygon, cut_line)
        divided_polygons = sorted(divided_polygons, key=lambda p: p.centroid.y)
        bottom_polygon_area = divided_polygons[0].area
        top_polygon_area = divided_polygons[1].area
        # for p in divided_polygons:
        #     x, y = p.exterior.xy
        #     plt.plot(x, y)
    return divided_polygons


#directory = "D://UAV_Steglitz_2019/00__Code/qgis/study_site"
directory = "F://UAV_Steglitz_2019/00__Code/qgis/study_site"
#directory = "/Volumes/T7/UAV_Steglitz_2019/00__Code/qgis/study_site"
string = "areas_EPSG_3045_new_new"

directory = 'F://UAV_Steglitz_2019/04__Processed/areas_and_shapes'
string = 'areas_EPSG_3045_pipeline'

divided_features = []
for filename in os.listdir(directory):
    if filename.endswith(".shp") and string in filename:
        file_path = os.path.join(directory, filename)
        with fiona.open(file_path) as src:
                for feature in src:
                    polygon = Polygon(feature["geometry"]["coordinates"][0])
                    divided_polygons = split_polygon(polygon, 0.5)
                    divided_polygons = sorted(divided_polygons, key=lambda p: p.area, reverse=True)[:2]
                    divided_polygons = [split_polygon_orthogonally(p, 0.5) for p in divided_polygons]
                    divided_polygons = [p for sublist in divided_polygons for p in sublist]
                    divided_polygons = sorted(divided_polygons, key=lambda p: p.area, reverse=True)[:4]
                    for p in divided_polygons:
                        x, y = p.exterior.xy
                        plt.plot(x, y)
                        divided_features.append(p)

                write_out_file_name = directory + "/" + string + "_fourway_split.shp"

                schema = {
                    'geometry': 'Polygon',
                    'properties': {'id': 'int'},
                }

                with fiona.open(write_out_file_name, "w", "ESRI Shapefile", schema, crs=src.crs) as sink:
                    for i, polygon in enumerate(divided_features):
                        sink.write({
                            'geometry': mapping(polygon),
                            'properties': {'id': i},
                        })

plt.show()





print("END OF FILE")



