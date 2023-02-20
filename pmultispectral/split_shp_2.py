import fiona
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from shapely.geometry import LineString, MultiPolygon, Polygon, shape, mapping
from shapely.ops import split

tolerance = 1 # PERCENTAGE TOLERANCE FOR THE SPLIT

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

def divide_shp_file(directory, filename):
    file_path = os.path.join(directory, filename)
    divided_features = []
    with fiona.open(file_path) as src:
            for feature in src:
                polygon = Polygon(feature["geometry"]["coordinates"][0])
                divided_polygons = split_polygon(polygon, 0.5)
                divided_polygons = sorted(divided_polygons, key=lambda p: p.area, reverse=True)[:2]
                divided_polygons = [split_polygon_orthogonally(p, 0.5) for p in divided_polygons]
                divided_polygons = [p for sublist in divided_polygons for p in sublist]
                divided_polygons = sorted(divided_polygons, key=lambda p: p.area, reverse=True)[:4]

                for i, d in enumerate(divided_polygons):
                    #x, y = d.exterior.xy
                    #plt.plot(x, y)

                    divided_feature = { # copying feature attribute table properties
                        'type': 'Feature',
                        'geometry': mapping(d),
                        'properties': feature["properties"].copy() 
                    }
                    divided_feature["properties"]["split_id"] = i # save split_id
                    divided_features.append(divided_feature)

            schema = src.schema.copy()
            # add the new column to the attribute table schema for writing
            schema["properties"]["split_id"] = "int"

            output_file = os.path.join(directory, filename[:-4] + "_divided.shp")
            with fiona.open(output_file, 'w', driver='ESRI Shapefile', crs=src.crs, schema=schema) as dst:
                for divided_feature in divided_features:
                    dst.write(divided_feature)
    #plt.show()

# if __name__ == "__main__":
#     import sys

#     if len(sys.argv) < 2:
#         print("Please provide the filename string as an argument.")
#         sys.exit()

#     filename = sys.argv[1]
#     directory = os.path.dirname(os.path.abspath(filename))
#     divide_shp_file(directory, filename)

#directory = "D://UAV_Steglitz_2019/00__Code/qgis/study_site"
#directory = "F://UAV_Steglitz_2019/00__Code/qgis/study_site"
#directory = "/Volumes/T7/UAV_Steglitz_2019/00__Code/qgis/study_site"
#filename= "areas_EPSG_3045_new_new.shp"

directory = 'F://UAV_Steglitz_2019/04__Processed/areas_and_shapes'
filename = 'areas_EPSG_3045_pipeline_divided.shp'

divide_shp_file(directory, filename)

print("END OF FILE")


