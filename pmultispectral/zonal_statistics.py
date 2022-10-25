from osgeo import ogr, osr, gdal
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

    # check if both files are in the same spatial reference system otherwise algorithm doesnt work
    # r_ds.GetSpatialRef().GetName() == lyr.GetSpatialRef().GetName()
    
    nodata = r_ds.GetRasterBand(band).GetNoDataValue()

    zstats = []
    niter = 0

    # check if the id field is contained the current attribute table field names
    if id_field not in getAttributeTableNames(lyr): 
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


def clipLayer(base_layer_filename, clip_layer_filename, outfile_filename, invert_clip=False, update_shp=False):
    '''Clips the shadow shape files down to the extent of the transects sites'''    
    # Base Layer
    driverName = "ESRI Shapefile"
    driver = ogr.GetDriverByName(driverName)
    inDataSource = driver.Open(base_layer_filename, 0)
    inLayer = inDataSource.GetLayer()

    ## Clip Layer
    inClipSource = driver.Open(clip_layer_filename, 0)
    inClipLayer = inClipSource.GetLayer()

    ## Clipped Shapefile
    # case file already exists and only needs to be updated (in order to conserve attributes through clipping)
    if update_shp is True:
        outDataSource = driver.Open(outfile_filename, 1) # with write access
        #outLayer = outDataSource.GetLayer()
        inClipSource.DeleteLayer(0)
        outLayer = outDataSource.CreateLayer('', geom_type=ogr.wkbMultiPolygon)
    # case where new file needs to be created
    else:
        if os.path.exists(outfile_filename):
            driver.DeleteDataSource(outfile_filename)
        outDataSource = driver.CreateDataSource(outfile_filename)
        outLayer = outDataSource.CreateLayer('', geom_type=ogr.wkbMultiPolygon)
       
    # writing ESRI projection file (.prj) to store CRS
    spatialRef = inLayer.GetSpatialRef()
    spatialRef.MorphToESRI()
    prj_filename = outfile_filename[:-4] + ".prj"
    prj_file = open(prj_filename, 'w')
    prj_file.write(spatialRef.ExportToWkt())
    prj_file.close()

    # actual clip processing & write out
    if invert_clip == False:
        ogr.Layer.Clip(inLayer, inClipLayer, outLayer)
    elif invert_clip == True:
        ogr.Layer.Erase(inLayer, inClipLayer, outLayer)

    # clean up
    inDataSource.Destroy()
    inClipSource.Destroy()
    outDataSource.Destroy()
   
    #return outLayer


def clipShadowAllDates(folder_path, shp_transect_filename, search_pattern = "shadow", clip_exclude_areas = True, invert = True):
    '''identify all shape files for shadows in a given directory and clip them with the provided area (transect) shape file.
    Returning a list with the filenames to the corresponding clipped shadow areas. Normally also does the inverse
    clip returning all non shaded areas of the area (transect).'''
    import pmultispectral.rasterio_io as rasterio_io
    
    # finding all shadow shapefiles
    file_list_shadow = rasterio_io.listFiles(folder_path, file_extension = ".shp", search_pattern = search_pattern)
    # excluding already clipped files (from an earlier run) - which will be overridden subsequently
    file_list_shadow_filtered = rasterio_io.filterFiles(file_list_shadow, filter_key_exclude = ['transect', 'exclude']) #, filter_key_include = ['ETRS'])

    # findind all exclude shapefiles
    file_list_exclude = rasterio_io.listFiles(folder_path, file_extension = ".shp", search_pattern = "exclude")
    file_list_exclude_filtered = rasterio_io.filterFiles(file_list_exclude, filter_key_exclude = ['transect', 'is_exclude']) #, filter_key_include = ['ETRS'])


    # matching pairs in the two file lists
    file_list_shadow_filtered, file_list_exclude_filtered = rasterio_io.matchUpFileLists(
                                                                file_list_shadow_filtered, 
                                                                file_list_exclude_filtered, 
                                                                filter_key_exclude= ['exclude', 'shadow', '.shp', '_'])

    list_shadow_ogr = []

    # OMG THIS NEXT PART IS HIDEOUS
    for shp_shadow_filename, shp_exclude_filename in zip(file_list_shadow_filtered, file_list_exclude_filtered) :
        if clip_exclude_areas == True:
            # creating an exclude .shp file and setting it as the new input for the shadow clip below
            outfile_filename = shp_shadow_filename[:-4] +"_is_exclude.shp" 
            clipLayer(shp_transect_filename, shp_exclude_filename, outfile_filename, invert_clip= True)
            shp_transect_filename_next = outfile_filename # passing this on to the next steps
            
            outfile_filename = outfile_filename[:-4] +"_transect_is_shadow.shp" # building name for dyanimc transects 

        elif clip_exclude_areas == False:
            outfile_filename = shp_shadow_filename[:-4] +"_transect_is_shadow.shp" #building name for static transects
            shp_transect_filename_next = shp_transect_filename
        
        logging.info('shadow file for clip : ' + shp_shadow_filename)
        clipLayer(shp_transect_filename_next, shp_shadow_filename, outfile_filename)
        #clipLayer(shp_shadow_filename, shp_transect_filename_next, outfile_filename) # building the actual clip
        #clipLayer(shp_transect_filename_next, outfile_filename, outfile_filename, update_shp = True) # reclipping it through the transects to conserve attribute table

        list_shadow_ogr.append(outfile_filename)
        
        if invert == True: # clipping the transects with the transect shadow areas - to retain only no shadowed area .shp
            outfile_filename_inv = outfile_filename[:-14] +"_no_shadow.shp"
            clipLayer(shp_transect_filename_next, outfile_filename, outfile_filename_inv, invert_clip= True)
    
    return(list_shadow_ogr)


def reprojectShpFromRaster(layer, raster):
    #raster with projections I want
    #raster = gdal.Open("/home/zeito/pyqgis_data/utah_dem4326.raster")

    #shapefile with the from projection
    #driver = ogr.GetDriverByName("ESRI Shapefile")
    #dataSource = driver.Open("/home/zeito/pyqgis_data/polygon8.shp", 1)
    #layer = dataSource.GetLayer()

    #set spatial reference and transformation
    sourceprj = layer.GetSpatialRef()
    targetprj = osr.SpatialReference(wkt=raster.GetProjection())
    transform = osr.CoordinateTransformation(sourceprj, targetprj)

    #to_fill = ogr.GetDriverByName("Esri Shapefile")
    #ds = to_fill.CreateDataSource("/home/zeito/pyqgis_data/projected.shp")
    mem_driver = ogr.GetDriverByName("Memory")
    #mem_driver_gdal = gdal.GetDriverByName("MEM")
    #if os.path.exists('temp'):
    #            mem_driver.DeleteDataSource('temp')
    ds = mem_driver.CreateDataSource('temp')
    outlayer = ds.CreateLayer('', targetprj, ogr.wkbPolygon)
    
    attribute_names = []
    ldefn = layer.GetLayerDefn()
    for n in range(ldefn.GetFieldCount()):
        fdefn = ldefn.GetFieldDefn(n)
        attribute_names.append(fdefn.name)
        outlayer.CreateField(fdefn) # write field to new layer
    #print(attribute_names)

    #outlayer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))

    #apply transformation
    i = 0

    for feature in layer:
        transformed = feature.GetGeometryRef()
        transformed.Transform(transform)

        geom = ogr.CreateGeometryFromWkb(transformed.ExportToWkb())
        defn = outlayer.GetLayerDefn()
        feat = ogr.Feature(defn)
        for attribute_name in attribute_names: # copying values from attribute table into new feature
            value = feature.GetField(attribute_name)
            feat.SetField(attribute_name, value )
        #feat.SetField('id', i)
        feat.SetGeometry(geom)
        outlayer.CreateFeature(feat)
        i += 1
        feat = None

    #layer = outlayer
    #ds = None
    return outlayer


def reprojectShpInPlace(shp_filename, ref_id = 4326):
    '''Reprojects an existing ESRI Shapefile in Place on disk. The path to the Shapefile as well as the EPSG projection ID can be provided. 
    Default EPSG id is 4326 (WGS 84).'''
    
    # Load data and create Transformation
    driver = ogr.GetDriverByName('ESRI Shapefile')
    inDataSet = driver.Open(shp_filename, 1) # loading of Shapfile with write access
    inLayer = inDataSet.GetLayer()  # loading layer
    inSpatialRef = inLayer.GetSpatialRef() # input SpatialReference (EPSG)
    outSpatialRef = osr.SpatialReference() # output SpatialReference (EPSG)
    outSpatialRef.ImportFromEPSG(ref_id) # default is WGS 84
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef) # create the CoordinateTransformation

    # loop through the features, transforming the geometry, 
    # adding them to the layer as new feature and removing the 'old' feature
    inLayer_length = inLayer.GetFeatureCount()
    for ftr_id in range(0, inLayer_length): 
        Feature = inLayer.GetFeature(ftr_id) # ftr_id is unique within the file 
        # (appended feature will get continous ID regardless if feature with lower ID is removed)

        geom = Feature.GetGeometryRef()  # get the input geometry
        geom.Transform(coordTrans) # reproject the geometry
        Feature.SetGeometry(geom) # set the geometry 
        inLayer.CreateFeature(Feature) # add the feature to the shapefile
        inLayer.DeleteFeature(ftr_id) # remove old geomery feature

    # Save and close the shapefiles
    inDataSet.SyncToDisk()
    inDataSet.Destroy()
    
    # updating the projection file .prj (so the reprojected features match the actual SRS of the file)
    outSpatialRef.MorphToESRI()
    prj_file = open(shp_filename[:-4]+'.prj' , 'w')
    prj_file.write(outSpatialRef.ExportToWkt())
    prj_file.close()
    
def getCrsShp(shp_filename):
    ''' returns Spatial reference object of shapefile.'''
    driver = ogr.GetDriverByName('ESRI Shapefile')
    inDataSet = driver.Open(shp_filename, 0) # read only
    inLayer = inDataSet.GetLayer()  
    inSpatialRef = inLayer.GetSpatialRef()
    return(inSpatialRef)

def checkCrsShp(shp_filename, ref_id = 4326):
    '''compare if CRS of shapefile corrresponds to EPSG id.'''
    inSpatialRef = getCrsShp(shp_filename)
    outSpatialRef = osr.SpatialReference()  
    outSpatialRef.ImportFromEPSG(ref_id)
    return(outSpatialRef.ExportToWkt() == inSpatialRef.ExportToWkt())

#checkCrsShp("D:\\UAV_Steglitz_2019\\00__Code\\qgis\\zonal_statistics\\shadow_v2\\shadow_2019_07_17_Flug04_is_exclude_transect_is_shadow.shp")

#reprojectShpInPlace("D:\\UAV_Steglitz_2019\\00__Code\\qgis\\zonal_statistics\\shadow_v2\\shadow_2019_07_17_Flug04_is_exclude_transect_is_shadow.shp")
 

#  def reprojectRasterInPlace(raster_filename, ref_id = 4326):
#     '''Reprojects Raster data in place on disk. Filename to Data as well as a reference coordinate system can be provided (EPSG). 
#     Default CRS is WGS 84.'''
#     #filename = r"C:\path\to\input\raster
#     input_raster = gdal.Open(raster_filename)
#     #output_raster = r"C:\path\to\output\raster
#     warp = gdal.Warp(raster_filename, input_raster, dstSRS='EPSG:' + ref_id) # output, input, crs
#     warp = None # Closes the files