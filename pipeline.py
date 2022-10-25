# executing pipeline for orthomosaic preprocessing
from operator import truediv
import pmultispectral.rasterio_indices as rasterio_indices
import pmultispectral.rasterio_io as rasterio_io
import pmultispectral.zonal_statistics as zonal_statistics

import logging
logging.basicConfig(level=logging.INFO)



# platform depending alterations

# from sys import platform
# if platform == "linux" or platform == "linux2": # linux
#     raise Exception("Linux not implemented")
# elif platform == "darwin": # OS X
#     external_drive = "/Volumes/T7/"
# elif platform == "win32": # Windows...
#     external_drive = "D:/" # HOME
#     external_drive = "F:/" # UNI

import psutil
partitions = psutil.disk_partitions()
for p in partitions:
    if p.fstype == "exFAT": # Windows
        external_drive = p.mountpoint
        logging.info('disk located at : ' + external_drive)
    elif p.fstype == "exfat": # Osx
        external_drive = p.mountpoint + "/"
        logging.info('disk located at : ' + external_drive)


# directory info
folder_path = external_drive + "UAV_Steglitz_2019/01__Multispectral/orthomosaics"

#file_path = folder_path + "/2019_07_17_Flug04.tif"
#out_path = folder_path + "/2019_07_17_Flug04_indices.tif"




bandnames = {   1 : "530nm",
                2 : "550nm",
                3 : "570nm",
                4 : "670nm",
                5 : "700nm",
                6 : "800nm",
                7 : "mask",
                8 : "gi",
                9 : "gndvi",
                10 : "msr",
                11 : "ndvi",
                12 : "pri"} 

flights = {     "2019_04_17" : ["Flug01"],
                "2019_05_07" : ["Flug02"],
                "2019_06_14" : ["Flug01"],
                "2019_07_04" : ["Flug01"],
                "2019_07_17" : ["Flug01","Flug02","Flug03","Flug04","Flug05","Flug06"]}

#flights = {     "2019_04_17" : ["Flug01"]} #,
#               "2019_05_07" : ["Flug02"]}

# Flight times are derived from the individual .log files in the 04__logfile folder (mid point of observations)
#flight_hour = {"2019_04_17" : {"flight_number" :["Flug01"], "flight_time" : ["11:21"] },
#                "2019_05_07" : {"flight_number" :["Flug02"], "flight_time" : ["11:18"] },
#                "2019_06_14" : {"flight_number" :["Flug01"], "flight_time" : ["11:29"] },
#                "2019_07_04" : {"flight_number" :["Flug01"], "flight_time" : ["08:26"] },
#                "2019_07_17" : {"flight_number" :["Flug01","Flug02","Flug03","Flug04","Flug05","Flug06"], 
#                                "flight_time" : ["04:26", "08:03", "10:29", "13:17", "16:05", "19:03" ] } }


flight_time  = {"2019_04_17" : {"Flug01" : "11:21" },
                "2019_05_07" : {"Flug02" : "11:18" },
                "2019_06_14" : {"Flug01" : "11:29" },
                "2019_07_04" : {"Flug01" : "08:26" },
                "2019_07_17" : {"Flug01" : "04:26",
                                "Flug02" : "08:03",
                                "Flug03" : "10:29",
                                "Flug04" : "13:17",
                                "Flug05" : "16:05",
                                "Flug06" : "19:03"} }


parameter = {   'clip_shadows' : False, 
                'write_indices' : False,
                'zonal_statistics': True, 
                'zonal_statistics_keys': ["gi", "gndvi", "msr", "ndvi", "pri"], # for which bands are zonal statistics to be calculated
                'zonal_statistics_run_shadows' : False,
                #'zonal_statistics_run_no_shadows' : True,
                'check_for_georef' : False } # if (in case they exist) manually georeferenced files should be used for zonal statistics 

#file_path = "F:/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04.tif" #WINDOWS
#file_path = "/Volumes/T7/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04.tif" #MAC

#out_path = "F:/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04_indices.tif" #WINDOWS
#out_path = "/Volumes/T7/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04_altered.tif" #MAC


# deriving a filepath list 
file_list = rasterio_io.listFiles(folder_path, ".tif") # get .tif files in directory
#file_list_filtered = rasterio_io.filterFiles(file_list, filter_key_exclude = ['indices', 'aux', 'ovr', 'xml'], filter_key_include = ['ETRS']) # filter out unwanted ones

# RUN IN ORDER TO GENERATE CLIPPED SHADOW/ NO SHADOW SHAPEFILES
file_path_shadow =  external_drive + "UAV_Steglitz_2019/00__Code/qgis/zonal_statistics/shadow_v2"  # location of shadow shape files
if parameter["clip_shadows"] == True: # clip all shadow .shp files within directory with the original transect file to derive shaded areas of transects (.shp)
    shp_transect_filename =  external_drive + "UAV_Steglitz_2019/00__Code/qgis/zonal_statistics/areas_EPSG_3045_new_new.shp"
    zonal_statistics.clipShadowAllDates(file_path_shadow, shp_transect_filename)

for flight_date in list(flights.keys()): # extract individual flights (date and flight number) from directory
    for flight_number in flights[flight_date]:
        file_list_filtered = rasterio_io.filterFiles(file_list, \
                                                    filter_key_exclude = ['indices', 'georef', 'aux', 'ovr', 'xml', 'points'], \
                                                    filter_key_include = ['ETRS', 'modified', flight_date, flight_number]) 

        if file_list_filtered != None: # only run if files were found in path
            # RUN INDICE CALCULATION MODULE
            if parameter["write_indices"] == True: 
                for file_path in file_list_filtered:
                    logging.info('running writeIndiceToDisk : ' + file_path)
                    rasterio_indices.writeIndicesToDisk(file_path)

            # RUN ZONAL STATISTICS MODULE
            if parameter["zonal_statistics"] == True:
                 for file_path in file_list_filtered:
                    fn_raster = file_path.replace('.tif', '_indices.tif') # should be run on the indices files
                    logging.info('running zonalStatistics for : ' + fn_raster)
                    
                    if parameter["check_for_georef"] == True: 
                        logging.info('searching for georeferenced image')
                        fn_raster = rasterio_io.checkForAlternativeFile(file_path = fn_raster, 
                                                                        file_extension = ".tif", 
                                                                        filter_key_exclude=['aux', 'ovr', 'xml', 'points'],
                                                                        filter_key_include ="arcgis_georef",
                                                                        remove_str = None, 
                                                                        replace_str = "")
                        
                    
                    if parameter["zonal_statistics_run_shadows"] == True: #ONLY ON CAN BE PASSED TO THE ANALYSIS BELOW
                        # identify corresponding shadow file
                        file_list_shadow = rasterio_io.listFiles(file_path_shadow, file_extension = ".shp", search_pattern = "is_shadow")
                        fn_zones = rasterio_io.filterFiles(file_list_shadow, filter_key_include = [flight_date, flight_number])
                        fn_zones = fn_zones[0] # conversion from 1 element list to string HACKY
                        logging.info('using shadowed transects: ' + fn_zones)
                        shadow_val = 1
                        shadow_str = '_is_shadow'
                        if zonal_statistics.checkCrsShp(fn_zones, ref_id = 4326) == False: # check for WGS 84 projection
                            logging.info('reprojecting CRS from: ' + fn_zones) 
                            zonal_statistics.reprojectShpInPlace(fn_zones, ref_id = 4326)

                    elif parameter["zonal_statistics_run_shadows"] == False:
                        # Old way of statically assigning the area for transects
                        # fn_zones = external_drive + "UAV_Steglitz_2019/00__Code/qgis/zonal_statistics/areas_EPSG_3045_new.shp"
                        file_list_shadow = rasterio_io.listFiles(file_path_shadow, file_extension = ".shp", search_pattern = "no_shadow")
                        fn_zones = rasterio_io.filterFiles(file_list_shadow, filter_key_include = [flight_date, flight_number])
                        fn_zones = fn_zones[0] # conversion from 1 element list to string HACKY
                        logging.info('using non-shadow transects: ' + fn_zones)
                        shadow_val = 0
                        shadow_str = '_no_shadow'
                        if zonal_statistics.checkCrsShp(fn_zones, ref_id=4326) == False:  # check for WGS 84 projection
                            logging.info('reprojecting CRS from: ' + fn_zones)
                            zonal_statistics.reprojectShpInPlace(fn_zones, ref_id=4326)
                    
                    

                    
                    #fn_zones = "/Volumes/T7/UAV_Steglitz_2019/00__Code/qgis/zonal_statistics/shadow_2019_05_07_Flug02.shp"
                    #shadow_val = 1

                    #fn_raster = external_drive + "UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_04_17_Flug01_ETRS1989_indices.tif"
                    #fn_zones = external_drive + "UAV_Steglitz_2019/00__Code/qgis/first_results/areas.shp"
                    
                    #zs_stats_band1 = zonal_statistics.zonalStatistics(fn_raster, fn_zones, band = 1, fn_csv = None)
                    #zs_stats_band_ndvi = zonal_statistics.zonalStatistics(fn_raster, fn_zones, band = 11, adjust_func = (lambda a, b :  a / b) ,adjust_value = 65535, band_name = "ndvi" ,fn_csv = None)

                    
                    # Zonal Statistics for Vegetation Indices (value conversion from uint16 to float)
                    zs_stats_veg_indx = None # initialize it blank (setup)
                    for band_position, band_name in bandnames.items():
                        if band_name in parameter["zonal_statistics_keys"]:
                            zs_stats_band = zonal_statistics.zonalStatistics(fn_raster, fn_zones, \
                                                                            band = band_position, \
                                                                            id_field= 'transect', \
                                                                            adjust_func = (lambda a, b :  a / b) , \
                                                                            adjust_value = 65535, \
                                                                            band_name = band_name,\
                                                                            flight_date = flight_date ,\
                                                                            flight_number = flight_number,\
                                                                            flight_time = flight_time[flight_date][flight_number],\
                                                                            shadow = shadow_val,\
                                                                            fn_csv = None)
                            zs_stats_veg_indx = zonal_statistics.mergeZonalStatistics( zs_stats_veg_indx, zs_stats_band)
                    zs_stats_veg_indx.to_csv(fn_raster.replace('.tif', '_zonal_statistics' + shadow_str + '.csv'))
    
# run for all dates, append date to dataframe

# TESTING AREA
print("beginning testing!")

# reading orthomosaic values into individual band numpy arrays  

# checking the profile for band names 
import rasterio

#rasterio_indices.writeIndicesToDisk(file_path)






#with rasterio.open(file_path[:-4] + "_indices.tif") as src:
#    test_profile = src.profile

# deep check
with rasterio.open(file_path[:-4] + "_indices.tif") as src:
    test_profile = src.profile.copy()
    test_raster = src.read()

# read a specific band
    src.indexes # get number of bands in datastructure
    band1 = dataset.read(1) # reading band at position [1]





# double check
with rasterio.open(file_path[:-4] + "_indices.tif") as src:
    print(src.profile)
    test = src.read(12) # read the one array entry
pltIndx(test)


with rasterio.open(file_path) as src:
    test = src.read()