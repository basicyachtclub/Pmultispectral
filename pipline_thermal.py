# STATIC IMPORT FROM pipeline script - helps to keep these scripts synced and less redundant!
from pipeline import *


# due to different file names flights need to be redefined 
# (note that we actually utilise the FOLDER for the search names as these are more coherent then the file names)
flights_thermal = { "2019-04-17" : ["Flug_01"],
                "2019-05-07" : ["Flug_02"],
                "2019-06-14" : ["Flug_01"],
                "2019-07-04" : ["Flug_01"],
                "2019-07-17" : ["Flug_02","Flug_03","Flug_04","Flug_05"] }

flights_thermal_all_ortho = {       "2019-04-17" : ["Flug_01", "Flug_02"],
                                    "2019-05-07" : ["Flug_01", "Flug_02"],
                                    "2019-06-14" : ["Flug_01"], 
                                    "2019-07-04" : ["Flug_01", "Flug_02"],
                                    "2019-07-17" : ["Flug_02","Flug_03","Flug_04","Flug_05"] } 
                                    # "2019-07-17" - "Flug_01" and "Flug_06" have point clouds but no ortho

# put this here as well in order to avoid changes to flights in pipeline to affect this script
flights = {"2019_07_17" : ["Flug02", "Flug03", "Flug04", "Flug05"]}
flights_thermal = {"2019-07-17" : ["Flug_02", "Flug_03", "Flug_04", "Flug_05"]}


# adjustment for a single band for reproducability
# key - band number, value - name prefix in zonal statistics
bandnames_thermal = {   1 : "thermal"} 

zs_stats_thermal_folder = external_drive + "UAV_Steglitz_2019/04__Processed/zonal_statistics_thermal_v1"

# EXTRACTING THERMAL .TIF FILES
folder_path = external_drive + "UAV_Steglitz_2019/02__Thermal"
file_list = rasterio_io.listFiles(folder_path, search_pattern= "ortho", file_extension= ".tif", recursive=True)

# SHADOW CLIPPING (shadow creation for individual transects/days ) MUST BE DONE VIA MULTISPECTRAL PIPELINE
#file_path_shadow =  external_drive + "UAV_Steglitz_2019/00__Code/qgis/zonal_statistics/shadow_v2"


for flight_date, flight_date_thermal in zip( list(flights.keys()), list(flights_thermal.keys()) ): # extract individual flights (date and flight number) from directory
    for flight_number, flight_number_thermal in zip( flights[flight_date] , flights_thermal[flight_date_thermal] ):
        # this looping and excluding is a little redundant, but lets keep it for understanability/ similarity to the multispectral structure
        # AGAIN: understand that files are being identified based on the folder names, not the file names!
        file_list_filtered = rasterio_io.filterFiles(file_list, 
                                                    filter_key_exclude = ['points', 'Older', 'aux', '.xml'], \
                                                    filter_key_include = ['modified', flight_date_thermal, flight_number_thermal],
                                                    include_folder_names= True ) 
       
        if file_list_filtered != None: # only run if files were found in path
            # RUN ZONAL STATISTICS MODULE
                if parameter["zonal_statistics"] == True:
                    for file_path in file_list_filtered:
                        #fn_raster = file_path.replace('.tif', '_indices.tif') # should be run on the indices files
                        fn_raster = file_path
                        logging.info('running zonalStatistics for : ' + fn_raster)
                        
                        # if parameter["check_for_georef"] == True: 
                        #     logging.info('searching for georeferenced image')
                        #     fn_raster = rasterio_io.checkForAlternativeFile(file_path = fn_raster, 
                        #                                                     file_extension = ".tif", 
                        #                                                     filter_key_exclude=['aux', 'ovr', 'xml', 'points'],
                        #                                                     filter_key_include ="arcgis_georef",
                        #                                                     remove_str = None, 
                        #                                                     replace_str = "")
                            
                        
                        if parameter["zonal_statistics_run_shadows"] == True: #ONLY ONE CAN BE PASSED TO THE ANALYSIS BELOW
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
                                #zonal_statistics.reprojectShpInPlaceTemp(fn_zones, ref_id=4326)

                        elif parameter["zonal_statistics_run_shadows"] == 'SPECIAL':
                            #special_key, shadow_val = 'one', 1
                            #special_key, shadow_val = 'two', 2
                            #special_key, shadow_val = 'three', 3
                            special_key, shadow_val = 'four', 4
                            file_list_shadow = rasterio_io.listFiles(
                                file_path_shadow_special, file_extension=".shp", search_pattern=special_key)
                            fn_zones = rasterio_io.filterFiles(file_list_shadow, filter_key_include=['is_shadow'])
                            fn_zones = fn_zones[0]  # conversion from 1 element list to string HACKY
                            #fn_zones = file_list_shadow[0]
                            logging.info('using SPECIAL-shadows: ' + fn_zones)
                            shadow_str = '_special_shadow_' + special_key  # + '_'
                            # check for WGS 84 projection
                            if zonal_statistics.checkCrsShp(fn_zones, ref_id=4326) == False:
                                logging.info('reprojecting CRS from: ' + fn_zones)
                                zonal_statistics.reprojectShpInPlace(fn_zones, ref_id=4326)
                                #zonal_statistics.reprojectShpInPlaceTemp(fn_zones, ref_id=4326)


                        # Zonal Statistics for Vegetation Indices (value conversion from uint16 to float)
                        zs_stats_veg_indx = None # initialize it blank (setup)
                        for band_position, band_name in bandnames_thermal.items():
                            if band_name in parameter["zonal_statistics_keys"]:
                                zs_stats_band = zonal_statistics.zonalStatistics(fn_raster, fn_zones, \
                                                                                band = band_position, \
                                                                                id_field= 'transect', \
                                                                                adjust_func = None , \
                                                                                adjust_value = None, \
                                                                                band_name = band_name,\
                                                                                flight_date = flight_date ,\
                                                                                flight_number = flight_number,\
                                                                                flight_time = flight_time[flight_date][flight_number],\
                                                                                shadow = shadow_val,\
                                                                                fn_csv = None)
                                zs_stats_veg_indx = zonal_statistics.mergeZonalStatistics( zs_stats_veg_indx, zs_stats_band)
                        # write out zonal statistics to disk (.csv)
                        #zs_stats_veg_indx.to_csv(folder_path + '/zonal_statistics/' + flight_date + "_" + flight_number + "_thermal_zonal_statistics" + shadow_str + '.csv')
                        zs_stats_file_name = os.path.basename(os.path.abspath(fn_raster)).replace(
                            '.tif', '_thermal_zonal_statistics' + shadow_str + '.csv')  # output filename
                        zs_stats_veg_indx.to_csv( os.path.join(zs_stats_thermal_folder, zs_stats_file_name) )
        

print("DONE")