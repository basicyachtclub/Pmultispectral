import pandas as pd
from osgeo import gdal, ogr
import os

# Open the raster dataset
raster_ds = gdal.Open('D://UAV_Steglitz_2019/04__Processed/orthomosaics_indices_v4/2019_07_17_Flug04_ETRS1989_modified_indices.tif')

# Open the polygon shapefile
polygon_ds = ogr.Open('D://UAV_Steglitz_2019/04__Processed/areas_and_shapes/areas_EPSG_3045_pipeline_divided.shp')
polygon_lyr = polygon_ds.GetLayer()

temp_clip_ds = 'D://UAV_Steglitz_2019/04__Processed/areas_and_shapes/clipped_feature.tif'

# Define an empty list to store the extracted pixel data
data_list = []

# Loop over all features in the layer
for polygon_feat in polygon_lyr:

    # Clip the raster to the extent of the polygon feature
    xmin, xmax, ymin, ymax = polygon_feat.geometry().GetEnvelope()
    gdal.Warp(temp_clip_ds, raster_ds, outputBounds=[xmin, ymin, xmax, ymax], format='GTiff')

    # Open the clipped raster dataset
    clip_ds = gdal.Open(temp_clip_ds)

    # Get the pixel values for all bands in the raster dataset
    for i in range(clip_ds.RasterCount):
        band = clip_ds.GetRasterBand(i + 1)
        polygon_data = band.ReadAsArray()
        data_list.append((polygon_feat.GetFID(), i + 1, polygon_data))

# Create a Pandas DataFrame from the list of pixel data
df = pd.DataFrame(data_list, columns=['FID', 'Band', 'PixelData'])

os.remove(temp_clip_ds)
