# executing pipeline for orthomosaic preprocessing
from operator import truediv
import pmultispectral.rasterio_indices as rasterio_indices
import pmultispectral.rasterio_io as rasterio_io
import pmultispectral.zonal_statistics as zonal_statistics

import logging
logging.basicConfig(level=logging.INFO)

# platform depending alterations
from sys import platform
if platform == "linux" or platform == "linux2": # linux
    raise Exception("Linux not implemented")
elif platform == "darwin": # OS X
    external_drive = "/Volumes/T7/"
elif platform == "win32": # Windows...
    external_drive = "F:/"

# directory info
folder_path = external_drive + "UAV_Steglitz_2019/01__Multispectral/orthomosaics"
file_path = folder_path + "/2019_07_17_Flug04.tif"
out_path = folder_path + "/2019_07_17_Flug04_indices.tif"

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

parameter = {   'write_indices' : False,
                'zonal_statistics': True, 
                'zonal_statistics_keys': ["gi", "gndvi", "msr", "ndvi", "pri"]} # for which bands are zonal statistics to be calculated

#file_path = "F:/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04.tif" #WINDOWS
#file_path = "/Volumes/T7/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04.tif" #MAC

#out_path = "F:/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04_indices.tif" #WINDOWS
#out_path = "/Volumes/T7/UAV_Steglitz_2019/01__Multispectral/orthomosaics/2019_07_17_Flug04_altered.tif" #MAC


# deriving a filepath list 
file_list = rasterio_io.listFiles(folder_path, ".tif") # get .tif files in directory
#file_list_filtered = rasterio_io.filterFiles(file_list, filter_key_exclude = ['indices', 'aux', 'ovr', 'xml'], filter_key_include = ['ETRS']) # filter out unwanted ones



for flight_date in list(flights.keys()): # extract individual flights (date and flight number) from directory
    for flight_number in flights[flight_date]:
        file_list_filtered = rasterio_io.filterFiles(file_list, \
                                                    filter_key_exclude = ['indices', 'aux', 'ovr', 'xml'], \
                                                    filter_key_include = ['ETRS', flight_date, flight_number]) 

        if file_list_filtered != None: # instances wheen no file_path is fund
            # RUN INDICE CALCULATION MODULE
            if parameter["write_indices"] == True: 
                for file_path in file_list_filtered:
                    logging.info('writeIndiceToDisk : ' + file_path)
                    rasterio_indices.writeIndicesToDisk(file_path)

            # RUN ZONAL STATISTICS MODULE
            if parameter["zonal_statistics"] == True:
                for file_path in file_list_filtered:
                    fn_raster = file_path.replace('.tif', '_indices.tif') # should be run on the indices files
                    fn_zones = external_drive + "UAV_Steglitz_2019/01__Multispectral/orthomosaics/areas_EPSG_3045.shp"
                    shadow_val = 0
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
                                                                            adjust_func = (lambda a, b :  a / b) , \
                                                                            adjust_value = 65535, \
                                                                            band_name = band_name,\
                                                                            flight_date = flight_date ,\
                                                                            flight_number = flight_number,\
                                                                            shadow = shadow_val,\
                                                                            fn_csv = None)
                            zs_stats_veg_indx = zonal_statistics.mergeZonalStatistics( zs_stats_veg_indx, zs_stats_band)
                    zs_stats_veg_indx.to_csv(fn_raster.replace('.tif', '_zonal_statistics.csv'))
    
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