from pickle import TRUE
from re import T
from osgeo import gdal
from osgeo import ogr
import os
import numpy as np
import csv
import pandas as pd
import logging
#import geopandas as gpd

def boundingBoxToOffsets(bbox, geot):
    col1 = int((bbox[0] - geot[0]) / geot[1])
    col2 = int((bbox[1] - geot[0]) / geot[1]) + 1
    row1 = int((bbox[3] - geot[3]) / geot[5])
    row2 = int((bbox[2] - geot[3]) / geot[5]) + 1
    return [row1, row2, col1, col2]


def geotFromOffsets(row_offset, col_offset, geot):
    new_geot = [
    geot[0] + (col_offset * geot[1]),
    geot[1],
    0.0,
    geot[3] + (row_offset * geot[5]),
    0.0,
    geot[5]
    ]
    return new_geot


def setFeatureStats(fid, min, max, mean, median, sd, sum, count, centroid, area, bbox, info, \
                    names=["min", "max", "mean", "median", "sd", "sum", "count", "centroid", "area", "bbox", "info", "id"]):
    featstats = {
    names[0]: min,
    names[1]: max,
    names[2]: mean,
    names[3]: median,
    names[4]: sd,
    names[5]: sum,
    names[6]: count,
    names[7]: centroid,
    names[8]: area,
    names[9]: bbox,
    names[10]: info,
    names[11]: fid,
    }
    return featstats

def convertDtypeValues(raster, lambda_func, conversion_factor ):
    '''Converting Formula to translate bewteen different data types'''
    raster_conv = lambda_func(raster, conversion_factor)
    return raster_conv

def zonalStatistics(fn_raster, fn_zones, band = 1, id_field = "id",\
                        adjust_func = None, \
                        adjust_value = None, \
                        band_name = None, \
                        flight_date = None, \
                        flight_number = None, \
                        flight_time = None, \
                        shadow = None, \
                        fn_csv = None):

    '''All credit for the original code goes to Konrad Hafen
    https://opensourceoptions.com/blog/zonal-statistics-algorithm-with-python-in-4-steps/'''

    # fn_raster = filename for raster data object
    # fn_zones = filename for shapefile for regions
    # fn_csv = filename for csv write out, if none is provided data is returned
    # both datasets needs to be in the same CRS

    mem_driver = ogr.GetDriverByName("Memory")
    mem_driver_gdal = gdal.GetDriverByName("MEM")
    shp_name = "temp"

    #fn_raster = "/Volumes/T7/UAV_Steglitz_2019/00__Code/qgis/first_results/14_06_2019_flug1_orginal_16bit_rectified_ndvi.tif"
    #fn_zones = "/Volumes/T7/UAV_Steglitz_2019/00__Code/qgis/first_results/areas.shp"

    r_ds = gdal.Open(fn_raster)
    p_ds = ogr.Open(fn_zones)

    lyr = p_ds.GetLayer()
    geot = r_ds.GetGeoTransform()
    # A geotransform (geot) consists in a set of 6 coefficients:
    # GT(0) x-coordinate of the upper-left corner of the upper-left pixel.
    # GT(1) w-e pixel resolution / pixel width.
    # GT(2) row rotation (typically zero).
    # GT(3) y-coordinate of the upper-left corner of the upper-left pixel.
    # GT(4) column rotation (typically zero).
    # GT(5) n-s pixel resolution / pixel height (negative value for a north-up image).

    nodata = r_ds.GetRasterBand(band).GetNoDataValue()

    zstats = []
    niter = 0

    # check if the id field is contained the current attribute table field names
    if  id_field not in getAttributeTableNames(lyr): 
       raise ValueError("id_field not in field values.")

    # workaround lyr.GetNextFeature() returning None on Windows - on Mac it seems to work fine
    lyr.ResetReading()
    lyr.GetFeatureCount() # failsafe to check if GDAL detects any layers at all

    for ftr_id in range(0,lyr.GetFeatureCount()):
        p_feat = lyr.GetFeature(ftr_id) # this confusely works

    #p_feat = lyr.GetNextFeature()
    #while p_feat:
        if p_feat.GetGeometryRef() is not None:
            if os.path.exists(shp_name):
                mem_driver.DeleteDataSource(shp_name) # delete temporary raster if it already exists
            tp_ds = mem_driver.CreateDataSource(shp_name) # create a new, empty raster in memory
            tp_srs = lyr.GetSpatialRef() # temporary srs to satisfy CreateLayer warning level
            tp_lyr = tp_ds.CreateLayer('polygons', tp_srs, ogr.wkbPolygon) # create a temporary polygon layer
            tp_lyr.CreateFeature(p_feat.Clone())
            offsets = boundingBoxToOffsets(p_feat.GetGeometryRef().GetEnvelope(), geot) # get the bounding box of the polygon feature and convert the coordinates to cell offsets
            new_geot = geotFromOffsets(offsets[0], offsets[2], geot)

            tr_ds = mem_driver_gdal.Create(\
            "", \
            offsets[3] - offsets[2], \
            offsets[1] - offsets[0], \
            1, \
            gdal.GDT_Byte) # create the raster for the rasterized polygon in memory

            tr_ds.SetGeoTransform(new_geot) # set the geotransfrom the rasterized polygon
            gdal.RasterizeLayer(tr_ds, [1], tp_lyr, burn_values=[1]) # rasterize the polygon feature
            tr_array = tr_ds.ReadAsArray() # read data from the rasterized polygon

            r_array = r_ds.GetRasterBand(band).ReadAsArray(\
            offsets[2],\
            offsets[0],\
            offsets[3] - offsets[2],\
            offsets[1] - offsets[0])

            # specifying which field is used as an id
            #id = p_feat.GetFID() # old
            id = p_feat.GetField(id_field) # new

            # here it would be also possibe to add the vegetation type ( as safed in the .shp)
            # p_feat.GetField(1) 
            # As well as the describtor of location e.g. "close to house"
            # p_feat.GetField(2)
            # get bounding box
            # p_feat.GetGeometryRef().GetEnvelope()
            # get centroid point
            # p_feat.GetGeometryRef().Centroid().GetPoint_2D()
            # get area
            # p_feat.GetGeometryRef().Area()

            # getting field for vegetation type
            info_field = p_feat.GetField(1) 

            # for calculation of the size of the raster area
            # see https://gis.stackexchange.com/questions/425849/calculate-cell-pixel-area-with-rasterio-in-python
            # tr_ds.RasterXSize # x extent of rasterized polygon NOT TRUE - needs to be offset first!
            # tr_ds.RasterYSize
            # geot[1]*(-geot[5]) # pixel size of raster in squared degrees (Lon * Lat)

            if r_array is not None:
                
                if (adjust_func != None) and (adjust_value != None): # added by phil
                    # adjust function must take the first argument as the raster
                    r_array = adjust_func(r_array, adjust_value)

                maskarray = np.ma.MaskedArray(\
                r_array,\
                mask = np.logical_or(r_array==nodata, np.logical_not(tr_array)))

                if maskarray is not None:

                    zstats.append(setFeatureStats(\
                    id,\
                    maskarray.min(),\
                    maskarray.max(),\
                    maskarray.mean(),\
                    np.ma.median(maskarray),\
                    maskarray.std(),\
                    maskarray.sum(),\
                    maskarray.count(),\
                    p_feat.GetGeometryRef().Centroid().GetPoint_2D(),\
                    p_feat.GetGeometryRef().Area(),\
                    p_feat.GetGeometryRef().GetEnvelope(),\
                    info_field))

                else:
                    zstats.append(setFeatureStats(\
                    id,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata))
            else:
                zstats.append(setFeatureStats(\
                    id,\
                    info_field, \
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata,\
                    nodata))

            tp_ds = None
            tp_lyr = None
            tr_ds = None

            #p_feat = lyr.GetNextFeature()


    if fn_csv != None:
        #fn_csv = "/Users/Jordn/Desktop/zstats.csv"
        col_names = zstats[0].keys()
        with open(fn_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, col_names)
            writer.writeheader()
            writer.writerows(zstats)
    else: # returns data if no csv filename is provided
        #import pandas as pd
        df = pd.DataFrame.from_dict(zstats) # seemless conversion to R compatible data frame
        if band_name != None:
            df = df.assign(band = band_name) # appennd vegetation indice as column
        if shadow != None:
            df = df.assign(shadow = shadow)
        if flight_date != None:
            df = df.assign(date = flight_date)
        if flight_number != None:
            df = df.assign(flight_number = flight_number)
        if flight_time != None:
            df = df.assign(flight_time = flight_time)
        return df
        

# zonalStatistics(fn_raster = "/Volumes/T7/UAV_Steglitz_2019/00__Code/qgis/first_results/14_06_2019_flug1_orginal_16bit_rectified_ndvi.tif",
#                fn_zones = "/Volumes/T7/UAV_Steglitz_2019/00__Code/qgis/first_results/areas.shp",
#                fn_csv = "/Users/Jordn/Desktop/zstats.csv")


def mergeZonalStatistics(df_1 = None, df_2 = None):
    '''Merging two Zonal Statistics DataFrames into one.'''
    #if df_1 == None:
    #    df_1 = pd.DataFrame() 

    #elif df_2 == None: #if only on dataframe is provided
    #    return df_1    
    
    df = pd.concat([df_1, df_2], axis=0) # vertival
    #pd.concat([df_1, df_2], axis=1) # horizontal
    return df


def getAttributeTableNames(layer):
    '''extracts the names of field in the attribute table (colnames) of a .shp'''
    schema = []
    ldefn = layer.GetLayerDefn()
    for n in range(ldefn.GetFieldCount()):
        fdefn = ldefn.GetFieldDefn(n)
        schema.append(fdefn.name)
    return schema

def clipShadow(shp_shadow_filename, shp_transect_filename, outfile_filename):
    '''Clips the shadow shape files down to the extent of the transects sites'''    
    # Base Layer
    driverName = "ESRI Shapefile"
    driver = ogr.GetDriverByName(driverName)
    inDataSource = driver.Open(shp_transect_filename, 0)
    inLayer = inDataSource.GetLayer()

    ## Clip Layer
    inClipSource = driver.Open(shp_shadow_filename, 0)
    inClipLayer = inClipSource.GetLayer()

    ## Clipped Shapefile
    outDataSource = driver.CreateDataSource(outfile_filename)
    outLayer = outDataSource.CreateLayer('FINAL', geom_type=ogr.wkbMultiPolygon)

    # writing ESRI projection file (.prj) to store CRS
    spatialRef = inLayer.GetSpatialRef()
    spatialRef.MorphToESRI()
    prj_filename = outfile_filename[:-4] + ".prj"
    prj_file = open(prj_filename, 'w')
    prj_file.write(spatialRef.ExportToWkt())
    prj_file.close()

    # actual clip processing & write out
    ogr.Layer.Clip(inLayer, inClipLayer, outLayer)

    # clean up
    inDataSource.Destroy()
    inClipSource.Destroy()
    outDataSource.Destroy()
   
    #return outLayer


def clipShadowAllDates(folder_path, shp_transect_filename, search_pattern = "shadow"):
    '''identify all shape files for shadows in a given directory and clip them with the provided area shape file.
    Returning a list with the filenames to the corresponding clipped shadow areas.'''
    import pmultispectral.rasterio_io as rasterio_io
    
    # finding all shadow shapefiles
    file_list = rasterio_io.listFiles(folder_path, file_extension = ".shp", search_pattern = search_pattern)
    # excluding already clipped files (from an earlier run) - which will be overridden subsequently
    file_list_filtered = rasterio_io.filterFiles(file_list, filter_key_exclude = ['clipped']) #, filter_key_include = ['ETRS'])

    list_shadow_ogr = []
    for shp_shadow_filename in file_list_filtered:
        logging.info('found these files : ' + shp_shadow_filename)
        outfile_filename = shp_shadow_filename[:-4] +"_clipped.shp"
        fn_zones_shadow = clipShadow(shp_shadow_filename, shp_transect_filename, outfile_filename)
        list_shadow_ogr.append(outfile_filename)
    return(list_shadow_ogr)


